"""Pydantic command models shared between Napari executors and agents."""

from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field, TypeAdapter, confloat

Float = confloat(strict=False)


class CmdLayerVisibility(BaseModel):
    action: Literal["layer_visibility"]
    name: str
    op: Literal["show", "hide", "toggle"]


class CmdPanelToggle(BaseModel):
    action: Literal["panel_toggle"]
    name: str
    op: Literal["open", "close"]


class CmdZoomBox(BaseModel):
    action: Literal["zoom_box"]
    box: Annotated[list[Float], Field(min_length=4, max_length=4)]


class CmdCenterOn(BaseModel):
    action: Literal["center_on"]
    point: Annotated[list[Float], Field(min_length=2, max_length=2)]


class CmdSetZoom(BaseModel):
    action: Literal["set_zoom"]
    zoom: Float


class CmdFitToLayer(BaseModel):
    action: Literal["fit_to_layer"]
    name: str


class CmdListLayers(BaseModel):
    action: Literal["list_layers"]


class CmdHelp(BaseModel):
    action: Literal["help"]


BaseNapariCommand = Union[
    CmdLayerVisibility,
    CmdPanelToggle,
    CmdZoomBox,
    CmdCenterOn,
    CmdSetZoom,
    CmdFitToLayer,
    CmdListLayers,
    CmdHelp,
]

BaseCommandAdapter = TypeAdapter(BaseNapariCommand)

__all__ = [
    "BaseCommandAdapter",
    "BaseNapariCommand",
    "CmdCenterOn",
    "CmdFitToLayer",
    "CmdHelp",
    "CmdLayerVisibility",
    "CmdListLayers",
    "CmdPanelToggle",
    "CmdSetZoom",
    "CmdZoomBox",
]
