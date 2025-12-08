"""Dataset ingest handler."""

from typing import TYPE_CHECKING

from ...command_models import CmdDataIngest
from ...data_store import ingest_dataset
from ...errors import CommandExecutionError
from ...registry import register_handler

if TYPE_CHECKING:
    from napari.viewer import Viewer  # noqa: F401


@register_handler("data_ingest")
def handle_data_ingest(command: CmdDataIngest, viewer: "Viewer") -> str:  # noqa: ARG001
    """Ingest a dataset into AIMINO_DATA_ROOT and write manifest."""
    try:
        metadata = {"marker_cols": [command.marker_col]} if command.marker_col else None
        manifest = ingest_dataset(
            command.image_path,
            command.h5ad_path,
            command.dataset_id,
            copy_files=command.copy_files,
            metadata=metadata,
        )
        return (
            f"Ingested dataset '{command.dataset_id}' "
            f"(image={manifest['image_path']}, h5ad={manifest['h5ad_path']})"
        )
    except Exception as exc:
        raise CommandExecutionError(f"Failed to ingest dataset: {exc}") from exc


__all__ = ["handle_data_ingest"]
