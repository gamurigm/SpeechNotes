
import os
from openai import OpenAI
from dotenv import load_dotenv, dotenv_values

# Load values from .env file directly to ignore system env vars
env_vars = dotenv_values(".env")
file_api_key = env_vars.get("NVIDIA_API_KEY")

# Hardcoded keys to test
keys_to_test = [
    ("From .env", file_api_key),
    ("Double Dash", "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"),
    ("Single Dash", "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")
]

base_url = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
model_name = os.getenv("MODEL_NAME", "deepseek-ai/deepseek-v3.1-terminus")

print(f"Testing NVIDIA NIM API...")
print(f"URL: {base_url}")
print(f"Model: {model_name}")

for label, key in keys_to_test:
    print(f"\nTesting Key: {label}")
    if not key:
        print("  Skipping (None)")
        continue
        
    print(f"  Key: {key[:10]}...{key[-5:]}")
    
    client = OpenAI(
        base_url=base_url,
        api_key=key
    )

    try:
        completion = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": "Hi"}],
            temperature=0.5,
            max_tokens=10,
            stream=False
        )
        print("  Result: SUCCESS")
    except Exception as e:
        print(f"  Result: FAILED - {e}")
