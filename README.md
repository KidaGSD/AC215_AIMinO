# AIMinO (Napari + Agentic Control)

## File Structure

```
.
├── aimino_frontend/                    # Frontend Application Package
│   ├── src/
│   │   └── aimino_frontend/
│   │       ├── aimino_core/            # Shared core logic (handlers, executor)
│   │       │   ├── handlers/          # Command handlers
│   │       │   ├── command_models.py  # Command definitions
│   │       │   └── registry.py        # Handler registry
│   │       └── napari_app/            # Napari UI application
│   ├── pyproject.toml                 # Package configuration
│   └── README.md                      # Frontend package docs
├── src/
│   ├── api_service/                   # Backend (server agents)
│   └── deployment/                    # Deployment configurations
├── tests/                             # Testing pipeline (Unit, Integration, System)
├── docker-compose.test.yml            # Test orchestration
├── environment.yml                    # Conda environment specification
├── .env.example                       # Environment variables example
└── .github/                           # GitHub Actions CI/CD pipeline

```


## Quick Start

### Scenario A: Regular Users (Plugin Only)

If you just want to use the AIMinO plugin, **you don't need to create a Conda environment**:

1. **Install Plugin**:
   ```bash
   pip install aimino
   ```
   
   > **Note**: If the package is not yet published to PyPI, you can install from source:
   > ```bash
   > cd aimino_frontend
   > pip install -e .
   > ```

2. **Launch Napari and Use Plugin**:
   ```bash
   # Launch Napari (command line or desktop icon)
   napari
   
   # In the Napari menu:
   # Plugins → AIMinO ChatBox → Open ChatBox
   # ChatBox will appear as a dock widget on the right
   ```

**Prerequisites**: The backend API service must be running. If the backend is not running, refer to the backend startup steps in "Scenario B".

---

### Scenario B: Developers (Full Development Environment)

If you need to develop or modify code:

1.  **Create Environment**:
    ```bash
    # Create .env file from template
    cp .env.example .env
    
    # Create Conda environment
    conda env create -f environment.yml
    conda activate aimino
    ```

2.  **Install Frontend (Development Mode)**:
    ```bash
    cd aimino_frontend
    pip install -e .
    ```
    
    This installs the `aimino` package (which includes `aimino_core` and `napari_app`) in editable mode.

3.  **Run Backend (Docker)**:
    ```bash
    # IMPORTANT: Run from project root directory (not from aimino_frontend/)
    # If you're in aimino_frontend/, go back: cd ..
    
    # Build image
    DOCKER_BUILDKIT=1 docker build -t aimino-api:dev -f src/api_service/Dockerfile .

    # Run container
    docker run --rm -p 8000:8000 --env-file .env aimino-api:dev
    ```
    
    **Note**: The Docker build command must be run from the project root directory (where both `src/` and `aimino_frontend/` directories are located).

4.  **Run Frontend (Napari)**:

    **Method A: Use as Napari Plugin (Recommended)**:
    ```bash
    # 1. Launch Napari (command line or desktop icon)
    napari
    
    # 2. In the Napari menu:
    #    Plugins → AIMinO ChatBox → Open ChatBox
    #    ChatBox will appear as a dock widget on the right
    ```

    **Method B: Command Line Launch (Standalone Mode)**:
    ```bash
    # Use command line tool
    aimino-napari
    
    # Or use Python module
    export $(grep -v '^#' .env | xargs)
    python -m aimino_frontend.napari_app.main
    ```
    
    **Note**: Method A is the officially recommended way by Napari, allowing users to open ChatBox through the menu in an already open Napari. Method B will create a new Napari viewer and automatically add sample data.


## Testing

### Test Napari Plugin

1. **Install/Reinstall Plugin**:
   ```bash
   cd aimino_frontend
   pip install -e .
   ```
   
   **Important**: If the plugin has already been installed, you need to reinstall to ensure the new configuration takes effect:
   ```bash
   pip install -e . --force-reinstall --no-deps
   ```

2. **Verify Plugin Registration**:
   ```bash
   # Check if the plugin is recognized by Napari
   napari --info
   # You should be able to see the "aimino" plugin
   
   # Or use npe2 command to check
   npe2 list
   ```

3. **Restart Napari**:
   ```bash
   # Completely close all Napari windows, then restart
   napari
   ```
   
   **Important**: After installing or updating a plugin, you must completely restart Napari for the new plugin to be recognized.

4. **Test Plugin Functionality**:
   ```bash
   # In Napari:
   # 1. Open menu Plugins → AIMinO ChatBox → Open ChatBox
   # 2. Confirm ChatBox dock widget appears on the right
   # 3. Try entering commands, such as "show layers"
   ```

### Troubleshooting

If the plugin does not appear in the menu:

**⚠️ Most Important: Ensure the plugin is installed in the same Python environment that Napari uses!**

1. **Find the Python Environment Used by Napari**:
   ```bash
   # Method 1: Check Napari's Python path
   napari --info | grep "Python"
   
   # Method 2: Run in Napari
   # Open Napari → Plugins → Console → Enter:
   # import sys; print(sys.executable)
   ```

2. **Install Plugin in That Environment**:
   ```bash
   # If Napari uses conda environment
   conda activate <napari_env_name>
   cd aimino_frontend
   pip install -e .
   
   # If Napari uses system Python
   # Make sure to use the same Python interpreter
   /path/to/napari/python -m pip install -e aimino_frontend/
   ```

3. **Confirm Plugin is Installed**:
   ```bash
   # Use Napari's Python environment
   python -c "import aimino_frontend; print('✓ Plugin installed')"
   pip list | grep aimino
   ```

4. **Check Entry Point**:
   ```bash
   # Use Napari's Python environment
   python -c "from aimino_frontend.napari_app import _get_manifest; import json; print(json.dumps(_get_manifest(), indent=2))"
   ```

5. **Clear Napari Cache**:
   ```bash
   # Napari cache location (macOS)
   rm -rf ~/.napari/plugins
   # Then restart Napari
   ```

6. **Check Napari Version**:
   ```bash
   napari --version
   # Make sure to use a version that supports npe2 (napari >= 0.4.0)
   ```

7. **Verify Using Test Script**:
   ```bash
   cd aimino_frontend
   # Run using Napari's Python environment
   python test_plugin.py
   ```

### Run Full Test Suite

The easiest way to run the full test suite (Unit, Integration, System) is via Docker Compose:

```bash
# Run all tests
docker-compose -f docker-compose.test.yml up --abort-on-container-exit --exit-code-from test_runner

# Clean up
docker-compose -f docker-compose.test.yml down -v
```

