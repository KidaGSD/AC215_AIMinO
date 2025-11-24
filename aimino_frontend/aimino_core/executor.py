"""Command execution entry points."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast, get_args

from .command_models import BaseCommandAdapter, BaseNapariCommand
from .errors import CommandExecutionError
from .registry import dispatch

if TYPE_CHECKING:
    from napari.viewer import Viewer


def execute_command(
    command: BaseNapariCommand | dict[str, Any],
    viewer: "Viewer",
) -> str:
    """Validate and execute a command on the provided Napari viewer."""
    union_args = get_args(BaseNapariCommand)
    if isinstance(command, union_args):
        cmd = cast(BaseNapariCommand, command)
    else:
        cmd = BaseCommandAdapter.validate_python(command)

    handler = dispatch(cmd.action)
    return handler(cmd, viewer)


__all__ = [
    "CommandExecutionError",
    "execute_command",
]
