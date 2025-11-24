"""Command handler package."""

from __future__ import annotations

from typing import Dict

from ..command_models import BaseNapariCommand
from ..registry import CommandHandler

DEFAULT_HANDLER_MODULES = [
    ".layers",
    ".viewer",
    ".ui",
]

_loaded = False


def register_default_handlers(registry: Dict[str, CommandHandler]) -> None:
    """Ensure default handlers are registered."""
    global _loaded
    _ = registry  # placeholder to keep signature consistent
    if _loaded:
        return

    from importlib import import_module

    for module_name in DEFAULT_HANDLER_MODULES:
        import_module(module_name, package=__name__)

    _loaded = True


__all__ = ["register_default_handlers"]
