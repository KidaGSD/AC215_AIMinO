"""Viewer display command handlers for napari.Viewer methods."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...command_models import (
    CmdBindKey,
    CmdCloseViewer,
    CmdExportFigure,
    CmdExportRois,
    CmdFitToLayer,
    CmdFitToView,
    CmdHelp,
    CmdOpenFile,
    CmdOpenSample,
    CmdResetView,
    CmdScreenshot,
    CmdShowViewer,
    CmdUpdateConsole,
    CmdZoomBox,
    CmdPanelToggle,
)
from ...errors import CommandExecutionError
from ...registry import register_handler
from ...handlers.layer_management.layer_list import find_layer, list_layers

def get_vispy_camera(viewer: "Viewer"):
    window = getattr(viewer, "window", None)
    if window is None:
        return None

    qt_viewer = getattr(window, "_qt_viewer", None) or getattr(window, "qt_viewer", None)
    if qt_viewer is None:
        return None

    canvas = getattr(qt_viewer, "canvas", None)
    if canvas is not None and hasattr(canvas, "scene"):
        scene = getattr(canvas, "scene", None)
        return getattr(scene, "camera", None)

    view = getattr(qt_viewer, "view", None)
    if view is not None:
        return getattr(view, "camera", None)
    return None


def set_view_box(viewer: "Viewer", x1: float, y1: float, x2: float, y2: float) -> str:
    xlo, xhi = sorted([float(x1), float(x2)])
    ylo, yhi = sorted([float(y1), float(y2)])

    camera = get_vispy_camera(viewer)
    if camera and hasattr(camera, "set_range"):
        camera.set_range(x=(xlo, xhi), y=(ylo, yhi))

    viewer.camera.center = ((xlo + xhi) / 2.0, (ylo + yhi) / 2.0)
    return f"Zoomed to ({xlo:.1f}, {ylo:.1f})–({xhi:.1f}, {yhi:.1f})"

if TYPE_CHECKING:
    from napari.viewer import Viewer


@register_handler("fit_to_view")
def handle_fit_to_view(command: CmdFitToView, viewer: "Viewer") -> str:
    """Fit the current data view to the canvas."""
    margin = command.margin or 0.05
    viewer.fit_to_view(margin=margin)
    return f"Fitted view to canvas with margin {margin:.2f}"


@register_handler("reset_view")
def handle_reset_view(command: CmdResetView, viewer: "Viewer") -> str:
    """Reset the camera and fit the current layers to the canvas."""
    margin = command.margin or 0.05
    reset_camera_angle = command.reset_camera_angle if command.reset_camera_angle is not None else True
    viewer.reset_view(margin=margin, reset_camera_angle=reset_camera_angle)
    return f"Reset view with margin {margin:.2f}, reset_camera_angle={reset_camera_angle}"


@register_handler("screenshot")
def handle_screenshot(command: CmdScreenshot, viewer: "Viewer") -> str:
    """Take a screenshot of the current view."""
    image = viewer.screenshot(
        path=command.path,
        size=command.size,
        scale=command.scale,
        canvas_only=command.canvas_only if command.canvas_only is not None else True,
        flash=command.flash if command.flash is not None else False,
    )

    if command.path:
        return f"Screenshot saved to {command.path} (shape: {image.shape})"
    return f"Screenshot captured (shape: {image.shape})"


@register_handler("export_figure")
def handle_export_figure(command: CmdExportFigure, viewer: "Viewer") -> str:
    """Export the current figure to a file."""
    viewer.export_figure(
        path=command.path,
        size=command.size,
        scale=command.scale,
        dpi=command.dpi,
        canvas_only=command.canvas_only if command.canvas_only is not None else True,
    )
    return f"Figure exported to {command.path}"


@register_handler("export_rois")
def handle_export_rois(command: CmdExportRois, viewer: "Viewer") -> str:
    """Export ROIs (regions of interest) to files."""
    screenshot_list = viewer.export_rois(
        path=command.path,
        scale=command.scale,
        canvas_only=command.canvas_only if command.canvas_only is not None else True,
    )
    return f"Exported {len(screenshot_list)} ROI(s) to {command.path}"


@register_handler("open")
def handle_open(command: CmdOpenFile, viewer: "Viewer") -> str:
    """Open a file or list of files and add layers to viewer."""
    kwargs = command.kwargs or {}
    layers = viewer.open(
        path=command.path,
        stack=command.stack if command.stack is not None else False,
        plugin=command.plugin or "napari",
        layer_type=command.layer_type,
        **kwargs,
    )

    layer_names = [layer.name for layer in layers]
    return f"Opened {len(layers)} layer(s): {', '.join(layer_names)}"


@register_handler("open_sample")
def handle_open_sample(command: CmdOpenSample, viewer: "Viewer") -> str:
    """Open a sample from a plugin and add it to the viewer."""
    kwargs = command.kwargs or {}
    layers = viewer.open_sample(
        plugin=command.plugin,
        sample=command.sample,
        reader_plugin=command.reader_plugin,
        **kwargs,
    )

    layer_names = [layer.name for layer in layers]
    return f"Opened sample '{command.sample}' from plugin '{command.plugin}': {', '.join(layer_names)}"


@register_handler("close")
def handle_close(command: CmdCloseViewer, viewer: "Viewer") -> str:
    """Close the viewer window."""
    viewer.close()
    return "Viewer closed"


@register_handler("show")
def handle_show(command: CmdShowViewer, viewer: "Viewer") -> str:
    """Resize, show, and raise the viewer window."""
    block = command.block if command.block is not None else False
    viewer.show(block=block)
    return "Viewer shown"


@register_handler("bind_key")
def handle_bind_key(command: CmdBindKey, viewer: "Viewer") -> str:
    """Bind a key combination to a function."""
    if not command.func:
        raise CommandExecutionError("Function name is required for bind_key")

    # Note: bind_key expects a callable function, but we're accepting a string
    # In practice, you may need to look up the function from a registry
    # This is a simplified implementation
    overwrite = command.overwrite if command.overwrite is not None else False
    viewer.bind_key(command.key_bind, command.func, overwrite=overwrite)
    return f"Bound key '{command.key_bind}' to function '{command.func}'"


@register_handler("update_console")
def handle_update_console(command: CmdUpdateConsole, viewer: "Viewer") -> str:
    """Update console's namespace with desired variables."""
    if not command.variables:
        raise CommandExecutionError("Variables are required for update_console")

    viewer.update_console(command.variables)
    return f"Updated console with variables: {command.variables}"


@register_handler("fit_to_layer")
def handle_fit_to_layer(command: CmdFitToLayer, viewer: "Viewer") -> str:
    layer = find_layer(viewer, command.name)
    if layer is None:
        raise CommandExecutionError(
            f"Layer '{command.name}' not found. Layers: {', '.join(list_layers(viewer)) or '(none)'}"
        )

    world_extent = getattr(layer.extent, "world", None)
    if world_extent is None:
        raise CommandExecutionError(f"Layer '{layer.name}' does not expose world extent.")

    (ymin, xmin), (ymax, xmax) = world_extent[0][:2], world_extent[1][:2]
    return set_view_box(viewer, xmin, ymin, xmax, ymax)


@register_handler("zoom_box")
def handle_zoom_box(command: CmdZoomBox, viewer: "Viewer") -> str:
    x1, y1, x2, y2 = command.box
    return set_view_box(viewer, x1, y1, x2, y2)


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


__all__ = [
    "handle_bind_key",
    "handle_close",
    "handle_export_figure",
    "handle_export_rois",
    "handle_fit_to_layer",
    "handle_fit_to_view",
    "handle_help",
    "handle_open",
    "handle_open_sample",
    "handle_reset_view",
    "handle_screenshot",
    "handle_show",
    "handle_update_console",
    "handle_zoom_box",
    "handle_panel_toggle",
    "get_vispy_camera",
    "set_view_box",
]

