# dap-types

**dap-types** is a Python package that provides type definitions for the [Debug Adapter Protocol (DAP)](https://microsoft.github.io/debug-adapter-protocol/). Built on top of [Pydantic v2](https://pydantic-docs.helpmanual.io/), the package offers a comprehensive, type-safe model representation of DAP messages—including requests, responses, and events—to help you build or interface with debug adapters with confidence.

---

## Features

- **Comprehensive DAP Models:** Automatically generated Pydantic models for all major DAP messages.
- **Validation & Serialization:** Leverages Pydantic's powerful runtime validation and JSON serialization to ensure messages adhere to the protocol.
- **Automatic Schema Generation:** Uses the official DAP JSON schema (via `datamodel-code-generator`) to keep models up-to-date.
- **Modern Python Typing:** Supports Python 3.10+ with modern type annotations for better editor support and static analysis.

---

## Installation

Install **dap-types** directly from PyPI:

```bash
pip install dap-types
```

---

## Usage

Import the DAP types into your project and start creating or validating protocol messages:

```python
import json
import pydantic_core
from pydantic import TypeAdapter

from dap_types import InitializeRequest, InitializeRequestArguments, DiscriminatedProtocolMessage

# ------------------------------------------------------------------------------
# Create an "initialize" request message for a debug adapter.
#
# The InitializeRequest is a Pydantic model representing a DAP request.
# It includes:
#   - seq: A sequence number for the message (here, 1)
#   - type: Message type ("request")
#   - command: The DAP command ("initialize")
#   - arguments: An instance of InitializeRequestArguments with adapter details.
#
# Expected output (first printed line):
# {"seq": 1, "type": "request", "command": "initialize", "arguments": {"adapterID": "my-debug-adapter", "locale": "en-US"}}
# ------------------------------------------------------------------------------
initialize_request = InitializeRequest(
    seq=1,
    type="request",
    command="initialize",
    arguments=InitializeRequestArguments(
        adapterID="my-debug-adapter",
        locale="en-US"
    )
)

# ------------------------------------------------------------------------------
# Serialize the initialize_request to a JSON string.
#
# pydantic_core.to_jsonable_python() converts the Pydantic model to a JSON-serializable format,
# excluding any fields that are None. Then, json.dumps() produces the JSON string.
# The printed JSON string should match the expected output above.
# ------------------------------------------------------------------------------
print(json.dumps(
    pydantic_core.to_jsonable_python(initialize_request, exclude_none=True)
))

# ------------------------------------------------------------------------------
# Create a TypeAdapter for DiscriminatedProtocolMessage.
#
# This adapter is used to parse incoming JSON messages to the appropriate DAP model.
# The DiscriminatedProtocolMessage is a union type that can represent:
#   - DiscriminatedRequest
#   - DiscriminatedEvent
#   - Response
#
# This adapter will automatically select the correct type based on discriminator fields.
# ------------------------------------------------------------------------------
protocol_message_adapter = TypeAdapter(DiscriminatedProtocolMessage)

# ------------------------------------------------------------------------------
# Example: Parse an "initialize" response from a debug adapter.
#
# The JSON string represents a successful response to the initialize request.
# It includes:
#   - seq: 1 (matching the request sequence)
#   - type: "response"
#   - command: "initialize"
#   - request_seq: 1 (associating it with the original request)
#   - success: true
#   - body: Contains capability flags (e.g., supportsConfigurationDoneRequest)
#
# First, we parse the JSON using the protocol_message_adapter.
#
# Expected output (printed types):
#   - Before discrimination: <class 'dap_types.Response'>
#   - After calling initialize_request.discriminate_response(), the type becomes <class 'dap_types.InitializeResponse'>
# ------------------------------------------------------------------------------
initialize_response_json = """
{
    "seq": 1,
    "type": "response",
    "command": "initialize",
    "request_seq": 1,
    "success": true,
    "body": {
        "supportsConfigurationDoneRequest": true,
        "supportsFunctionBreakpoints": true,
        "supportsConditionalBreakpoints": true
    }
}
"""
# Validate and convert the JSON to the appropriate model.
initialize_response = protocol_message_adapter.validate_json(initialize_response_json)
print("typeof initialize_response:", type(initialize_response))
# Discriminate the response to obtain the specific type for an initialize response.
initialize_response = initialize_request.discriminate_response(initialize_response)
print("typeof initialize_response:", type(initialize_response))
# Expected printed types:
# typeof initialize_response: <class 'dap_types.Response'>
# typeof initialize_response: <class 'dap_types.InitializeResponse'>

# ------------------------------------------------------------------------------
# Example: Parse an "event" message from a debug adapter.
#
# The JSON string represents a "stopped" event, indicating the debuggee has halted
# due to a breakpoint.
# It includes:
#   - seq: 2 (sequence number for the event)
#   - type: "event"
#   - event: "stopped"
#   - body: Contains event details such as the reason ("breakpoint") and threadId.
#
# We parse this JSON message with the protocol_message_adapter.
# The expected parsed type is <class 'dap_types.StoppedEvent'>.
# ------------------------------------------------------------------------------
stopped_event_json = """
{
    "seq": 2,
    "type": "event",
    "event": "stopped",
    "body": {
        "reason": "breakpoint",
        "threadId": 1
    }
}
"""
stopped_event = protocol_message_adapter.validate_json(stopped_event_json)
print("typeof stopped_event:", type(stopped_event))
# Expected printed output:
# typeof stopped_event: <class 'dap_types.StoppedEvent'>
```

These models allow you to:
- **Construct messages** that conform to the DAP specification.
- **Validate incoming messages** from a debug adapter or client.
- **Serialize/deserialize** protocol messages with minimal boilerplate.

---

## Development

This repository includes GitHub Actions workflows to build, test, and publish the package. The build script located at `.github/workflows/build.py` automatically:

- Fetches the latest DAP JSON schema from the official repository.
- Generates the corresponding Pydantic models.
- Updates the package version in `pyproject.toml` based on the current date and DAP version.

### Local Build

To run the build script locally:

```bash
uv run .github/workflows/build.py
```

This will regenerate the models in `dap_types/__init__.py` and update version information.

## Contributing

Contributions are welcome! If you’d like to contribute:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Write tests and ensure all checks pass.
4. Submit a pull request.

Please adhere to the [Apache License 2.0](LICENSE) and follow the existing coding style.

---

## License

Distributed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.
