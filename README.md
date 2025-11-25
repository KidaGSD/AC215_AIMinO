# AIMinO (Napari + Agentic Control)

## File Structure

```
.
├── aimino_frontend/           # Frontend Application
│   ├── aimino_core/           # Shared core logic (handlers, executor)
│   └── napari_app/            # Napari UI application
├── src/
│   ├── api_service/           # Backend (server agents)
│   └── deployment/            # Deployment configurations (for milestone 5)
├── tests/                     # Testing pipeline (Unit, Integration, System)
├── docker-compose.test.yml    # Test orchestration
├── environment.yml            # Conda environment specification
├── .env.example               # Environment variables example
└── .github/                   # GitHub Actions CI/CD pipeline

```

## Additional Files for Milestone 4

For CI testing results, solution & technical architecture, and data versioning, please open this [Google Drive link](https://drive.google.com/drive/folders/1aN4ZzHSUJ141f9Ha4mW48-4Augia_E_h?usp=sharing).

## Quick Start

1.  **Create Environment**:
    ```bash
    # Create .env file from template
    cp .env.example .env
    
    # Create Conda environment
    conda env create -f environment.yml
    conda activate aimino
    ```

2.  **Install Frontend**:
    ```bash
    pip install -e aimino_frontend/aimino_core
    ```

3.  **Run Backend (Docker)**:
    ```bash
    # Build image
    DOCKER_BUILDKIT=1 docker build -t aimino-api:dev -f src/api_service/Dockerfile .

    # Run container
    docker run --rm -p 8000:8000 --env-file .env aimino-api:dev
    ```

4.  **Run Frontend (Napari)**:
    ```bash
    export $(grep -v '^#' .env | xargs)
    python -m aimino_frontend.napari_app.main
    ```


### Run Tests (locally)
The easiest way to run the full test suite (Unit, Integration, System) is via Docker Compose:

```bash
# Run all tests
docker-compose -f docker-compose.test.yml up --abort-on-container-exit --exit-code-from test_runner

# Clean up
docker-compose -f docker-compose.test.yml down -v
```

