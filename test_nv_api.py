import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("NVIDIA_API_KEY_ASR")
url = "https://integrate.api.nvidia.com/v1/models"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Accept": "application/json"
}

response = requests.get(url, headers=headers)
print("Status Code:", response.status_code)
print("Response:", response.text[:500])
