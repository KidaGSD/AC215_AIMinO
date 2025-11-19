# 本地测试指南

本指南说明如何在本地测试 Napari Agent API 的前后端连接。

## 前置要求

1. **安装依赖**
   ```bash
   conda env create -f environment.yml
   conda activate aimino
   ```

2. **设置环境变量**
   需要设置 LLM API 密钥（根据你使用的模型）：
   ```bash
   export GEMINI_API_KEY=your_gemini_api_key_here
   # 或者
   export OPENAI_API_KEY=your_openai_api_key_here
   # 或者
   export HF_TOKEN=your_huggingface_token_here
   ```

3. **设置 PYTHONPATH**
   从项目根目录运行，或者设置：
   ```bash
   export PYTHONPATH=/path/to/AC215_AIMinO:$PYTHONPATH
   ```

## 测试步骤

### 方法 1: 使用测试脚本（推荐）

#### 步骤 1: 启动 API 服务器

在一个终端窗口中：
```bash
cd /path/to/AC215_AIMinO
conda activate aimino
python -m src.server.start_api
```

你应该看到类似输出：
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

#### 步骤 2: 运行测试脚本

在另一个终端窗口中：
```bash
cd /path/to/AC215_AIMinO
conda activate aimino
python -m src.server.test_api
```

或者测试自定义输入：
```bash
python -m src.server.test_api http://localhost:8000 "center on 200,300"
```

### 方法 2: 使用 curl 测试

#### 测试健康检查
```bash
curl http://localhost:8000/health
```

#### 测试 /invoke 端点
```bash
curl -X POST http://localhost:8000/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "show nuclei layer",
    "context": null
  }'
```

### 方法 3: 完整端到端测试（Napari + API）

#### 步骤 1: 启动 API 服务器
```bash
python -m src.server.start_api
```

#### 步骤 2: 启动 Napari 客户端
在另一个终端：
```bash
python -m napari_app.main
```

在 Napari 窗口右侧的 dock 中输入命令，例如：
- `show nuclei layer`
- `center on 200,300`
- `hide cells layer`

## 故障排除

### 问题 1: 无法连接到服务器
**错误**: `ConnectionError: 无法连接到API服务器`

**解决方案**:
- 确保 API 服务器正在运行
- 检查端口 8000 是否被占用
- 确认 `AIMINO_API_URL` 环境变量指向正确的地址

### 问题 2: API 服务器启动失败
**错误**: `ModuleNotFoundError` 或导入错误

**解决方案**:
- 确保已激活 conda 环境: `conda activate aimino`
- 确保从项目根目录运行
- 检查 PYTHONPATH 设置

### 问题 3: LLM API 密钥错误
**错误**: `403 Forbidden` 或认证错误

**解决方案**:
- 检查环境变量是否正确设置: `echo $GEMINI_API_KEY`
- 确认 API 密钥有效
- 查看服务器日志中的详细错误信息

### 问题 4: 请求超时
**错误**: `TimeoutError: API请求超时`

**解决方案**:
- LLM 响应可能需要较长时间，这是正常的
- 可以增加超时时间（在 `client_agent.py` 中修改 `timeout=60`）
- 检查网络连接

## 验证清单

- [ ] API 服务器成功启动（看到 "Application startup complete"）
- [ ] 健康检查返回 `{"status": "ok", "runner_initialized": true}`
- [ ] `/invoke` 端点返回有效的 `final_commands` 列表
- [ ] Napari 客户端可以连接到 API 服务器
- [ ] 命令可以在 Napari 中成功执行

## 下一步

测试通过后，你可以：
1. 将 API 服务器部署到远程服务器
2. 更新客户端中的 `AIMINO_API_URL` 环境变量
3. 配置生产环境的 CORS 设置（在 `api.py` 中）

