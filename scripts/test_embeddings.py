"""Quick test to verify NVIDIA embedding model availability.

Usage (PowerShell):
    $env:NVIDIA_EMBEDDING_API_KEY="<your_key>"
    $env:EMBEDDING_MODEL="nvidia/llama-3_2-nemoretriever-300m-embed-v2"
    $env:NVIDIA_BASE_URL="https://integrate.api.nvidia.com/v1"  # optional if already set
    python scripts/test_embeddings.py

Exits with non-zero if the embedding call fails.
"""

import os
import sys
from dotenv import load_dotenv
from openai import OpenAI


def main() -> int:
    # Load .env so keys/models are available without exporting manually
    load_dotenv()

    api_key = os.getenv("NVIDIA_EMBEDDING_API_KEY") or os.getenv("NVIDIA_API_KEY")
    base_url = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
    model = os.getenv("EMBEDDING_MODEL", "nvidia/llama-3.2-nemoretriever-300m-embed-v2")

    if not api_key:
        print("ERROR: NVIDIA_EMBEDDING_API_KEY (or NVIDIA_API_KEY) is not set", file=sys.stderr)
        return 1

    client = OpenAI(api_key=api_key, base_url=base_url)

    try:
        resp = client.embeddings.create(
            model=model,
            input=["prueba de embeddings", "segunda frase"],
            encoding_format="float",
            extra_body={"input_type": "query", "truncate": "NONE"},
        )
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR calling embeddings: {exc}", file=sys.stderr)
        return 1

    dim = len(resp.data[0].embedding)
    print(f"Embeddings OK. Model: {model} | Dim: {dim} | Items: {len(resp.data)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
