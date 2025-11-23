"""Minimal Napari launcher wired to AIMinO agent stack."""

from __future__ import annotations

from typing import List, Optional

import napari
import numpy as np
from pathlib import Path
from qtpy import QtWidgets

from aimino_core import CommandExecutionError, execute_command
from napari_app.client_agent import AgentClient


SESSION_FILE = Path.home() / ".aimino_last_session"


def load_last_session_id() -> Optional[str]:
    try:
        if not SESSION_FILE.exists():
            return None
        session_id = SESSION_FILE.read_text(encoding="utf-8").strip()
        return session_id or None
    except OSError:
        return None


def save_last_session_id(session_id: str) -> None:
    try:
        SESSION_FILE.write_text(session_id, encoding="utf-8")
    except OSError:
        # Persistence failures should not break the UI.
        pass


class CommandDock(QtWidgets.QWidget):
    def __init__(self, viewer: napari.Viewer, agent: AgentClient) -> None:
        super().__init__()
        self.viewer = viewer
        self.agent = agent

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

        self.run_btn.clicked.connect(self.on_submit)
        self.input.returnPressed.connect(self.on_submit)

    def log(self, text: str) -> None:
        self.output.appendPlainText(text)

    def on_submit(self) -> None:
        user_text = self.input.text().strip()
        if not user_text:
            return
        self.input.clear()
        self.log(f"> {user_text}")
        try:
            commands = self.agent.invoke(user_text)
            if getattr(self.agent, "session_id", None):
                save_last_session_id(self.agent.session_id)  # type: ignore[arg-type]
        except Exception as exc:  # pragma: no cover - UI guard
            self.log(f"[agent error] {exc}")
            return

        for cmd in commands:
            try:
                msg = execute_command(cmd, self.viewer)
                self.log(f"command: {cmd} -> {msg}")
            except CommandExecutionError as exc:
                self.log(f"[execution error] {exc}")


def launch() -> None:
    viewer = napari.Viewer()

    img = np.random.random((256, 256))
    viewer.add_image(img, name="nuclei", visible=True)
    viewer.add_image(img * 0.1, name="cells", visible=False)

    # Optionally resume previous session for conversational memory.
    last_session_id = load_last_session_id()
    agent: AgentClient
    if last_session_id:
        choice = QtWidgets.QMessageBox.question(
            None,
            "AIMinO Session",
            "Previous session detected. Continue?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.Yes,
        )
        if choice == QtWidgets.QMessageBox.Yes:
            agent = AgentClient(session_id=last_session_id)
        else:
            agent = AgentClient()
    else:
        agent = AgentClient()
    dock = CommandDock(viewer, agent)
    viewer.window.add_dock_widget(dock, name="AIMinO Agent", area="right")

    napari.run()


if __name__ == "__main__":
    launch()
