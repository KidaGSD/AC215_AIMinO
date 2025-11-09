"""Handbook loaders for AIMinO agents."""

from importlib import resources


def load_text(name: str) -> str:
    return resources.files(__package__).joinpath(name).read_text(encoding="utf-8")


__all__ = ["load_text"]
