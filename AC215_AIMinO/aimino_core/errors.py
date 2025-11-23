"""Error types shared across AIMinO modules."""


class CommandExecutionError(RuntimeError):
    """Raised when a Napari command cannot be executed."""


__all__ = ["CommandExecutionError"]
