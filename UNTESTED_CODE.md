# Untested Code Documentation

**Target Coverage: 61%**  
**Current Coverage: 61%**

## Excluded from Coverage

The following modules are explicitly excluded in `pytest.ini` and not counted in coverage:

### 1. UI Components
- `napari_app/*` - Napari application entry points and UI interactions
- `handlers/viewer_display/*` - Viewer display handlers
- `handlers/layer_management/*` - Layer management
- `handlers/layer_visualization/*` - Layer visualization

**Reason:** Requires GUI frameworks and complex mocking. Core logic is tested through API layer.

### 2. Agent Logic
- `agents/lead_manager.py` - Agent orchestration logic
- `agents/workers/*` - Worker implementations

**Reason:** Requires Google ADK runtime and active LLM API connections. Validated through integration tests.

### 3. Utility Functions
- `handlers/special_analysis/utils/image_processing.py` - Image processing
- `handlers/special_analysis/utils/neighborhood.py` - Spatial computation

**Reason:** Requires large test datasets and computational resources. Tested through API endpoint integration tests.

### 4. Test Files
- `tests/*` - Standard practice, test code excluded from coverage

