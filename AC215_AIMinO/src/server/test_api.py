"""Simple test script for the Napari Agent API."""

from __future__ import annotations

import json
import sys

import requests


def test_health_check(api_url: str = "http://localhost:8000") -> bool:
    """Test the health check endpoint."""
    print(f"Testing health check endpoint: {api_url}/health")
    try:
        response = requests.get(f"{api_url}/health", timeout=5)
        response.raise_for_status()
        result = response.json()
        print(f"✓ Health check passed: {result}")
        return result.get("runner_initialized", False)
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return False


def test_invoke(api_url: str = "http://localhost:8000", user_input: str = "show nuclei layer") -> bool:
    """Test the /invoke endpoint."""
    print(f"\nTesting /invoke endpoint: {api_url}/invoke")
    print(f"User input: {user_input}")
    
    payload = {
        "user_input": user_input,
        "context": None  # Optional, can add more context
    }
    
    try:
        print("Sending request...")
        response = requests.post(
            f"{api_url}/invoke",
            json=payload,
            timeout=120  # LLM may need more time
        )
        response.raise_for_status()
        result = response.json()
        
        print(f"✓ Request successful!")
        print(f"Number of commands returned: {len(result.get('final_commands', []))}")
        print(f"Command details:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        return True
    except requests.exceptions.ConnectionError:
        print("✗ Unable to connect to server. Please ensure the API server is running.")
        print("   Start command: python -m src.server.start_api")
        return False
    except requests.exceptions.Timeout:
        print("✗ Request timeout. LLM may need more time to respond.")
        return False
    except requests.exceptions.HTTPError as e:
        print(f"✗ HTTP error: {e.response.status_code}")
        print(f"  Response content: {e.response.text}")
        return False
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


def main():
    """Run all tests."""
    api_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    user_input = sys.argv[2] if len(sys.argv) > 2 else "show nuclei layer"
    
    print("=" * 60)
    print("Napari Agent API Test")
    print("=" * 60)
    print(f"API URL: {api_url}\n")
    
    # Test health check
    if not test_health_check(api_url):
        print("\n⚠️  Server may not be properly initialized. Please check:")
        print("   1. Is the API server running?")
        print("   2. Are environment variables set correctly? (GEMINI_API_KEY, etc.)")
        sys.exit(1)
    
    # Test invoke endpoint
    success = test_invoke(api_url, user_input)
    
    print("\n" + "=" * 60)
    if success:
        print("✓ All tests passed!")
    else:
        print("✗ Test failed")
        sys.exit(1)


if __name__ == "__main__":
    main()

