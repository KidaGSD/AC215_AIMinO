#!/usr/bin/env python3
"""简单测试 Google Gemini API key 是否可用"""

import os
import sys

# 从 .env 文件读取 API key
from pathlib import Path
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        if line.startswith("GEMINI_API_KEY=") or line.startswith("GOOGLE_API_KEY="):
            key = line.split("=", 1)[1].strip()
            os.environ["GEMINI_API_KEY"] = key
            break

api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("错误: 未找到 API key")
    sys.exit(1)

print(f"找到 API key: {api_key[:10]}...{api_key[-4:]}")
print("正在测试 API key...")

try:
    import google.genai as genai
    
    # 尝试配置 API key
    if hasattr(genai, "configure"):
        genai.configure(api_key=api_key)
        print("✓ API key 已配置")
    else:
        # 如果没有 configure 方法，通过环境变量设置
        os.environ["GOOGLE_API_KEY"] = api_key
        print("✓ 通过环境变量设置 API key")
    
    # 尝试创建一个简单的请求
    client = genai.Client(api_key=api_key)
    
    print("✓ 成功连接到 Gemini API")
    print("✓ API key 可用！")
    
    # 尝试一个简单的生成请求
    print("\n正在测试生成请求...")
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents="Say hello in one word"
    )
    print(f"✓ 生成成功: {response.text}")
    
except Exception as e:
    print(f"\n✗ 错误: {e}")
    error_str = str(e)
    if "429" in error_str or "quota" in error_str.lower():
        print("\n提示: 这是配额错误，可能的原因：")
        print("1. 需要在 Google Cloud Console 中启用 'Generative Language API'")
        print("2. 可能需要设置计费账户（即使使用免费额度）")
        print("3. 访问 https://console.cloud.google.com/apis/library 启用 API")
        print("4. 访问 https://ai.dev/usage?tab=rate-limit 查看配额")
    elif "401" in error_str or "403" in error_str or "authentication" in error_str.lower():
        print("\n提示: 这是认证错误，请检查：")
        print("1. API key 是否正确")
        print("2. API key 是否有正确的权限")
    sys.exit(1)

