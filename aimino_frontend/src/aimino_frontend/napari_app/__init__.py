"""Napari desktop entry points for AIMinO."""

# Note: We don't use `from __future__ import annotations` here
# because Napari's dependency injection system needs actual type objects,
# not string annotations

from typing import TYPE_CHECKING
import pathlib
import os
import sys
import types

# CRITICAL: In a Napari environment, napari is always available
# We import it directly to ensure type annotations work with dependency injection
import napari

# Export the path to napari.yaml for npe2 (like napari-svg does)
# This allows npe2 to find the yaml file when entry point is "module:napari.yaml"
_napari_yaml_path = pathlib.Path(__file__).parent / "napari.yaml"
if _napari_yaml_path.exists():
    # Create a module-like object with a 'yaml' attribute pointing to the file path
    # Use a different name to avoid conflicts
    _napari_yaml_module = types.ModuleType('napari')
    _napari_yaml_module.yaml = str(_napari_yaml_path)
    # Store it in sys.modules so npe2 can find it
    if 'aimino_frontend.napari_app.napari' not in sys.modules:
        sys.modules['aimino_frontend.napari_app.napari'] = _napari_yaml_module

def _get_manifest() -> dict:
    """Return the Napari plugin manifest (npe2 format).
    
    This function reads the napari.yaml file and returns its contents.
    """
    import yaml
    
    manifest_path = pathlib.Path(__file__).parent / "napari.yaml"
    if manifest_path.exists():
        with open(manifest_path) as f:
            return yaml.safe_load(f)
    else:
        # Fallback if yaml file doesn't exist
        return {
            "name": "aimino",
            "display_name": "AIMinO ChatBox",
            "version": "0.1.0",
            "schema_version": "0.1.0",
            "contributions": {
                "commands": [
                    {
                        "id": "aimino.open_chatbox",
                        "python_name": "aimino_frontend.napari_app:open_chatbox",
                        "title": "Open ChatBox",
                    }
                ],
                "widgets": [
                    {
                        "command": "aimino.open_chatbox",
                        "display_name": "AIMinO ChatBox",
                    }
                ],
                "menus": {
                    "napari/plugins": [
                        {
                            "command": "aimino.open_chatbox",
                            "display_name": "AIMinO ChatBox",
                        }
                    ]
                },
            },
        }

def launch():
    """Launch Napari with AIMinO ChatBox."""
    from .main import launch as _launch
    return _launch()

def open_chatbox(viewer: napari.Viewer):
    """Open ChatBox in the given viewer.
    
    This function is called by Napari's plugin system.
    The viewer parameter is automatically injected by Napari via dependency injection.
    
    Args:
        viewer: napari.Viewer instance (injected by Napari)
    """
    from .main import open_chatbox as _open_chatbox
    return _open_chatbox(viewer)

def get_dock_widget(viewer: napari.Viewer):
    """Get the ChatBox dock widget.
    
    This function is called by Napari's plugin system.
    The viewer parameter is automatically injected by Napari via dependency injection.
    
    Args:
        viewer: napari.Viewer instance (injected by Napari)
    """
    from .main import get_dock_widget as _get_dock_widget
    return _get_dock_widget(viewer)

__all__ = ["launch", "open_chatbox", "get_dock_widget", "_get_manifest"]
