"""Minimal Napari launcher wired to AIMinO agent stack."""

from pathlib import Path
from typing import Optional, List
import asyncio
import os
import threading

# Load .env file from project root
try:
    from dotenv import load_dotenv
    # Try to find .env in common locations
    for env_path in [
        Path.cwd() / ".env",
        Path(__file__).parent.parent.parent.parent.parent.parent / ".env",
        Path.home() / ".aimino" / ".env",
    ]:
        if env_path.exists():
            load_dotenv(env_path)
            break
except ImportError:
    pass  # dotenv not installed, use system env vars

import napari
import numpy as np
from qtpy import QtWidgets, QtCore
from pydantic import BaseModel
import h5py
from tifffile import TiffFile

AUTOLOAD_SIZE_LIMIT = int(os.getenv("AIMINO_AUTLOAD_MAX_BYTES", "500000000"))  # 500MB default
DISABLE_AUTOLOAD = os.getenv("AIMINO_DISABLE_AUTOLOAD", "0").strip() == "1"
SKIP_16K_CHECK = os.getenv("AIMINO_SKIP_16K_CHECK", "0").strip() == "1"  # Skip 16k pixel limit check
AUTO_DOWNSAMPLE = int(os.getenv("AIMINO_AUTO_DOWNSAMPLE", "0"))  # Auto-downsample factor (0=disabled, 2=2x, 4=4x)

from aimino_frontend.aimino_core import CommandExecutionError, execute_command
from aimino_frontend.aimino_core.data_store import (
    ingest_dataset,
    list_datasets,
    get_dataset_paths,
    load_manifest,
    save_manifest,
    clear_processed_cache,
    suggest_dataset_id,
)
from aimino_frontend.aimino_core.handlers.context_handler import set_context_functions
from aimino_frontend.aimino_core.handlers.layer_management.layer_list import set_marker_resolver
from .client_agent import AgentClient, load_last_session_id
from .dataset_context import (
    get_context_payload,
    get_current_dataset_id,
    get_current_marker,
    get_last_radius,
    set_available_datasets,
    set_available_markers,
    set_current_dataset,
    set_marker,
    set_radius,
    update_from_command,
)

# Inject context functions into the handler
set_context_functions(
    set_dataset_fn=set_current_dataset,
    set_marker_fn=set_marker,
    get_dataset_id_fn=get_current_dataset_id,
    get_marker_fn=get_current_marker,
)
# Provide current marker to layer alias resolver (tumor/immune) for layer panel commands
set_marker_resolver(get_current_marker)


class CommandDock(QtWidgets.QWidget):
    def __init__(self, viewer: napari.Viewer, agent: AgentClient) -> None:
        super().__init__()
        self.viewer = viewer
        self.agent = agent
        self._last_session_id: str | None = load_last_session_id()

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        self.setLayout(layout)

        # Chat history area (main focus - like ChatGPT)
        self.output = QtWidgets.QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setPlaceholderText(
            "Welcome to AIMinO!\n\n"
            "Try commands like:\n"
            "  • list datasets\n"
            "  • show SOX10 density\n"
            "  • compute neighborhood for CD8\n"
            "  • center on 500, 500"
        )
        layout.addWidget(self.output, stretch=1)  # Takes most space

        # Bottom section: context + input
        bottom_section = QtWidgets.QVBoxLayout()
        bottom_section.setSpacing(6)

        # Dataset context label (compact bar)
        self.dataset_label = QtWidgets.QLabel()
        self.dataset_label.setStyleSheet(
            "font-size: 11px; padding: 4px 8px; "
            "background: #3a3a3a; border-radius: 4px; color: #aaa;"
        )
        bottom_section.addWidget(self.dataset_label)
        self._refresh_dataset_label()

        # Input row
        input_layout = QtWidgets.QHBoxLayout()
        input_layout.setSpacing(6)
        self.input = QtWidgets.QLineEdit()
        self.input.setPlaceholderText("Type a command...")
        self.input.setStyleSheet(
            "padding: 8px; border-radius: 4px; "
            "background: #2a2a2a; border: 1px solid #444;"
        )
        self.run_btn = QtWidgets.QPushButton("Send")
        self.run_btn.setFixedWidth(60)
        self.run_btn.setStyleSheet(
            "padding: 8px; border-radius: 4px; "
            "background: #4a7c59; font-weight: bold;"
        )
        input_layout.addWidget(self.input, stretch=1)
        input_layout.addWidget(self.run_btn)
        bottom_section.addLayout(input_layout)

        # Session checkbox (small, unobtrusive)
        self.restore_checkbox = QtWidgets.QCheckBox("Resume last session")
        self.restore_checkbox.setStyleSheet("font-size: 10px; color: #666;")
        if not self._last_session_id:
            self.restore_checkbox.setEnabled(False)
        bottom_section.addWidget(self.restore_checkbox)

        layout.addLayout(bottom_section)

        self.run_btn.clicked.connect(self.on_submit)
        self.input.returnPressed.connect(self.on_submit)
        self.restore_checkbox.stateChanged.connect(self.on_restore_toggled)

    def log(self, text: str) -> None:
        self.output.appendPlainText(text)
        # Auto-scroll to bottom (ChatGPT style)
        scrollbar = self.output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _update_dataset_label(self) -> None:
        ds = get_current_dataset_id()
        if ds:
            self.dataset_label.setText(f"Dataset: {ds}")
        else:
            self.dataset_label.setText("Dataset: (none selected)")

    def _refresh_dataset_label(self) -> None:
        dataset_id = get_current_dataset_id()
        marker = get_current_marker()
        if dataset_id:
            label = f"Dataset: {dataset_id}"
            if marker:
                label += f" | Marker: {marker}"
        else:
            label = "Dataset: (none selected)"
        self.dataset_label.setText(label)

    def set_current_dataset(self, dataset_id: Optional[str]) -> None:
        # Signal hook from DataImportDock
        if dataset_id:
            self.log(f"[dataset] Selected dataset '{dataset_id}'")
        self._refresh_dataset_label()

    def _with_dataset_context(self, cmd: object) -> object:
        dataset_id = get_current_dataset_id()
        marker = get_current_marker()
        if not dataset_id:
            return cmd
        if isinstance(cmd, BaseModel):
            data = cmd.model_dump()
            return self._with_dataset_context(data)
        if isinstance(cmd, dict):
            action = cmd.get("action")
            if isinstance(action, str) and action.startswith("special_"):
                new_cmd = dict(cmd)
                if "dataset_id" not in new_cmd:
                    new_cmd["dataset_id"] = dataset_id
                if marker and "marker_col" not in new_cmd and action != "data_ingest":
                    new_cmd["marker_col"] = marker
                return new_cmd
        return cmd

    def on_restore_toggled(self, state: int) -> None:
        if state == QtCore.Qt.Checked and self._last_session_id:
            self.agent.set_session_id(self._last_session_id)
            self.log(f"[session] Using last session: {self._last_session_id}")
        else:
            # When unchecked, clear explicit session so a new one can be created
            self.agent.set_session_id(None)
            self.log("[session] A new session will be created on next invoke")

    def on_submit(self) -> None:
        user_text = self.input.text().strip()
        if not user_text:
            return
        self.input.clear()
        self.log(f"> {user_text}")
        metadata = get_context_payload()

        # Disable button while processing
        self.run_btn.setEnabled(False)
        self.run_btn.setText("...")

        # Run agent in background thread to avoid UI freeze
        def run_agent():
            try:
                commands = asyncio.run(self.agent.invoke(user_text, metadata or None))
                # Use Qt signal to update UI from main thread
                QtCore.QMetaObject.invokeMethod(
                    self, "_handle_agent_response",
                    QtCore.Qt.QueuedConnection,
                    QtCore.Q_ARG(object, commands),
                    QtCore.Q_ARG(object, None)
                )
            except Exception as exc:
                QtCore.QMetaObject.invokeMethod(
                    self, "_handle_agent_response",
                    QtCore.Qt.QueuedConnection,
                    QtCore.Q_ARG(object, None),
                    QtCore.Q_ARG(object, exc)
                )

        thread = threading.Thread(target=run_agent, daemon=True)
        thread.start()

    @QtCore.Slot(object, object)
    def _handle_agent_response(self, commands, error) -> None:
        """Handle agent response in main thread."""
        # Re-enable button
        self.run_btn.setEnabled(True)
        self.run_btn.setText("Send")

        if error:
            self.log(f"[agent error] {error}")
            return

        if not commands:
            self.log("[info] No commands generated. Try rephrasing your request.")
            return

        for cmd in commands:
            try:
                enriched = self._with_dataset_context(cmd)
                action = enriched.get("action", "") if isinstance(enriched, dict) else ""

                # Handle help action specially - show cleaner output
                if action == "help":
                    msg = execute_command(enriched, self.viewer)
                    self.log(msg)  # Just show the help text, no command dump
                    continue

                # Check if dataset is required but missing
                if action.startswith("special_") and not enriched.get("dataset_id"):
                    self.log(
                        "[info] No dataset selected.\n"
                        "Please go to the 'Data' tab and:\n"
                        "  1. Select an existing dataset, or\n"
                        "  2. Import a new TIFF + h5ad pair"
                    )
                    continue

                msg = execute_command(enriched, self.viewer)
                # Show cleaner output for successful commands
                self.log(f"[{action}] {msg}")
                update_from_command(enriched)
                self._refresh_dataset_label()
            except CommandExecutionError as exc:
                self.log(f"[error] {exc}")


class DataImportDock(QtWidgets.QWidget):
    dataset_changed = QtCore.Signal(object)  # emits dataset_id or None

    def __init__(self, viewer: napari.Viewer, agent: AgentClient) -> None:
        super().__init__()
        self.viewer = viewer
        self.agent = agent
        self.setLayout(QtWidgets.QVBoxLayout())

        # Dataset basics
        basics = QtWidgets.QGroupBox("Dataset")
        basics_form = QtWidgets.QFormLayout()
        basics.setLayout(basics_form)
        self.layout().addWidget(basics)

        self.dataset_id_input = QtWidgets.QLineEdit()
        self.dataset_id_input.setPlaceholderText("auto if blank")
        basics_form.addRow("Dataset ID", self.dataset_id_input)

        self.marker_col_input = QtWidgets.QLineEdit()
        self.marker_col_input.setPlaceholderText("e.g. SOX10_positive (required to view)")
        basics_form.addRow("Marker column", self.marker_col_input)
        self.marker_col_input.textChanged.connect(self._on_marker_text_changed)

        # Files
        files = QtWidgets.QGroupBox("Files")
        files_form = QtWidgets.QFormLayout()
        files.setLayout(files_form)
        self.layout().addWidget(files)

        self.image_path_input = QtWidgets.QLineEdit()
        self.image_browse = QtWidgets.QPushButton("Browse")
        self.image_browse.clicked.connect(lambda: self._browse_file(self.image_path_input, "Select image (TIFF)", "Images (*.tif *.tiff *.ome.tif);;All Files (*)"))
        img_row = QtWidgets.QHBoxLayout()
        img_row.addWidget(self.image_path_input)
        img_row.addWidget(self.image_browse)
        files_form.addRow("TIFF image", img_row)

        self.h5ad_path_input = QtWidgets.QLineEdit()
        self.h5ad_path_input.setPlaceholderText("e.g. cells.h5ad")
        self.h5ad_browse = QtWidgets.QPushButton("Browse")
        self.h5ad_browse.clicked.connect(lambda: self._browse_file(self.h5ad_path_input, "Select h5ad", "h5ad Files (*.h5ad);;All Files (*)"))
        h5_row = QtWidgets.QHBoxLayout()
        h5_row.addWidget(self.h5ad_path_input)
        h5_row.addWidget(self.h5ad_browse)
        files_form.addRow("h5ad file", h5_row)

        # Actions
        actions = QtWidgets.QGroupBox("Actions")
        actions_layout = QtWidgets.QVBoxLayout()
        actions.setLayout(actions_layout)
        self.layout().addWidget(actions)

        # Primary action: Register dataset
        self.ingest_btn = QtWidgets.QPushButton("Register Dataset")
        self.ingest_btn.setStyleSheet("padding: 8px; font-weight: bold;")
        self.ingest_btn.clicked.connect(self._ingest_dataset)
        actions_layout.addWidget(self.ingest_btn)

        # Copy option (hidden by default, for advanced users)
        self.copy_checkbox = QtWidgets.QCheckBox("Copy files (instead of link)")
        self.copy_checkbox.setChecked(False)
        self.copy_checkbox.setStyleSheet("font-size: 11px; color: #888;")
        actions_layout.addWidget(self.copy_checkbox)

        # Hidden - not needed in current architecture
        self.remote_checkbox = QtWidgets.QCheckBox()
        self.remote_checkbox.setVisible(False)

        # Secondary actions
        secondary_row = QtWidgets.QHBoxLayout()
        hl_btn = QtWidgets.QPushButton("Load Marker Layers")
        hl_btn.clicked.connect(self._highlight_layers)
        self.cache_cleanup_btn = QtWidgets.QPushButton("Clear Cache")
        self.cache_cleanup_btn.clicked.connect(self._cleanup_cache)
        secondary_row.addWidget(hl_btn, 1)
        secondary_row.addWidget(self.cache_cleanup_btn, 1)
        actions_layout.addLayout(secondary_row)

        # Neighborhood controls
        neigh_row = QtWidgets.QHBoxLayout()
        self.neigh_radius = QtWidgets.QSpinBox()
        self.neigh_radius.setRange(1, 500)
        self.neigh_radius.setValue(int(get_last_radius() or 50))
        self.neigh_radius.setSuffix(" px")
        neigh_row.addWidget(QtWidgets.QLabel("Radius"))
        neigh_row.addWidget(self.neigh_radius)
        neigh_btn = QtWidgets.QPushButton("Compute Neighborhood")
        neigh_btn.clicked.connect(self._compute_neighborhood)
        neigh_row.addWidget(neigh_btn, 1)
        actions_layout.addLayout(neigh_row)

        # Existing datasets
        existing = QtWidgets.QGroupBox("Existing datasets")
        existing_layout = QtWidgets.QFormLayout()
        existing.setLayout(existing_layout)
        self.layout().addWidget(existing)

        self.dataset_combo = QtWidgets.QComboBox()
        self.dataset_combo.currentTextChanged.connect(self._on_dataset_selected)
        refresh_btn = QtWidgets.QPushButton("Refresh")
        refresh_btn.clicked.connect(self._refresh_datasets)
        combo_row = QtWidgets.QHBoxLayout()
        combo_row.addWidget(self.dataset_combo, stretch=1)
        combo_row.addWidget(refresh_btn)
        existing_layout.addRow("Select", combo_row)

        # Status/log area
        self.status = QtWidgets.QPlainTextEdit()
        self.status.setReadOnly(True)
        self.status.setMaximumBlockCount(200)
        self.status.setPlaceholderText("Status and guidance will appear here...")
        self.status.setMaximumHeight(160)
        self.layout().addWidget(self.status)

        # Flag to prevent autoload during initialization
        self._initializing = True
        # Defer dataset refresh to avoid blocking UI on startup
        QtCore.QTimer.singleShot(100, self._deferred_init)

    def _deferred_init(self) -> None:
        """Deferred initialization to avoid blocking UI on startup."""
        self._refresh_datasets()
        self._initializing = False

    def _detect_markers(self, h5ad_path: str) -> List[str]:
        """Try to infer marker columns from h5ad (bool or *_positive) with minimal I/O.

        OPTIMIZED: Only uses h5py for fast column name scanning without loading data.
        """
        markers: List[str] = []
        try:
            with h5py.File(h5ad_path, "r") as f:
                if "obs" in f:
                    cols = list(f["obs"].keys())
                    for name in cols:
                        lname = str(name).lower()
                        # Check for common marker naming patterns
                        if (lname.endswith("_positive") or
                            lname.endswith("_pos") or
                            lname.startswith("marker_") or
                            lname in {"tumor", "tumor_positive"}):
                            markers.append(str(name))
                        # Also check for common immune marker names
                        elif any(m in lname for m in ["cd45", "cd3", "cd4", "cd8", "cd20", "sox10", "foxp3", "ki67"]):
                            if "_positive" in lname or "_pos" in lname:
                                markers.append(str(name))
        except Exception as exc:
            self._append_status(f"[warn] h5py marker scan failed: {exc}")

        # If no markers found by name pattern, try a quick dtype check (limited)
        if not markers:
            try:
                with h5py.File(h5ad_path, "r") as f:
                    if "obs" in f:
                        obs_group = f["obs"]
                        for name in list(obs_group.keys())[:50]:  # Limit to first 50 columns
                            try:
                                ds = obs_group[name]
                                # Check if it's a categorical or boolean-like column
                                if hasattr(ds, 'dtype'):
                                    if ds.dtype == bool or str(ds.dtype).startswith('|S'):
                                        markers.append(str(name))
                            except Exception:
                                pass
            except Exception:
                pass

        return sorted(dict.fromkeys(markers))

    def _browse_file(self, target: QtWidgets.QLineEdit, title: str, filter_str: str) -> None:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, title, "", filter_str)
        if path:
            target.setText(path)

    def _append_status(self, text: str) -> None:
        self.status.appendPlainText(text)

    def _on_marker_text_changed(self, text: str) -> None:
        marker = text.strip()
        if marker and get_current_dataset_id():
            set_marker(marker)
            if DISABLE_AUTOLOAD:
                self._append_status("[info] Autoload disabled (AIMINO_DISABLE_AUTOLOAD=1); click 'Show current marker layers' to load.")
                return
            ds = get_current_dataset_id()
            base_cmd = {"dataset_id": ds, "marker_col": marker}
            self._append_status("[auto] preparing mask/density for current marker")
            try:
                manifest = load_manifest(ds)
            except Exception:
                manifest = {}
            self._safe_autoload(manifest, base_cmd)
        elif not marker:
            set_marker(None)

    def _run_command(self, cmd: dict) -> None:
        """Execute a command immediately on the viewer and log the result."""
        try:
            result = execute_command(cmd, self.viewer)
            self._append_status(f"[cmd] {cmd} -> {result}")
            update_from_command(cmd)
        except CommandExecutionError as exc:
            self._append_status(f"[cmd error] {exc}")
        except Exception as exc:
            self._append_status(f"[cmd error] {exc}")

    def _validate_inputs(self) -> Optional[str]:
        image_path = self.image_path_input.text().strip()
        h5ad_path = self.h5ad_path_input.text().strip()
        if not image_path:
            return "TIFF image path is required."
        if not h5ad_path:
            return "h5ad file path is required."
        return None

    def _within_size_limit(self, image_path: str, h5ad_path: str) -> bool:
        try:
            img_size = os.path.getsize(image_path)
            h5_size = os.path.getsize(h5ad_path)
            return max(img_size, h5_size) <= AUTOLOAD_SIZE_LIMIT
        except Exception:
            return False

    def _image_too_large(self, image_path: str) -> bool:
        """Check TIFF dimensions against common GL limits without full load."""
        if SKIP_16K_CHECK:
            return False  # User opted to skip this check
        try:
            with TiffFile(image_path) as tf:
                shape = tf.series[0].shape
            if len(shape) >= 2:
                h, w = shape[-2], shape[-1]
                return max(h, w) > 16384
        except Exception:
            return False
        return False

    def _safe_autoload(self, manifest: dict, base_cmd: dict) -> None:
        """Load mask/density if size is acceptable; otherwise warn to avoid freeze."""
        image_path = manifest.get("image_path", "")
        h5ad_path = manifest.get("h5ad_path", "")

        # If auto-downsample is enabled, skip size checks and load directly
        if AUTO_DOWNSAMPLE >= 1:
            self._append_status(f"[info] Auto-downsample enabled ({AUTO_DOWNSAMPLE}x). Loading...")
            self._run_command({"action": "special_load_marker_data", **base_cmd})
            self._run_command({"action": "special_show_mask", **base_cmd})
            self._run_command({"action": "special_show_density", **base_cmd})
            return

        if self._image_too_large(str(image_path)):
            self._append_status(
                "[info] Image exceeds 16k texture limit; auto-load skipped. "
                "Set AIMINO_AUTO_DOWNSAMPLE=2 in .env or click 'Load Marker Layers'."
            )
            return
        if not self._within_size_limit(str(image_path), str(h5ad_path)):
            self._append_status(
                "[info] Large file detected; auto-load skipped. "
                "Set AIMINO_AUTO_DOWNSAMPLE=2 in .env or click 'Load Marker Layers'."
            )
            return
        self._run_command({"action": "special_load_marker_data", **base_cmd})
        self._run_command({"action": "special_show_mask", **base_cmd})
        self._run_command({"action": "special_show_density", **base_cmd})

    def _ingest_dataset(self) -> None:
        error = self._validate_inputs()
        if error:
            self._append_status(f"[error] {error}")
            return
        dataset_id_input = self.dataset_id_input.text().strip()
        image_path = self.image_path_input.text().strip()
        h5ad_path = self.h5ad_path_input.text().strip()
        copy_files = self.copy_checkbox.isChecked()
        marker_col = self.marker_col_input.text().strip()
        # Try auto-detect marker if not provided
        if not marker_col:
            candidates = self._detect_markers(h5ad_path)
            if candidates:
                marker_col = candidates[0]
                self.marker_col_input.setText(marker_col)
                self._append_status(f"[auto] marker detected: {marker_col}")
        metadata = {"marker_cols": [marker_col]} if marker_col else None

        use_remote = self.remote_checkbox.isChecked()
        if use_remote:
            try:
                # Use existing agent transport if it supports register_dataset
                transport = getattr(self.agent, "transport", None)
                if not hasattr(transport, "register_dataset"):
                    from .client_agent import HttpTransport
                    transport = HttpTransport(os.getenv("SERVER_URL", "http://127.0.0.1:8000"))

                resp = asyncio.run(
                    transport.register_dataset(
                        image_path,
                        h5ad_path,
                        dataset_id=dataset_id_input or None,
                        copy_files=copy_files,
                        marker_col=marker_col or None,
                    )
                )
                manifest = resp.get("manifest", {})
            except Exception as exc:
                self._append_status(f"[error] remote register failed, fallback to local: {exc}")
                use_remote = False
        if not use_remote:
            try:
                manifest = ingest_dataset(
                    image_path,
                    h5ad_path,
                    dataset_id=dataset_id_input or None,
                    copy_files=copy_files,
                    metadata=metadata,
                )
            except Exception as exc:
                self._append_status(f"[error] ingest failed: {exc}")
                return

        dataset_id = manifest["dataset_id"]
        self.dataset_id_input.setText(dataset_id)
        self._append_status(f"[ok] Dataset '{dataset_id}' stored at {manifest['output_root']}")
        self._refresh_datasets(select=dataset_id)
        set_current_dataset(dataset_id, marker_col or None)
        if marker_col:
            set_available_markers([marker_col])
        # Auto-load mask/density if marker is provided
        if marker_col and not DISABLE_AUTOLOAD:
            base_cmd = {"dataset_id": dataset_id, "marker_col": marker_col}
            self._safe_autoload(manifest, base_cmd)
        self._refresh_datasets(select=dataset_id)

    def _refresh_datasets(self, select: Optional[str] = None) -> None:
        current = select or get_current_dataset_id()
        self.dataset_combo.blockSignals(True)
        self.dataset_combo.clear()
        entries = sorted(list(list_datasets()))
        set_available_datasets(entries)
        self.dataset_combo.addItem("(none)")
        autoload_ds: Optional[str] = None
        for ds in entries:
            self.dataset_combo.addItem(ds)
        selected = None
        if current and current in entries:
            index = self.dataset_combo.findText(current)
            if index != -1:
                self.dataset_combo.setCurrentIndex(index)
                selected = current
        else:
            if entries:
                # auto-select first dataset if none chosen
                self.dataset_combo.setCurrentIndex(1)
                selected = entries[0]
                autoload_ds = entries[0]
            else:
                self.dataset_combo.setCurrentIndex(0)
        self.dataset_combo.blockSignals(False)
        self._emit_selection(selected)
        if autoload_ds:
            self._on_dataset_selected(autoload_ds)

    def _on_dataset_selected(self, text: str) -> None:
        ds = text.strip()
        if ds and ds != "(none)":
            self.dataset_id_input.setText(ds)
            marker = None
            manifest_data = {}
            try:
                manifest = get_dataset_paths(ds)
                self._append_status(f"[dataset] {ds}: loaded manifest")
                manifest_data = load_manifest(ds)
                marker_cols = manifest_data.get("metadata", {}).get("marker_cols") or []
                if marker_cols:
                    marker = marker_cols[0]
                    self.marker_col_input.setText(marker)
                    set_marker(marker)
                    set_available_markers(marker_cols)
                else:
                    # Auto-detect marker if manifest missing
                    candidates = self._detect_markers(manifest.h5ad_path)
                    if candidates:
                        marker = candidates[0]
                        self.marker_col_input.setText(marker)
                        set_marker(marker)
                        set_available_markers(candidates)
                        manifest_data.setdefault("metadata", {})["marker_cols"] = candidates
                        try:
                            save_manifest(ds, manifest_data)
                            self._append_status(f"[auto] marker detected: {marker}")
                        except Exception:
                            self._append_status(f"[warn] marker detected ({marker}) but manifest save failed")
            except Exception as exc:
                self._append_status(f"[warning] Failed to read dataset '{ds}': {exc}")
            self._emit_selection(ds, marker)
            # Skip autoload during initialization to prevent UI freeze
            if getattr(self, '_initializing', False):
                self._append_status("[info] Dataset loaded. Use 'Load Marker Layers' to view.")
            elif marker and not DISABLE_AUTOLOAD and manifest_data:
                base_cmd = {"dataset_id": ds, "marker_col": marker}
                self._append_status("[auto] preparing mask/density for selected dataset")
                self._safe_autoload(manifest_data, base_cmd)
            else:
                self._append_status("[info] Autoload disabled or marker missing; use 'Load Marker Layers' to load.")
        else:
            self._emit_selection(None)
            set_available_markers([])

    def _emit_selection(self, dataset_id: Optional[str], marker: Optional[str] = None) -> None:
        set_current_dataset(dataset_id, marker)
        self.dataset_changed.emit(dataset_id)

    def _cleanup_cache(self) -> None:
        ds = get_current_dataset_id()
        if not ds:
            self._append_status("[warn] No dataset selected to clean.")
            return
        try:
            result = clear_processed_cache(ds)
            self._append_status(f"[ok] cache cleared for {ds}: {result}")
        except Exception as exc:
            self._append_status(f"[error] cache cleanup failed: {exc}")

    def _compute_neighborhood(self) -> None:
        """Compute neighborhood layers for the current dataset/marker."""
        ds = get_current_dataset_id()
        marker = get_current_marker()
        if not ds or not marker:
            self._append_status("[warn] Select dataset + marker before computing neighborhood.")
            return
        radius = float(self.neigh_radius.value())
        set_radius(radius)
        cmd = {
            "action": "special_compute_neighborhood",
            "dataset_id": ds,
            "marker_col": marker,
            "radius": radius,
            "force_recompute": False,
        }
        self._run_command(cmd)

    def _highlight_layers(self) -> None:
        """Make mask/density layers visible for current marker."""
        ds = get_current_dataset_id()
        marker = get_current_marker()
        if not ds or not marker:
            self._append_status("[warn] select dataset + marker first")
            return
        base_cmd = {"dataset_id": ds, "marker_col": marker}
        try:
            manifest = load_manifest(ds)
        except Exception:
            manifest = {}
        markers = manifest.get("metadata", {}).get("marker_cols") or []
        if markers:
            set_available_markers(markers)
        if self._image_too_large(str(manifest.get("image_path", ""))):
            self._append_status("[warn] Image too large for safe load; consider downsampled/pyramid data.")
            return
        if not self._within_size_limit(
            str(manifest.get("image_path", "")), str(manifest.get("h5ad_path", ""))
        ):
            self._append_status("[warn] Dataset too large; load may be slow or freeze.")
        self._run_command({"action": "special_load_marker_data", **base_cmd})
        self._run_command({"action": "special_show_mask", **base_cmd})
        self._run_command({"action": "special_show_density", **base_cmd})


class AIMinOMainDock(QtWidgets.QWidget):
    """Main AIMinO dock with tabbed interface for Chat and Data Import."""

    def __init__(self, viewer: napari.Viewer) -> None:
        super().__init__()
        self.viewer = viewer
        self.agent = AgentClient()

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        # Create tabbed interface
        self.tabs = QtWidgets.QTabWidget()
        layout.addWidget(self.tabs)

        # Tab 1: Chat (primary)
        self.chat_tab = CommandDock(viewer, self.agent)
        self.tabs.addTab(self.chat_tab, "Chat")

        # Tab 2: Data Import
        self.data_tab = DataImportDock(viewer, self.agent)
        self.data_tab.dataset_changed.connect(self.chat_tab.set_current_dataset)
        self.tabs.addTab(self.data_tab, "Data")

        # Set Chat as default tab
        self.tabs.setCurrentIndex(0)

        # Style tabs
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #3a3a3a; }
            QTabBar::tab {
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #3a3a3a;
                font-weight: bold;
            }
        """)

        # Hook into layer added events to detect TIFF drag-and-drop
        # Use a flag to skip events during initialization
        self._skip_layer_events = True
        self.viewer.layers.events.inserted.connect(self._on_layer_inserted)
        # Enable event handling after a short delay (after init completes)
        QtCore.QTimer.singleShot(500, self._enable_layer_events)

    def _enable_layer_events(self) -> None:
        """Enable layer event handling after initialization."""
        self._skip_layer_events = False

    def _on_layer_inserted(self, event) -> None:
        """Detect when a new layer is added (e.g., via drag-and-drop) and offer registration."""
        # Skip events during initialization
        if getattr(self, '_skip_layer_events', True):
            return

        layer = event.value
        # Check if the layer has a source path (drag-and-drop files have this)
        source_path = None
        try:
            # Napari stores source info in layer.source.path for drag-and-drop
            source_obj = getattr(layer, 'source', None)
            if source_obj is not None:
                source_path = getattr(source_obj, 'path', None)
        except Exception:
            pass

        if source_path is None:
            # Check layer metadata as fallback
            try:
                meta = getattr(layer, 'metadata', {}) or {}
                source_path = meta.get('path') or meta.get('source_path')
            except Exception:
                pass

        if source_path is None:
            return

        source_path = str(source_path)
        # Check if it's a TIFF file
        if not source_path.lower().endswith(('.tif', '.tiff', '.ome.tif', '.ome.tiff')):
            return

        # Delay showing dialog to avoid blocking event loop
        QtCore.QTimer.singleShot(100, lambda: self._show_registration_dialog(source_path, layer.name))

    def _show_registration_dialog(self, tiff_path: str, layer_name: str) -> None:
        """Show dialog asking if user wants to register the TIFF to DataStore.

        Args:
            tiff_path: Path to the TIFF file
            layer_name: Name of the layer in Napari (used for context in messages)
        """
        from pathlib import Path
        _ = layer_name  # Reserved for future use (e.g., pre-filling dataset ID)

        tiff_file = Path(tiff_path)

        # Auto-detect corresponding h5ad file (same directory, same stem name)
        h5ad_candidates = [
            tiff_file.with_suffix('.h5ad'),
            tiff_file.parent / (tiff_file.stem.replace('.ome', '') + '.h5ad'),
        ]
        # Also check without common suffixes
        stem = tiff_file.stem
        for suffix in ['.ome', '_ome']:
            if stem.endswith(suffix):
                h5ad_candidates.append(tiff_file.parent / (stem[:-len(suffix)] + '.h5ad'))

        h5ad_path = None
        for candidate in h5ad_candidates:
            if candidate.exists():
                h5ad_path = candidate
                break

        # Create dialog
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Register Dataset to AIMinO")
        dialog.setMinimumWidth(450)

        layout = QtWidgets.QVBoxLayout(dialog)

        # Info label
        info_text = f"TIFF file detected:\n{tiff_path}\n\n"
        if h5ad_path:
            info_text += f"Matching h5ad found:\n{h5ad_path}\n\n"
        else:
            info_text += "No matching h5ad file found automatically.\n\n"
        info_text += "Would you like to register this dataset with AIMinO?"

        info_label = QtWidgets.QLabel(info_text)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # Dataset ID input
        form = QtWidgets.QFormLayout()
        dataset_id_input = QtWidgets.QLineEdit()
        dataset_id_input.setPlaceholderText(f"auto: {suggest_dataset_id(tiff_path)}")
        form.addRow("Dataset ID:", dataset_id_input)

        # h5ad path input (pre-filled if found)
        h5ad_input = QtWidgets.QLineEdit()
        if h5ad_path:
            h5ad_input.setText(str(h5ad_path))
        else:
            h5ad_input.setPlaceholderText("Select h5ad file...")
        h5ad_row = QtWidgets.QHBoxLayout()
        h5ad_row.addWidget(h5ad_input)
        h5ad_browse = QtWidgets.QPushButton("Browse")
        h5ad_browse.clicked.connect(lambda: self._browse_h5ad_for_dialog(h5ad_input))
        h5ad_row.addWidget(h5ad_browse)
        form.addRow("h5ad file:", h5ad_row)

        layout.addLayout(form)

        # Buttons
        btn_layout = QtWidgets.QHBoxLayout()
        register_btn = QtWidgets.QPushButton("Register")
        register_btn.setStyleSheet("padding: 8px; font-weight: bold; background: #4a7c59;")
        skip_btn = QtWidgets.QPushButton("Skip")
        skip_btn.setStyleSheet("padding: 8px;")

        btn_layout.addWidget(skip_btn)
        btn_layout.addWidget(register_btn)
        layout.addLayout(btn_layout)

        def on_register():
            h5ad_val = h5ad_input.text().strip()
            if not h5ad_val:
                QtWidgets.QMessageBox.warning(dialog, "Missing h5ad", "Please select an h5ad file.")
                return
            if not Path(h5ad_val).exists():
                QtWidgets.QMessageBox.warning(dialog, "File not found", f"h5ad file not found: {h5ad_val}")
                return

            dataset_id = dataset_id_input.text().strip() or None
            dialog.accept()
            self._register_dropped_dataset(tiff_path, h5ad_val, dataset_id)

        register_btn.clicked.connect(on_register)
        skip_btn.clicked.connect(dialog.reject)

        dialog.exec_()

    def _browse_h5ad_for_dialog(self, target: QtWidgets.QLineEdit) -> None:
        """Browse for h5ad file in registration dialog."""
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Select h5ad file", "", "h5ad Files (*.h5ad);;All Files (*)"
        )
        if path:
            target.setText(path)

    def _register_dropped_dataset(self, tiff_path: str, h5ad_path: str, dataset_id: Optional[str]) -> None:
        """Register a drag-and-dropped dataset to the DataStore."""
        try:
            # Detect markers from h5ad
            markers = self.data_tab._detect_markers(h5ad_path)
            metadata = {"marker_cols": markers} if markers else None

            manifest = ingest_dataset(
                tiff_path,
                h5ad_path,
                dataset_id=dataset_id,
                copy_files=False,
                metadata=metadata,
            )

            registered_id = manifest["dataset_id"]
            marker = markers[0] if markers else None

            # Update UI
            self.data_tab._append_status(f"[ok] Registered drag-and-drop dataset: {registered_id}")
            self.data_tab._refresh_datasets(select=registered_id)
            set_current_dataset(registered_id, marker)

            # Switch to Data tab and show success
            self.tabs.setCurrentIndex(1)
            self.data_tab.dataset_id_input.setText(registered_id)
            if marker:
                self.data_tab.marker_col_input.setText(marker)

            self.chat_tab.log(f"[dataset] Registered '{registered_id}' from drag-and-drop")
            self.chat_tab._refresh_dataset_label()

        except Exception as exc:
            QtWidgets.QMessageBox.critical(
                self, "Registration Failed", f"Failed to register dataset:\n{exc}"
            )


def get_dock_widget(viewer: napari.Viewer) -> AIMinOMainDock:
    """Create and return the AIMinO main dock widget.

    This function is used by the Napari plugin system to create the dock widget.
    """
    return AIMinOMainDock(viewer)


def open_chatbox(viewer: napari.Viewer = None):
    """Open the AIMinO dock widget.

    This is the entry point for the Napari plugin menu.
    Returns the widget so it can be used by Napari's widget system.
    """
    import logging
    import napari

    logger = logging.getLogger("aimino_debug")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        logger.addHandler(ch)

    logger.info(f"DEBUG: open_chatbox called. viewer={viewer}")

    if viewer is None:
        logger.warning("DEBUG: viewer is None, attempting fallback to current_viewer()")
        try:
            viewer = napari.current_viewer()
            logger.info(f"DEBUG: Retrieved current_viewer: {viewer}")
        except Exception as e:
            logger.error(f"DEBUG: Failed to get current_viewer: {e}")

    if viewer is None:
        logger.error("DEBUG: Viewer is still None. Cannot create dock widget.")
        return None

    # Return single unified dock widget
    return get_dock_widget(viewer)


def launch() -> None:
    """Launch Napari with AIMinO agent (standalone mode).

    This creates a new viewer and adds sample data.
    """
    viewer = napari.Viewer()

    img = np.random.random((256, 256))
    viewer.add_image(img, name="nuclei", visible=True)
    viewer.add_image(img * 0.1, name="cells", visible=False)

    dock = open_chatbox(viewer)
    viewer.window.add_dock_widget(dock, name="AIMinO", area="right")
    napari.run()


if __name__ == "__main__":
    launch()
