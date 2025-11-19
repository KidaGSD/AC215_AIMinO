"""Simple test script for the Napari Agent API."""

from __future__ import annotations

import json
import sys

import requests


def test_health_check(api_url: str = "http://localhost:8000") -> bool:
    """Test the health check endpoint."""
    print(f"测试健康检查端点: {api_url}/health")
    try:
        response = requests.get(f"{api_url}/health", timeout=5)
        response.raise_for_status()
        result = response.json()
        print(f"✓ 健康检查通过: {result}")
        return result.get("runner_initialized", False)
    except Exception as e:
        print(f"✗ 健康检查失败: {e}")
        return False


def test_invoke(api_url: str = "http://localhost:8000", user_input: str = "show nuclei layer") -> bool:
    """Test the /invoke endpoint."""
    print(f"\n测试 /invoke 端点: {api_url}/invoke")
    print(f"用户输入: {user_input}")
    
    payload = {
        "user_input": user_input,
        "context": None  # 可选，可以添加更多上下文
    }
    
    try:
        print("发送请求...")
        response = requests.post(
            f"{api_url}/invoke",
            json=payload,
            timeout=120  # LLM可能需要更长时间
        )
        response.raise_for_status()
        result = response.json()
        
        print(f"✓ 请求成功!")
        print(f"返回的命令数量: {len(result.get('final_commands', []))}")
        print(f"命令详情:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        return True
    except requests.exceptions.ConnectionError:
        print("✗ 无法连接到服务器。请确保API服务器正在运行。")
        print("   启动命令: python -m src.server.start_api")
        return False
    except requests.exceptions.Timeout:
        print("✗ 请求超时。LLM可能需要更长时间响应。")
        return False
    except requests.exceptions.HTTPError as e:
        print(f"✗ HTTP错误: {e.response.status_code}")
        print(f"  响应内容: {e.response.text}")
        return False
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False


def main():
    """Run all tests."""
    api_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    user_input = sys.argv[2] if len(sys.argv) > 2 else "show nuclei layer"
    
    print("=" * 60)
    print("Napari Agent API 测试")
    print("=" * 60)
    print(f"API URL: {api_url}\n")
    
    # 测试健康检查
    if not test_health_check(api_url):
        print("\n⚠️  服务器可能未正确初始化。请检查:")
        print("   1. API服务器是否正在运行")
        print("   2. 环境变量是否正确设置 (GEMINI_API_KEY等)")
        sys.exit(1)
    
    # 测试invoke端点
    success = test_invoke(api_url, user_input)
    
    print("\n" + "=" * 60)
    if success:
        print("✓ 所有测试通过!")
    else:
        print("✗ 测试失败")
        sys.exit(1)


if __name__ == "__main__":
    main()

