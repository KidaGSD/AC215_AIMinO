"""Minimal Napari launcher wired to AIMinO agent stack."""



from typing import List
import asyncio

import napari
import numpy as np
from qtpy import QtWidgets, QtCore

from aimino_frontend.aimino_core import CommandExecutionError, execute_command
from .client_agent import AgentClient, load_last_session_id


class CommandDock(QtWidgets.QWidget):
    def __init__(self, viewer: napari.Viewer, agent: AgentClient) -> None:
        super().__init__()
        self.viewer = viewer
        self.agent = agent
        self._last_session_id: str | None = load_last_session_id()

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        self.input = QtWidgets.QLineEdit()
        self.input.setPlaceholderText("e.g. show nuclei layer, center on 200,300")
        layout.addWidget(self.input)

        self.run_btn = QtWidgets.QPushButton("Run Agent")
        layout.addWidget(self.run_btn)

        self.output = QtWidgets.QPlainTextEdit()
        self.output.setReadOnly(True)
        layout.addWidget(self.output)

        # Optional checkbox to resume last conversation if available
        self.restore_checkbox = QtWidgets.QCheckBox("Resume last conversation")
        if not self._last_session_id:
            self.restore_checkbox.setEnabled(False)
        layout.addWidget(self.restore_checkbox)

        self.run_btn.clicked.connect(self.on_submit)
        self.input.returnPressed.connect(self.on_submit)
        self.restore_checkbox.stateChanged.connect(self.on_restore_toggled)

    def log(self, text: str) -> None:
        self.output.appendPlainText(text)

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
        try:
            commands = asyncio.run(self.agent.invoke(user_text))
        except Exception as exc:  # pragma: no cover - UI guard
            self.log(f"[agent error] {exc}")
            return

        for cmd in commands:
            try:
                msg = execute_command(cmd, self.viewer)
                self.log(f"command: {cmd} -> {msg}")
            except CommandExecutionError as exc:
                self.log(f"[execution error] {exc}")


def get_dock_widget(viewer: napari.Viewer) -> CommandDock:
    """Create and return the AIMinO command dock widget.
    
    This function is used by the Napari plugin system to create the dock widget.
    """
    agent = AgentClient()
    dock = CommandDock(viewer, agent)
    return dock


def open_chatbox(viewer: napari.Viewer = None):
    """Open the AIMinO ChatBox dock widget.
    
    This is the entry point for the Napari plugin menu.
    Returns the widget so it can be used by Napari's widget system.
    """
    import logging
    import napari
    
    logger = logging.getLogger("aimino_debug")
    logger.setLevel(logging.INFO)
    # Add handler if not present
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

    dock = get_dock_widget(viewer)
    return dock


def launch() -> None:
    """Launch Napari with AIMinO agent (standalone mode).
    
    This creates a new viewer and adds sample data.
    """
    viewer = napari.Viewer()

    img = np.random.random((256, 256))
    viewer.add_image(img, name="nuclei", visible=True)
    viewer.add_image(img * 0.1, name="cells", visible=False)

    dock = open_chatbox(viewer)
    viewer.window.add_dock_widget(dock, name="AIMinO ChatBox", area="right")
    napari.run()


if __name__ == "__main__":
    launch()
