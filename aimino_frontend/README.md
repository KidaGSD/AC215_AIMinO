# AIMinO Frontend Package

这是 AIMinO 项目的 Napari 前端包，包含核心命令执行系统和 Napari 应用界面。

## 包结构

采用标准的 src-layout 结构：

```
aimino_frontend/
├── src/
│   └── aimino_frontend/  # Python 包源码
│       ├── __init__.py
│       ├── aimino_core/  # 核心命令模型、处理器和执行器
│       │   ├── handlers/ # 各种命令处理器
│       │   └── ...
│       └── napari_app/   # Napari 应用入口和客户端代理
│           ├── main.py  # 主启动函数
│           └── client_agent.py  # 代理客户端
├── pyproject.toml        # 包配置文件
└── README.md
```

## 安装

### 开发模式安装

在 `aimino_frontend` 目录下运行：

```bash
pip install -e .
```

### 生产模式安装

```bash
pip install .
```

### 构建分发包

```bash
pip install build
python -m build
```

这将生成 `dist/` 目录，包含 `.whl` 和 `.tar.gz` 文件。

## 使用

安装后，可以通过以下方式使用：

### 作为命令行工具

```bash
aimino-napari
```

### 作为 Python 模块

```python
from aimino_frontend.napari_app import launch
launch()
```

### 导入核心功能

```python
from aimino_frontend.aimino_core import execute_command, CommandExecutionError
from aimino_frontend.napari_app.client_agent import AgentClient
```

## 依赖

主要依赖包括：
- `napari`: Napari 可视化框架
- `pydantic>=2`: 数据验证
- `httpx`: HTTP 客户端
- `google-genai`: Google GenAI SDK
- `qtpy`: Qt Python 绑定
- `numpy`: 数值计算

完整依赖列表请查看 `pyproject.toml`。

## 开发

安装开发依赖：

```bash
pip install -e ".[dev]"
```

运行测试：

```bash
pytest
```

