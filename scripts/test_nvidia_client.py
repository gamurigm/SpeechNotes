"""
Test NVIDIA NIM Client
Tests the basic functionality of the NVIDIA inference client.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.llm.nvidia_client import NvidiaInferenceClient


def test_basic_generation():
    """Test basic text generation."""
    print("=" * 60)
    print("Test 1: Basic Text Generation")
    print("=" * 60)
    
    client = NvidiaInferenceClient()
    
    prompt = "Explica en 2 oraciones qué es la inteligencia artificial."
    print(f"\nPrompt: {prompt}\n")
    
    try:
        response = client.generate(prompt)
        print(f"Response:\n{response}\n")
        print("✓ Test passed!")
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")
        return False
    
    return True


def test_chat_completion():
    """Test chat completion with message history."""
    print("\n" + "=" * 60)
    print("Test 2: Chat Completion")
    print("=" * 60)
    
    client = NvidiaInferenceClient()
    
    messages = [
        {"role": "system", "content": "Eres un asistente útil y conciso."},
        {"role": "user", "content": "¿Cuál es la capital de Francia?"},
    ]
    
    print("\nMessages:")
    for msg in messages:
        print(f"  {msg['role']}: {msg['content']}")
    
    try:
        response = client.chat(messages)
        print(f"\nResponse:\n{response}\n")
        print("✓ Test passed!")
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")
        return False
    
    return True


def test_streaming():
    """Test streaming generation."""
    print("\n" + "=" * 60)
    print("Test 3: Streaming Generation")
    print("=" * 60)
    
    client = NvidiaInferenceClient()
    
    prompt = "Cuenta hasta 5 en español."
    print(f"\nPrompt: {prompt}\n")
    print("Streaming response:")
    
    try:
        full_response = ""
        for chunk in client.stream_generate(prompt):
            print(chunk, end="", flush=True)
            full_response += chunk
        
        print("\n")
        if full_response:
            print("✓ Test passed!")
        else:
            print("✗ Test failed: No response received")
            return False
    
    except Exception as e:
        print(f"\n✗ Test failed: {str(e)}")
        return False
    
    return True


def test_custom_parameters():
    """Test generation with custom parameters."""
    print("\n" + "=" * 60)
    print("Test 4: Custom Parameters")
    print("=" * 60)
    
    client = NvidiaInferenceClient()
    
    prompt = "Escribe una palabra creativa."
    print(f"\nPrompt: {prompt}")
    print("Parameters: temperature=0.9, max_tokens=50\n")
    
    try:
        response = client.generate(
            prompt,
            temperature=0.9,
            max_tokens=50
        )
        print(f"Response:\n{response}\n")
        print("✓ Test passed!")
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")
        return False
    
    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("NVIDIA NIM CLIENT TESTS")
    print("=" * 60)
    
    tests = [
        test_basic_generation,
        test_chat_completion,
        test_streaming,
        test_custom_parameters
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n✗ Unexpected error: {str(e)}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ All tests passed!")
    else:
        print(f"\n✗ {total - passed} test(s) failed")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
