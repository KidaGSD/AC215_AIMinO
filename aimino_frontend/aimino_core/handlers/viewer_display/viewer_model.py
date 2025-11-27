"""ViewerModel command handlers for napari.components.ViewerModel methods and properties."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...command_models import (
    CmdViewerModelHelp,
    CmdViewerModelReset,
    CmdViewerModelTheme,
    CmdViewerModelTitle,
    CmdViewerModelUpdate,
    CmdViewerModelUpdateStatusFromCursor,
)
from ...errors import CommandExecutionError
from ...registry import register_handler

if TYPE_CHECKING:
    from napari.viewer import Viewer


@register_handler("viewer_model_title")
def handle_viewer_model_title(command: CmdViewerModelTitle, viewer: "Viewer") -> str:
    """Set the title of the viewer model."""
    title = command.title
    viewer.title = title
    return f"Set viewer title to '{title}'"


@register_handler("viewer_model_theme")
def handle_viewer_model_theme(command: CmdViewerModelTheme, viewer: "Viewer") -> str:
    """Set the theme of the viewer."""
    theme = command.theme
    viewer.theme = theme
    return f"Set viewer theme to '{theme}'"


@register_handler("viewer_model_help")
def handle_viewer_model_help(command: CmdViewerModelHelp, viewer: "Viewer") -> str:
    """Set the help message of the viewer model."""
    help_text = command.help
    viewer.help = help_text
    return f"Set viewer help message to '{help_text}'"


@register_handler("viewer_model_reset")
def handle_viewer_model_reset(command: CmdViewerModelReset, viewer: "Viewer") -> str:
    """Reset the state of the viewer model to default values."""
    viewer.reset()
    return "Viewer model reset to default values"


@register_handler("viewer_model_update")
def handle_viewer_model_update(command: CmdViewerModelUpdate, viewer: "Viewer") -> str:
    """Update viewer model properties in place."""
    if not command.values:
        raise CommandExecutionError("Values are required for viewer_model_update")
    
    recurse = command.recurse if command.recurse is not None else True
    viewer.update(command.values, recurse=recurse)
    return f"Updated viewer model with values: {command.values}"


@register_handler("viewer_model_update_status_from_cursor")
def handle_viewer_model_update_status_from_cursor(
    command: CmdViewerModelUpdateStatusFromCursor, viewer: "Viewer"
) -> str:
    """Update the status and tooltip from the cursor position."""
    viewer.update_status_from_cursor()
    return "Updated status and tooltip from cursor position"


__all__ = [
    "handle_viewer_model_help",
    "handle_viewer_model_reset",
    "handle_viewer_model_theme",
    "handle_viewer_model_title",
    "handle_viewer_model_update",
    "handle_viewer_model_update_status_from_cursor",
]

