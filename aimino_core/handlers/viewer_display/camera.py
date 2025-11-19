"""Camera command handlers for napari.components.Camera methods and properties."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...command_models import (
    CmdCameraAngles,
    CmdCameraCenter,
    CmdCameraMousePan,
    CmdCameraMouseZoom,
    CmdCameraPerspective,
    CmdCameraReset,
    CmdCameraSetViewDirection,
    CmdCameraUpdate,
    CmdCameraZoom,
)
from ...errors import CommandExecutionError
from ...registry import register_handler

if TYPE_CHECKING:
    from napari.viewer import Viewer


@register_handler("camera_center")
def handle_camera_center(command: CmdCameraCenter, viewer: "Viewer") -> str:
    """Set the center of rotation for the camera."""
    center = command.center
    if len(center) == 2:
        # 2D: use last two values
        viewer.camera.center = (float(center[0]), float(center[1]))
        return f"Set camera center to ({float(center[0]):.1f}, {float(center[1]):.1f})"
    elif len(center) == 3:
        # 3D: use all three values
        viewer.camera.center = (float(center[0]), float(center[1]), float(center[2]))
        return f"Set camera center to ({float(center[0]):.1f}, {float(center[1]):.1f}, {float(center[2]):.1f})"
    else:
        raise CommandExecutionError(f"Center must have 2 or 3 values, got {len(center)}")


@register_handler("camera_zoom")
def handle_camera_zoom(command: CmdCameraZoom, viewer: "Viewer") -> str:
    """Set the zoom level of the camera."""
    zoom = float(command.zoom)
    viewer.camera.zoom = zoom
    return f"Set camera zoom to {zoom:.2f}"


@register_handler("camera_angles")
def handle_camera_angles(command: CmdCameraAngles, viewer: "Viewer") -> str:
    """Set the Euler angles of the camera (for 3D viewing)."""
    angles = command.angles
    if len(angles) != 3:
        raise CommandExecutionError(f"Angles must have 3 values (rx, ry, rz), got {len(angles)}")
    
    viewer.camera.angles = (float(angles[0]), float(angles[1]), float(angles[2]))
    return f"Set camera angles to ({float(angles[0]):.1f}°, {float(angles[1]):.1f}°, {float(angles[2]):.1f}°)"


@register_handler("camera_perspective")
def handle_camera_perspective(command: CmdCameraPerspective, viewer: "Viewer") -> str:
    """Set the perspective (field of view) of the camera (for 3D viewing)."""
    perspective = float(command.perspective)
    viewer.camera.perspective = perspective
    return f"Set camera perspective to {perspective:.2f}"


@register_handler("camera_mouse_pan")
def handle_camera_mouse_pan(command: CmdCameraMousePan, viewer: "Viewer") -> str:
    """Enable or disable mouse panning for the camera."""
    enabled = command.enabled
    viewer.camera.mouse_pan = enabled
    state = "enabled" if enabled else "disabled"
    return f"Mouse panning {state}"


@register_handler("camera_mouse_zoom")
def handle_camera_mouse_zoom(command: CmdCameraMouseZoom, viewer: "Viewer") -> str:
    """Enable or disable mouse zooming for the camera."""
    enabled = command.enabled
    viewer.camera.mouse_zoom = enabled
    state = "enabled" if enabled else "disabled"
    return f"Mouse zooming {state}"


@register_handler("camera_reset")
def handle_camera_reset(command: CmdCameraReset, viewer: "Viewer") -> str:
    """Reset the camera to default values."""
    viewer.camera.reset()
    return "Camera reset to default values"


@register_handler("camera_set_view_direction")
def handle_camera_set_view_direction(command: CmdCameraSetViewDirection, viewer: "Viewer") -> str:
    """Set camera angles from direction vectors."""
    view_direction = command.view_direction
    up_direction = command.up_direction
    
    if len(view_direction) != 3:
        raise CommandExecutionError(f"View direction must have 3 values, got {len(view_direction)}")
    
    if up_direction is not None and len(up_direction) != 3:
        raise CommandExecutionError(f"Up direction must have 3 values, got {len(up_direction)}")
    
    view_dir_tuple = (float(view_direction[0]), float(view_direction[1]), float(view_direction[2]))
    
    if up_direction is not None:
        up_dir_tuple = (float(up_direction[0]), float(up_direction[1]), float(up_direction[2]))
        viewer.camera.set_view_direction(view_direction=view_dir_tuple, up_direction=up_dir_tuple)
        return f"Set camera view direction to {view_dir_tuple} with up direction {up_dir_tuple}"
    else:
        viewer.camera.set_view_direction(view_direction=view_dir_tuple)
        return f"Set camera view direction to {view_dir_tuple}"


@register_handler("camera_update")
def handle_camera_update(command: CmdCameraUpdate, viewer: "Viewer") -> str:
    """Update camera properties in place."""
    if not command.values:
        raise CommandExecutionError("Values are required for camera_update")
    
    viewer.camera.update(command.values)
    return f"Updated camera with values: {command.values}"


__all__ = [
    "handle_camera_angles",
    "handle_camera_center",
    "handle_camera_mouse_pan",
    "handle_camera_mouse_zoom",
    "handle_camera_perspective",
    "handle_camera_reset",
    "handle_camera_set_view_direction",
    "handle_camera_update",
    "handle_camera_zoom",
]

