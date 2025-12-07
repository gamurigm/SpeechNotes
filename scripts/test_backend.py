#!/usr/bin/env python3
"""
Simple test to check if backend formatter endpoints work
"""

import requests
import time

print("🧪 Testing Backend Formatter Endpoints")
print("=" * 60)

# Wait for backend to be ready
print("⏳ Waiting for backend to start...")
max_attempts = 10
for i in range(max_attempts):
    try:
        response = requests.get("http://localhost:8001/", timeout=2)
        if response.status_code == 200:
            print("✅ Backend is running!")
            break
    except:
        time.sleep(1)
        if i == max_attempts - 1:
            print("❌ Backend not responding after 10 seconds")
            print("   Make sure: python -m uvicorn main:socket_app --host 0.0.0.0 --port 8001 --reload")
            exit(1)

# Test files endpoint
print("\n📁 Testing GET /api/format/files...")
try:
    response = requests.get("http://localhost:8001/api/format/files", timeout=5)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        files = response.json()
        print(f"   ✅ Found {len(files)} files")
        if files:
            print(f"   First file: {files[0]['name']}")
    else:
        print(f"   ❌ Error: {response.text}")
except Exception as e:
    print(f"   ❌ Exception: {e}")

print("\n" + "=" * 60)
print("If files endpoint works, open: http://localhost:3006/formatter")
