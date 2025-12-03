"""Command handler package."""

from __future__ import annotations

from typing import Dict

from ..command_models import BaseNapariCommand
from ..registry import CommandHandler

DEFAULT_HANDLER_MODULES = [
    ".viewer_display.viewer",
    ".viewer_display.camera",
    ".viewer_display.dims",
    ".viewer_display.viewer_model",
    ".layer_management.layer_creation",
    ".layer_management.layer_list",
    ".layer_management.layer_selection",
    ".layer_visualization.image_layer",
    ".layer_visualization.points_layer",
    ".layer_visualization.shapes_layer",
    ".layer_visualization.labels_layer",
]

_loaded = False


def register_default_handlers(registry: Dict[str, CommandHandler]) -> None:
    """Ensure default handlers are registered."""
    global _loaded
    _ = registry  # placeholder to keep signature consistent
    if _loaded:
        return

    from importlib import import_module
    import logging

    logger = logging.getLogger(__name__)

    for module_name in DEFAULT_HANDLER_MODULES:
        try:
            import_module(module_name, package=__name__)
        except ImportError as e:
            # Log warning but don't fail - some modules may not be available in all environments
            logger.warning(
                f"Failed to import handler module {module_name}: {e}. "
                "This may be expected in some deployment environments."
            )
        except Exception as e:
            # Log other errors but continue
            logger.error(
                f"Unexpected error importing handler module {module_name}: {e}",
                exc_info=True,
            )

    _loaded = True


__all__ = ["register_default_handlers"]
