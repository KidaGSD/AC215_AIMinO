# AIMinO Frontend Package

A Napari frontend application for AIMinO, providing command execution and agent client functionality for bioimage analysis.

## Package Structure

This package uses a standard src-layout structure:

```
aimino_frontend/
├── src/
│   └── aimino_frontend/  # Python package source
│       ├── __init__.py
│       ├── aimino_core/  # Core command models, handlers, and executor
│       │   ├── handlers/ # Various command handlers
│       │   └── ...
│       └── napari_app/   # Napari application entry points and agent client
│           ├── main.py  # Main launch function
│           └── client_agent.py  # Agent client
├── pyproject.toml        # Package configuration
└── README.md
```

## Installation

### Install from PyPI

```bash
pip install aimino
```

### Development Installation

Install in development mode from the `aimino_frontend` directory:

```bash
pip install -e .
```

### Production Installation

```bash
pip install .
```

### Build Distribution Packages

```bash
pip install build
python -m build
```

This will generate a `dist/` directory containing `.whl` and `.tar.gz` files.

## Usage

After installation, you can use the package in the following ways:

### As a Command Line Tool

```bash
aimino-napari
```

### As a Python Module

```python
from aimino_frontend.napari_app import launch
launch()
```

### Import Core Functionality

```python
from aimino_frontend.aimino_core import execute_command, CommandExecutionError
from aimino_frontend.napari_app.client_agent import AgentClient
```

## Dependencies

Main dependencies include:
- `napari`: Napari visualization framework
- `pydantic>=2`: Data validation
- `httpx`: HTTP client
- `google-genai`: Google GenAI SDK
- `qtpy`: Qt Python bindings
- `numpy`: Numerical computing

See `pyproject.toml` for the complete dependency list.

## Development

Install development dependencies:

```bash
pip install -e ".[dev]"
```

Run tests:

```bash
pytest
```

## Napari Plugin

This package includes a Napari plugin that can be accessed through the Napari plugin menu. The plugin provides an interactive chatbox interface for AI-powered image analysis commands.

## License

MIT License

## Authors

AIMinO Team: Yingxiao (TK) Shi, Kida Huang, Yinuo Cheng, Yuan Tian

## Project Links

- Homepage: https://github.com/KidaGSD/AC215_AIMinO
- Repository: https://github.com/KidaGSD/AC215_AIMinO
- Issues: https://github.com/KidaGSD/AC215_AIMinO/issues
