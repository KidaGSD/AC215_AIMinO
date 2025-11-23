"""UI and panel command handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..command_models import CmdHelp, CmdListLayers, CmdPanelToggle
from ..errors import CommandExecutionError
from ..registry import register_handler
from .shared import list_layers

if TYPE_CHECKING:
    from napari.viewer import Viewer


@register_handler("panel_toggle")
def handle_panel_toggle(command: CmdPanelToggle, viewer: "Viewer") -> str:
    docks = getattr(viewer.window, "_dock_widgets", {})
    if command.name in docks:
        docks[command.name].setVisible(command.op == "open")
        return f"{'Opened' if command.op == 'open' else 'Closed'} panel '{command.name}'"

    lname = command.name.lower().strip()
    exact_matches = [key for key in docks if key.lower() == lname]
    if len(exact_matches) == 1:
        docks[exact_matches[0]].setVisible(command.op == "open")
        return f"{'Opened' if command.op == 'open' else 'Closed'} panel '{exact_matches[0]}'"

    partial_matches = [key for key in docks if lname in key.lower()]
    if len(partial_matches) == 1:
        docks[partial_matches[0]].setVisible(command.op == "open")
        return f"{'Opened' if command.op == 'open' else 'Closed'} panel '{partial_matches[0]}'"
    if len(partial_matches) > 1:
        raise CommandExecutionError(
            f"Panel name '{command.name}' is ambiguous: {', '.join(partial_matches)}"
        )

    raise CommandExecutionError(
        f"Panel '{command.name}' not found. Panels: {', '.join(docks.keys()) or '(none)'}"
    )


@register_handler("list_layers")
def handle_list_layers(command: CmdListLayers, viewer: "Viewer") -> str:  # noqa: ARG001
    return "Layers: " + (", ".join(list_layers(viewer)) or "(none)")


@register_handler("help")
def handle_help(command: CmdHelp, viewer: "Viewer") -> str:  # noqa: ARG001
    return (
        "Examples:\n"
        "- show nuclei layer\n"
        "- hide layer cells\n"
        "- center on 250, 300\n"
        "- zoom box 0,0,512,512\n"
        "- set zoom 1.5\n"
        "- fit to layer nuclei\n"
        "- list layers\n"
    )


__all__ = [
    "handle_help",
    "handle_list_layers",
    "handle_panel_toggle",
]
