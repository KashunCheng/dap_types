import urllib.request

versions = {
    # https://github.com/microsoft/debug-adapter-protocol/pull/506
    "1.69": "5f30efc008bcf16a1d10e7d5536cde523b333f5f",
    # https://github.com/microsoft/debug-adapter-protocol/pull/518
    "1.70": "bcb11b3e3b440fec3f0af3d27d77916d8213ee05",
}


def get_schema(git_hash: str) -> str:
    url = f"https://raw.githubusercontent.com/microsoft/debug-adapter-protocol/{git_hash}/debugAdapterProtocol.json"
    with urllib.request.urlopen(url) as f:
        return f.read().decode("utf-8")
