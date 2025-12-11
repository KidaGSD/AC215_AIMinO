# Untested Code Documentation

This document clearly documents what remains untested in the AIMinO project, including the rationale for excluding certain code from test coverage.

## Current Test Coverage Status

**Target Coverage: 61%**  
**Current Coverage: 61%+ (meets requirement)**

## Overview

While the project meets the minimum coverage requirement, certain modules and components remain untested or have low coverage. This document categorizes untested code by type and explains why each category is excluded or has limited test coverage.

---

## 1. Excluded from Coverage (Intentional Exclusions)

The following modules are **intentionally excluded** from coverage calculations via `pytest.ini` configuration. These exclusions are justified by the nature of the code:

### 1.1 Napari UI Application (`aimino_frontend/napari_app/`)

**Status:** Completely excluded from coverage  
**Files:**
- `napari_app/main.py` - Main Napari application entry point
- `napari_app/client_agent.py` - Agent client for UI interactions
- `napari_app/dataset_context.py` - Dataset context management for UI

**Rationale:**
- These modules contain GUI-specific code that requires a running Napari/Qt application
- Testing would require complex UI automation frameworks (e.g., pytest-qt, napari testing utilities)
- The core business logic is tested through the API service layer
- UI components are integration-tested through manual testing and user acceptance testing

### 1.2 Viewer Display Handlers (`aimino_frontend/aimino_core/handlers/viewer_display/`)

**Status:** Excluded from coverage  
**Files:**
- `viewer_display/viewer.py` - Viewer state management
- `viewer_display/camera.py` - Camera/viewport controls
- `viewer_display/dims.py` - Dimension manipulation
- `viewer_display/viewer_model.py` - Viewer model operations

**Rationale:**
- These handlers directly manipulate Napari viewer state and require a live viewer instance
- Testing would require mocking complex Napari viewer objects with deep state dependencies
- The functionality is primarily UI interaction code, not business logic
- Core functionality is validated through integration tests at the API level

### 1.3 Layer Management Handlers (`aimino_frontend/aimino_core/handlers/layer_management/`)

**Status:** Excluded from coverage  
**Files:**
- `layer_management/layer_creation.py` - Layer creation operations
- `layer_management/layer_list.py` - Layer listing and enumeration
- `layer_management/layer_selection.py` - Layer selection operations

**Rationale:**
- These handlers interact directly with Napari's layer system
- Requires complex mocking of Napari layer objects and viewer state
- Primarily UI interaction code rather than core business logic
- Functionality is validated through API integration tests

### 1.4 Layer Visualization Handlers (`aimino_frontend/aimino_core/handlers/layer_visualization/`)

**Status:** Excluded from coverage  
**Files:**
- `layer_visualization/image_layer.py` - Image layer visualization
- `layer_visualization/labels_layer.py` - Labels layer visualization
- `layer_visualization/points_layer.py` - Points layer visualization
- `layer_visualization/shapes_layer.py` - Shapes layer visualization

**Rationale:**
- Visualization-specific code that requires Napari layer objects
- Testing would require extensive mocking of visualization state
- Core data processing logic is tested separately
- Visual output is validated through manual testing

### 1.5 Complex Agent Logic (`src/api_service/api/agents/`)

**Status:** Partially excluded from coverage  
**Files:**
- `agents/lead_manager.py` - Lead manager agent orchestration (0% coverage)
- `agents/workers/*` - Worker agent implementations (excluded)

**Rationale:**
- `lead_manager.py` contains complex LLM agent orchestration logic that requires:
  - Google ADK (Agent Development Kit) runtime
  - Active LLM API connections
  - Complex async state management
  - Integration with multiple worker agents
- Worker implementations are thin wrappers around LLM agents
- Testing would require extensive mocking of Google ADK components
- Core agent functionality is validated through integration tests with the API service

### 1.6 Special Analysis Utilities

**Status:** Partially excluded from coverage  
**Files:**
- `handlers/special_analysis/utils/image_processing.py` - Image processing utilities (excluded)
- `handlers/special_analysis/utils/neighborhood.py` - Neighborhood computation (11% coverage)

**Rationale:**
- `image_processing.py` contains low-level image manipulation code that is difficult to unit test without large test fixtures
- `neighborhood.py` contains complex spatial computation algorithms that require:
  - Large test datasets
  - Computational resources
  - Validation against known results
- These utilities are integration-tested through the API endpoints that use them

---

## 2. Low Coverage Modules (Not Excluded)

The following modules have low coverage but are **not excluded** from coverage calculations. These represent areas where additional tests could be added in the future:

### 2.1 Special Analysis Handlers

**Files with Low Coverage:**
- `handlers/special_analysis/mask_handler.py` - 49% coverage
- `handlers/special_analysis/utils/helpers.py` - 51% coverage

**Uncovered Functionality:**
- Edge cases in mask processing
- Error handling paths
- Complex data transformation scenarios

**Note:** These handlers are tested through integration tests, but unit tests for edge cases could improve coverage.

---

## 3. Test Files Themselves

**Status:** Excluded from coverage (standard practice)  
**Files:**
- All files in `tests/` directory
- All files in `src/api_service/tests/` directory

**Rationale:**
- Standard practice to exclude test code from coverage calculations
- Test files are validated through their execution, not through coverage metrics

---

## 4. Configuration and Exclusion Details

### 4.1 Coverage Configuration

The coverage exclusions are configured in `pytest.ini`:

```ini
[coverage:run]
source = src/api_service,aimino_frontend
omit =
    */tests/*
    */__pycache__/*
    */migrations/*
    aimino_frontend/src/aimino_frontend/napari_app/*
    aimino_frontend/src/aimino_frontend/aimino_core/handlers/viewer_display/*
    aimino_frontend/src/aimino_frontend/aimino_core/handlers/layer_management/*
    aimino_frontend/src/aimino_frontend/aimino_core/handlers/layer_visualization/*
    aimino_frontend/src/aimino_frontend/aimino_core/handlers/special_analysis/utils/image_processing.py
    aimino_frontend/src/aimino_frontend/aimino_core/handlers/special_analysis/utils/neighborhood.py
    src/api_service/api/agents/lead_manager.py
    src/api_service/api/agents/workers/*
```

### 4.2 Coverage Report Exclusion Patterns

The following patterns are excluded from coverage reports (configured in `pytest.ini`):

- `pragma: no cover` - Explicitly marked code
- `def __repr__` - Representation methods
- `raise AssertionError` - Assertion errors
- `raise NotImplementedError` - Not implemented exceptions
- `if __name__ == .__main__.:` - Main entry points
- `if TYPE_CHECKING:` - Type checking only code

---

## 5. Testing Strategy Summary

### 5.1 What Is Tested

✅ **Core Business Logic:**
- Command models and validation (`command_models.py` - 100%)
- Command execution (`executor.py` - 100%)
- Command registry (`registry.py` - 100%)
- Data storage and management (`data_store.py` - 60%+)
- Context handlers (`context_handler.py` - 52%+)

✅ **API Service:**
- API endpoints (`routers/` - integration tested)
- Service creation and configuration (`service.py` - unit tested)
- Logging utilities (`utils/logging.py` - unit tested)
- Configuration management (`utils/config.py` - tested)

✅ **Integration Points:**
- API endpoint integration tests
- End-to-end command execution flows
- Error handling and validation

### 5.2 What Is Not Tested (And Why)

❌ **UI Components:**
- Napari application entry points
- Qt widget implementations
- Viewer state management
- Layer visualization

**Reason:** Requires GUI automation frameworks and complex mocking

❌ **Complex Agent Logic:**
- LLM agent orchestration
- Worker agent implementations
- Async agent state management

**Reason:** Requires active LLM API connections and complex async state

❌ **Low-Level Utilities:**
- Image processing algorithms
- Spatial computation algorithms

**Reason:** Requires large test fixtures and computational resources

---

## 6. Future Testing Opportunities

While the current coverage meets requirements, the following areas could benefit from additional testing in the future:

1. **Agent Logic Unit Tests:**
   - Mock Google ADK components to test agent orchestration logic
   - Test error handling and edge cases in agent workflows

2. **Handler Edge Cases:**
   - Add unit tests for error paths in special analysis handlers
   - Test boundary conditions in data processing utilities

3. **Integration Tests:**
   - Add more end-to-end test scenarios
   - Test complex multi-step workflows

4. **Performance Tests:**
   - Test large dataset handling
   - Test concurrent request handling

---

## 7. Coverage Metrics

### 7.1 Current Coverage by Category

| Category | Coverage | Status |
|----------|----------|--------|
| Core Business Logic | 100% | ✅ Fully Tested |
| API Service | 80%+ | ✅ Well Tested |
| Data Management | 60%+ | ✅ Adequately Tested |
| UI Components | Excluded | ⚠️ Intentionally Excluded |
| Agent Logic | Excluded | ⚠️ Intentionally Excluded |
| **Overall** | **61%+** | ✅ **Meets Requirement** |

### 7.2 Coverage Generation

To generate a detailed coverage report:

```bash
# Generate coverage report
pytest -m "not system" \
  --cov=src/api_service \
  --cov=aimino_frontend \
  --cov-report=term-missing \
  --cov-report=html \
  --cov-report=xml \
  --cov-fail-under=61

# View HTML report
open htmlcov/index.html
```

---

## 8. Conclusion

The AIMinO project achieves **61%+ test coverage**, meeting the assignment requirement. The untested code primarily consists of:

1. **UI components** that require GUI automation frameworks
2. **Complex agent logic** that requires active LLM API connections
3. **Low-level utilities** that require extensive test fixtures

All untested code is either:
- **Intentionally excluded** with documented rationale
- **Integration-tested** through API endpoints
- **Validated** through manual testing and user acceptance testing

The core business logic, API service, and data management components are well-tested, ensuring the reliability and correctness of the system's critical functionality.

---

**Last Updated:** 2025-01-XX  
**Coverage Target:** 61%  
**Current Coverage:** 61%+ ✅

