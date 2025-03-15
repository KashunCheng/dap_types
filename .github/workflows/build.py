import subprocess
import tomllib
from datetime import datetime

import ast
import os
import re
from ast import ClassDef, Name, fix_missing_locations
from pathlib import Path
from tempfile import TemporaryDirectory
from datamodel_code_generator import InputFileType, generate, LiteralType, DataModelType
from typing import Tuple
from dap_versions import versions, get_schema

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


def create_library_source(json_schema: str):
    with TemporaryDirectory() as temporary_directory_name:
        temporary_directory = Path(temporary_directory_name)
        output = Path(temporary_directory / "model.py")
        generate(
            json_schema,
            input_file_type=InputFileType.JsonSchema,
            input_filename="debugAdapterProtocol.json",
            output=output,
            output_model_type=DataModelType.PydanticV2BaseModel,
            enum_field_as_literal=LiteralType.All,
        )
        original: str = output.read_text()
    model = ast.parse(original)

    # Patch classes like Body1, Body2, etc.
    # To rename them to StoppedEventBody, ContinuedEventBody, etc.
    class ClassnameRewriter(ast.NodeVisitor):
        def __init__(self):
            self.body_regex = re.compile(r"Body\d*$")
            self.body_ann_assign_map: dict[str, Tuple[ClassDef, Name]] = {}
            self.body_class_map: dict[str, ClassDef] = {}
            self.current_class_def = None

        def visit_ClassDef(self, node):
            self.current_class_def = node
            match = self.body_regex.match(node.name)
            if match:
                self.body_class_map[node.name] = node
            self.generic_visit(node)

        def visit_Name(self, node):
            match = self.body_regex.match(node.id)
            if match:
                self.body_ann_assign_map[node.id] = (self.current_class_def, node)
            self.generic_visit(node)

    cr = ClassnameRewriter()
    cr.visit(model)
    assert len(cr.body_ann_assign_map) == len(cr.body_class_map)
    for body_name, (class_def, name) in cr.body_ann_assign_map.items():
        new_name = class_def.name + "Body"
        cr.body_class_map[body_name].name = new_name
        name.id = new_name

    # Implement an associated type for each request class, so that it can have an associated response class.
    # Then, implement discriminate method on Response class to return the associated response class. The function should receive a request class and return the associated response class.
    class AssociatedTypeGenerator(ast.NodeTransformer):
        def __init__(self):
            self.request_classes = []
            self.event_classes = []

        def visit_ImportFrom(self, node):
            if node.module == "typing":
                node.names.append(ast.alias("Annotated"))
            if node.module == "pydantic":
                node.names.append(ast.alias("TypeAdapter"))
                node.names.append(ast.alias("ConfigDict"))
            return node

        def visit_response(self, node: ClassDef):
            if node.name == "Response":
                return node
            if node.name == "ErrorResponse":
                node.body.append(ast.parse("success: Literal[False]").body[0])
                return node
            node.body.append(ast.parse(f"success: Literal[True]").body[0])
            return node

        def visit_ClassDef(self, node):
            if hasattr(node.bases[0], "id") and node.bases[0].id == "BaseModel":
                node.body.insert(
                    0, ast.parse("model_config = ConfigDict(extra='allow')").body[0]
                )
            if not node.name.endswith("Request"):
                if node.name.endswith("Response"):
                    return self.visit_response(node)
                if node.name.endswith("Event") and not node.name == "Event":
                    self.event_classes.append(node.name)
                return node
            if node.name == "Request":
                return node
            self.request_classes.append(node.name)
            response_type = re.sub(r"Request$", "Response", node.name)
            node.body.append(
                ast.parse(f"""
@classmethod
def discriminate_response(cls, res: Response) -> {response_type} | ErrorResponse:
    response_adaptor = TypeAdapter(Annotated[{response_type} | ErrorResponse, Field(..., discriminator='success')])
    return response_adaptor.validate_python(res.model_dump())
            """).body[0]
            )
            return node

        def visit_Module(self, node):
            self.generic_visit(node)

            node.body.append(
                ast.parse(
                    f"DiscriminatedRequest = Annotated[{' | '.join(self.request_classes)}, Field(discriminator='command')]"
                ).body[0]
            )
            node.body.append(
                ast.parse(
                    f"DiscriminatedEvent = Annotated[{' | '.join(self.event_classes)}, Field(discriminator='event')]"
                ).body[0]
            )
            node.body.append(
                ast.parse(
                    "DiscriminatedProtocolMessage = Annotated[Union[DiscriminatedRequest, DiscriminatedEvent, Response], Field(discriminator='type')]"
                ).body[0]
            )
            return node

    atg = AssociatedTypeGenerator()
    atg.visit(model)
    model = fix_missing_locations(model)

    with open(
        os.path.join(
            PROJECT_ROOT,
            "dap_types",
            "__init__.py",
        ),
        "w",
    ) as f:
        f.write(ast.unparse(model))


def main():
    today = datetime.today().strftime("%Y%m%d")
    for version, git_hash in versions.items():
        schema = get_schema(git_hash)
        create_library_source(schema)
        version_str = f"{today}!{version}"
        pyproject_path = os.path.join(PROJECT_ROOT, "pyproject.toml")
        with open(pyproject_path, "r") as f:
            content = f.read()
            data = tomllib.loads(content)
            old_version = data["project"]["version"]
            content = content.replace(old_version, version_str)
        with open(pyproject_path, "w") as f:
            f.write(content)
        subprocess.run(["uv", "build"], check=True, cwd=PROJECT_ROOT)


if __name__ == "__main__":
    main()
