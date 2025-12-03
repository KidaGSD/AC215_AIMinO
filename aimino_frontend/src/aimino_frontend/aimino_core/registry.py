"""Command registry utilities."""

from __future__ import annotations

from typing import Callable, Dict, List, TYPE_CHECKING

from .command_models import BaseNapariCommand

if TYPE_CHECKING:
    from napari.viewer import Viewer

CommandHandler = Callable[[BaseNapariCommand, "Viewer"], str]

COMMAND_REGISTRY: Dict[str, CommandHandler] = {}


def register_handler(action: str) -> Callable[[CommandHandler], CommandHandler]:
    """Decorator used by handler modules to register command implementations."""

    def decorator(func: CommandHandler) -> CommandHandler:
        if action in COMMAND_REGISTRY:
            raise ValueError(f"Handler already registered for action '{action}'")
        COMMAND_REGISTRY[action] = func
        return func

    return decorator


def available_actions() -> List[str]:
    """Return the list of currently registered actions."""
    from .handlers import register_default_handlers

    register_default_handlers(COMMAND_REGISTRY)
    return sorted(COMMAND_REGISTRY.keys())


def dispatch(action: str) -> CommandHandler:
    """Retrieve a handler for the given action."""
    from .handlers import register_default_handlers
    from .errors import CommandExecutionError

    register_default_handlers(COMMAND_REGISTRY)
    handler = COMMAND_REGISTRY.get(action)
    if handler is None:
        raise CommandExecutionError(f"Unsupported action: {action}")
    return handler


__all__ = [
    "COMMAND_REGISTRY",
    "CommandHandler",
    "available_actions",
    "dispatch",
    "register_handler",
]
