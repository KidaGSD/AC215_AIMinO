"""Pydantic command models shared between Napari executors and agents."""

from __future__ import annotations

from typing import Annotated, Literal, Optional, Tuple, Union

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


class CmdFitToView(BaseModel):
    action: Literal["fit_to_view"]
    margin: Optional[Float] = Field(default=0.05, ge=0.0, le=1.0)


class CmdResetView(BaseModel):
    action: Literal["reset_view"]
    margin: Optional[Float] = Field(default=0.05, ge=0.0, le=1.0)
    reset_camera_angle: Optional[bool] = True


class CmdScreenshot(BaseModel):
    action: Literal["screenshot"]
    path: Optional[str] = None
    size: Optional[Tuple[int, int]] = None
    scale: Optional[Float] = None
    canvas_only: Optional[bool] = True
    flash: Optional[bool] = False


class CmdExportFigure(BaseModel):
    action: Literal["export_figure"]
    path: str
    size: Optional[Tuple[int, int]] = None
    scale: Optional[Float] = None
    dpi: Optional[Float] = None
    canvas_only: Optional[bool] = True


class CmdExportRois(BaseModel):
    action: Literal["export_rois"]
    path: str
    scale: Optional[Float] = None
    canvas_only: Optional[bool] = True


class CmdOpenFile(BaseModel):
    action: Literal["open"]
    path: Union[str, list[str]]
    stack: Optional[bool] = False
    plugin: Optional[str] = "napari"
    layer_type: Optional[Literal["graph", "image", "labels", "points", "shapes", "surface", "tracks", "vectors"]] = None
    kwargs: Optional[dict] = None


class CmdOpenSample(BaseModel):
    action: Literal["open_sample"]
    plugin: str
    sample: str
    reader_plugin: Optional[str] = None
    kwargs: Optional[dict] = None


class CmdCloseViewer(BaseModel):
    action: Literal["close"]


class CmdShowViewer(BaseModel):
    action: Literal["show"]
    block: Optional[bool] = False


class CmdBindKey(BaseModel):
    action: Literal["bind_key"]
    key_bind: str
    func: Optional[str] = None
    overwrite: Optional[bool] = False


class CmdUpdateConsole(BaseModel):
    action: Literal["update_console"]
    variables: Union[dict, str, list[str]]


class CmdCameraCenter(BaseModel):
    action: Literal["camera_center"]
    center: Annotated[list[Float], Field(min_length=2, max_length=3)]


class CmdCameraZoom(BaseModel):
    action: Literal["camera_zoom"]
    zoom: Float


class CmdCameraAngles(BaseModel):
    action: Literal["camera_angles"]
    angles: Annotated[list[Float], Field(min_length=3, max_length=3)]


class CmdCameraPerspective(BaseModel):
    action: Literal["camera_perspective"]
    perspective: Float


class CmdCameraMousePan(BaseModel):
    action: Literal["camera_mouse_pan"]
    enabled: bool


class CmdCameraMouseZoom(BaseModel):
    action: Literal["camera_mouse_zoom"]
    enabled: bool


class CmdCameraReset(BaseModel):
    action: Literal["camera_reset"]


class CmdCameraSetViewDirection(BaseModel):
    action: Literal["camera_set_view_direction"]
    view_direction: Annotated[list[Float], Field(min_length=3, max_length=3)]
    up_direction: Optional[Annotated[list[Float], Field(min_length=3, max_length=3)]] = None


class CmdCameraUpdate(BaseModel):
    action: Literal["camera_update"]
    values: dict


class CmdDimsPoint(BaseModel):
    action: Literal["dims_point"]
    axis: Union[int, list[int]]
    value: Union[Float, list[Float]]


class CmdDimsRange(BaseModel):
    action: Literal["dims_range"]
    axis: Union[int, list[int]]
    range: Union[list[Float], list[list[Float]]]


class CmdDimsSetAxisLabel(BaseModel):
    action: Literal["dims_set_axis_label"]
    axis: Union[int, list[int]]
    label: Union[str, list[str]]


class CmdDimsSetPoint(BaseModel):
    action: Literal["dims_set_point"]
    axis: Union[int, list[int]]
    value: Union[Float, list[Float]]


class CmdDimsSetRange(BaseModel):
    action: Literal["dims_set_range"]
    axis: Union[int, list[int]]
    range: Union[list[Float], list[list[Float]]]


class CmdDimsOrder(BaseModel):
    action: Literal["dims_order"]
    order: list[int]


class CmdDimsAxisLabels(BaseModel):
    action: Literal["dims_axis_labels"]
    labels: list[str]


class CmdDimsNdisplay(BaseModel):
    action: Literal["dims_ndisplay"]
    ndisplay: Literal[2, 3]


class CmdDimsReset(BaseModel):
    action: Literal["dims_reset"]


class CmdDimsRoll(BaseModel):
    action: Literal["dims_roll"]


class CmdDimsTranspose(BaseModel):
    action: Literal["dims_transpose"]


class CmdDimsUpdate(BaseModel):
    action: Literal["dims_update"]
    values: dict


class CmdViewerModelTitle(BaseModel):
    action: Literal["viewer_model_title"]
    title: str


class CmdViewerModelTheme(BaseModel):
    action: Literal["viewer_model_theme"]
    theme: str


class CmdViewerModelHelp(BaseModel):
    action: Literal["viewer_model_help"]
    help: str


class CmdViewerModelReset(BaseModel):
    action: Literal["viewer_model_reset"]


class CmdViewerModelUpdate(BaseModel):
    action: Literal["viewer_model_update"]
    values: dict
    recurse: Optional[bool] = True


class CmdViewerModelUpdateStatusFromCursor(BaseModel):
    action: Literal["viewer_model_update_status_from_cursor"]


class CmdViewerModelAddLayer(BaseModel):
    action: Literal["viewer_model_add_layer"]
    layer: Optional[dict] = None


class CmdViewerModelAddImage(BaseModel):
    action: Literal["viewer_model_add_image"]
    data: Optional[Union[list, dict]] = None  # Can be array-like or dict
    kwargs: Optional[dict] = None


class CmdViewerModelAddLabels(BaseModel):
    action: Literal["viewer_model_add_labels"]
    data: Optional[Union[list, dict]] = None
    kwargs: Optional[dict] = None


class CmdViewerModelAddPoints(BaseModel):
    action: Literal["viewer_model_add_points"]
    data: Optional[Union[list, dict]] = None
    kwargs: Optional[dict] = None


class CmdViewerModelAddShapes(BaseModel):
    action: Literal["viewer_model_add_shapes"]
    data: Optional[Union[list, dict]] = None
    kwargs: Optional[dict] = None


class CmdViewerModelAddSurface(BaseModel):
    action: Literal["viewer_model_add_surface"]
    data: Optional[Union[list, dict]] = None
    kwargs: Optional[dict] = None


class CmdViewerModelAddTracks(BaseModel):
    action: Literal["viewer_model_add_tracks"]
    data: Optional[Union[list, dict]] = None
    kwargs: Optional[dict] = None


class CmdViewerModelAddVectors(BaseModel):
    action: Literal["viewer_model_add_vectors"]
    data: Optional[Union[list, dict]] = None
    kwargs: Optional[dict] = None


class CmdLayerListAppend(BaseModel):
    action: Literal["layer_list_append"]
    layer_name: str


class CmdLayerListClear(BaseModel):
    action: Literal["layer_list_clear"]


class CmdLayerListExtend(BaseModel):
    action: Literal["layer_list_extend"]
    layer_names: list[str]


class CmdLayerListInsert(BaseModel):
    action: Literal["layer_list_insert"]
    index: int
    layer_name: str


class CmdLayerListRemove(BaseModel):
    action: Literal["layer_list_remove"]
    layer_name: str


class CmdLayerListPop(BaseModel):
    action: Literal["layer_list_pop"]
    index: Optional[int] = None


class CmdLayerListMove(BaseModel):
    action: Literal["layer_list_move"]
    src_index: int
    dest_index: Optional[int] = 0


class CmdLayerListMoveMultiple(BaseModel):
    action: Literal["layer_list_move_multiple"]
    sources: list[Union[int, list[int]]]  # Can be list of ints or slices
    dest_index: Optional[int] = 0


class CmdLayerListRemoveSelected(BaseModel):
    action: Literal["layer_list_remove_selected"]


class CmdLayerListReverse(BaseModel):
    action: Literal["layer_list_reverse"]


class CmdLayerListSave(BaseModel):
    action: Literal["layer_list_save"]
    path: str
    selected: Optional[bool] = False
    plugin: Optional[str] = None


class CmdLayerListLinkLayers(BaseModel):
    action: Literal["layer_list_link_layers"]
    layer_names: Optional[list[str]] = None
    attributes: Optional[list[str]] = None


class CmdLayerListUnlinkLayers(BaseModel):
    action: Literal["layer_list_unlink_layers"]
    layer_names: Optional[list[str]] = None
    attributes: Optional[list[str]] = None


class CmdLayerListSelectAll(BaseModel):
    action: Literal["layer_list_select_all"]


class CmdLayerListSelectNext(BaseModel):
    action: Literal["layer_list_select_next"]
    step: Optional[int] = 1
    shift: Optional[bool] = False


class CmdLayerListSelectPrevious(BaseModel):
    action: Literal["layer_list_select_previous"]
    shift: Optional[bool] = False


class CmdLayerListToggleSelectedVisibility(BaseModel):
    action: Literal["layer_list_toggle_selected_visibility"]


class CmdLayerListGetExtent(BaseModel):
    action: Literal["layer_list_get_extent"]
    layer_names: Optional[list[str]] = None


class CmdLayerListIndex(BaseModel):
    action: Literal["layer_list_index"]
    layer_name: str
    start: Optional[int] = 0
    stop: Optional[int] = None


class CmdLayerSelectionAdd(BaseModel):
    action: Literal["layer_selection_add"]
    layer_names: list[str]


class CmdLayerSelectionRemove(BaseModel):
    action: Literal["layer_selection_remove"]
    layer_names: list[str]


class CmdLayerSelectionToggle(BaseModel):
    action: Literal["layer_selection_toggle"]
    layer_names: list[str]


class CmdLayerSelectionClear(BaseModel):
    action: Literal["layer_selection_clear"]


class CmdLayerSelectionSelectOnly(BaseModel):
    action: Literal["layer_selection_select_only"]
    layer_names: list[str]


class CmdLayerSelectionSetActive(BaseModel):
    action: Literal["layer_selection_set_active"]
    layer_name: str


class CmdLayerSelectionDiscard(BaseModel):
    action: Literal["layer_selection_discard"]
    layer_names: list[str]


class CmdLayerSelectionVisibility(BaseModel):
    action: Literal["layer_selection_visibility"]
    visible: bool


class CmdImageContrastLimits(BaseModel):
    action: Literal["image_contrast_limits"]
    layer_name: str
    limits: Annotated[list[Float], Field(min_length=2, max_length=2)]


class CmdImageGamma(BaseModel):
    action: Literal["image_gamma"]
    layer_name: str
    gamma: Float


class CmdImageColormap(BaseModel):
    action: Literal["image_colormap"]
    layer_name: str
    colormap: str


class CmdImageInterpolation(BaseModel):
    action: Literal["image_interpolation"]
    layer_name: str
    interpolation: str


class CmdImageRendering(BaseModel):
    action: Literal["image_rendering"]
    layer_name: str
    rendering: str


class CmdImageIsoThreshold(BaseModel):
    action: Literal["image_iso_threshold"]
    layer_name: str
    threshold: Float


class CmdImageAttenuation(BaseModel):
    action: Literal["image_attenuation"]
    layer_name: str
    attenuation: Float


class CmdPointsSize(BaseModel):
    action: Literal["points_size"]
    layer_name: str
    size: Union[Float, list[Float]]


class CmdPointsSymbol(BaseModel):
    action: Literal["points_symbol"]
    layer_name: str
    symbol: Union[str, list[str]]


class CmdPointsFaceColor(BaseModel):
    action: Literal["points_face_color"]
    layer_name: str
    color: Union[str, list[float], list[list[float]]]


class CmdPointsBorderColor(BaseModel):
    action: Literal["points_border_color"]
    layer_name: str
    color: Union[str, list[float], list[list[float]]]


class CmdPointsBorderWidth(BaseModel):
    action: Literal["points_border_width"]
    layer_name: str
    width: Union[Float, list[Float]]


class CmdPointsOutOfSliceDisplay(BaseModel):
    action: Literal["points_out_of_slice_display"]
    layer_name: str
    display: bool


class CmdPointsShading(BaseModel):
    action: Literal["points_shading"]
    layer_name: str
    shading: str


class CmdPointsAntialiasing(BaseModel):
    action: Literal["points_antialiasing"]
    layer_name: str
    antialiasing: Float


class CmdPointsCanvasSizeLimits(BaseModel):
    action: Literal["points_canvas_size_limits"]
    layer_name: str
    limits: Annotated[list[Float], Field(min_length=2, max_length=2)]


class CmdShapesEdgeWidth(BaseModel):
    action: Literal["shapes_edge_width"]
    layer_name: str
    width: Union[Float, list[Float]]


class CmdShapesEdgeColor(BaseModel):
    action: Literal["shapes_edge_color"]
    layer_name: str
    color: Union[str, list[float], list[list[float]]]


class CmdShapesFaceColor(BaseModel):
    action: Literal["shapes_face_color"]
    layer_name: str
    color: Union[str, list[float], list[list[float]]]


class CmdShapesZIndex(BaseModel):
    action: Literal["shapes_z_index"]
    layer_name: str
    index: Union[int, list[int]]


class CmdShapesText(BaseModel):
    action: Literal["shapes_text"]
    layer_name: str
    text: Union[str, dict]


class CmdShapesCurrentEdgeWidth(BaseModel):
    action: Literal["shapes_current_edge_width"]
    layer_name: str
    width: Float


class CmdShapesCurrentEdgeColor(BaseModel):
    action: Literal["shapes_current_edge_color"]
    layer_name: str
    color: Union[str, list[float]]


class CmdShapesCurrentFaceColor(BaseModel):
    action: Literal["shapes_current_face_color"]
    layer_name: str
    color: Union[str, list[float]]


class CmdLabelsContour(BaseModel):
    action: Literal["labels_contour"]
    layer_name: str
    contour: bool


class CmdLabelsNEditDimensions(BaseModel):
    action: Literal["labels_n_edit_dimensions"]
    layer_name: str
    n_edit_dimensions: int


class CmdLabelsBrushSize(BaseModel):
    action: Literal["labels_brush_size"]
    layer_name: str
    size: Float


class CmdLabelsColormap(BaseModel):
    action: Literal["labels_colormap"]
    layer_name: str
    colormap: str


class CmdLabelsContiguous(BaseModel):
    action: Literal["labels_contiguous"]
    layer_name: str
    contiguous: bool


class CmdLabelsRendering(BaseModel):
    action: Literal["labels_rendering"]
    layer_name: str
    rendering: str


class CmdLabelsIsoGradientMode(BaseModel):
    action: Literal["labels_iso_gradient_mode"]
    layer_name: str
    mode: str


class CmdLabelsSelectedLabel(BaseModel):
    action: Literal["labels_selected_label"]
    layer_name: str
    label: int


class CmdLabelsMode(BaseModel):
    action: Literal["labels_mode"]
    layer_name: str
    mode: str


# Special analysis commands for biological image processing
class CmdDataIngest(BaseModel):
    action: Literal["data_ingest"]
    dataset_id: str
    image_path: str
    h5ad_path: str
    copy_files: bool = False
    marker_col: Optional[str] = None


class CmdLoadMarkerData(BaseModel):
    action: Literal["special_load_marker_data"]
    marker_col: str
    dataset_id: Optional[str] = None
    image_path: Optional[str] = None
    h5ad_path: Optional[str] = None
    output_root: Optional[str] = None
    force_recompute: bool = False


class CmdShowMask(BaseModel):
    action: Literal["special_show_mask"]
    marker_col: str
    color: Optional[str] = None


class CmdShowDensity(BaseModel):
    action: Literal["special_show_density"]
    marker_col: str


class CmdUpdateDensity(BaseModel):
    action: Literal["special_update_density"]
    marker_col: str
    dataset_id: Optional[str] = None
    image_path: Optional[str] = None
    h5ad_path: Optional[str] = None
    output_root: Optional[str] = None
    sigma: Optional[Float] = None
    colormap: Optional[str] = None
    force: bool = False


class CmdComputeNeighborhood(BaseModel):
    action: Literal["special_compute_neighborhood"]
    marker_col: str
    dataset_id: Optional[str] = None
    image_path: Optional[str] = None
    h5ad_path: Optional[str] = None
    output_root: Optional[str] = None
    radius: Optional[Float] = None
    force_recompute: bool = False


# Context management commands
class CmdSetDataset(BaseModel):
    action: Literal["set_dataset"]
    dataset_id: str


class CmdSetMarker(BaseModel):
    action: Literal["set_marker"]
    marker_col: str


class CmdListDatasets(BaseModel):
    action: Literal["list_datasets"]


class CmdGetDatasetInfo(BaseModel):
    action: Literal["get_dataset_info"]
    dataset_id: Optional[str] = None


class CmdClearCache(BaseModel):
    action: Literal["clear_processed_cache"]
    dataset_id: Optional[str] = None
    delete_raw: bool = False


BaseNapariCommand = Union[
    CmdLayerVisibility,
    CmdPanelToggle,
    CmdZoomBox,
    CmdCenterOn,
    CmdSetZoom,
    CmdFitToLayer,
    CmdListLayers,
    CmdHelp,
    CmdFitToView,
    CmdResetView,
    CmdScreenshot,
    CmdExportFigure,
    CmdExportRois,
    CmdOpenFile,
    CmdOpenSample,
    CmdCloseViewer,
    CmdShowViewer,
    CmdBindKey,
    CmdUpdateConsole,
    CmdCameraCenter,
    CmdCameraZoom,
    CmdCameraAngles,
    CmdCameraPerspective,
    CmdCameraMousePan,
    CmdCameraMouseZoom,
    CmdCameraReset,
    CmdCameraSetViewDirection,
    CmdCameraUpdate,
    CmdDimsPoint,
    CmdDimsRange,
    CmdDimsSetAxisLabel,
    CmdDimsSetPoint,
    CmdDimsSetRange,
    CmdDimsOrder,
    CmdDimsAxisLabels,
    CmdDimsNdisplay,
    CmdDimsReset,
    CmdDimsRoll,
    CmdDimsTranspose,
    CmdDimsUpdate,
    CmdViewerModelTitle,
    CmdViewerModelTheme,
    CmdViewerModelHelp,
    CmdViewerModelReset,
    CmdViewerModelUpdate,
    CmdViewerModelUpdateStatusFromCursor,
    CmdViewerModelAddLayer,
    CmdViewerModelAddImage,
    CmdViewerModelAddLabels,
    CmdViewerModelAddPoints,
    CmdViewerModelAddShapes,
    CmdViewerModelAddSurface,
    CmdViewerModelAddTracks,
    CmdViewerModelAddVectors,
    CmdLayerListAppend,
    CmdLayerListClear,
    CmdLayerListExtend,
    CmdLayerListInsert,
    CmdLayerListRemove,
    CmdLayerListPop,
    CmdLayerListMove,
    CmdLayerListMoveMultiple,
    CmdLayerListRemoveSelected,
    CmdLayerListReverse,
    CmdLayerListSave,
    CmdLayerListLinkLayers,
    CmdLayerListUnlinkLayers,
    CmdLayerListSelectAll,
    CmdLayerListSelectNext,
    CmdLayerListSelectPrevious,
    CmdLayerListToggleSelectedVisibility,
    CmdLayerListGetExtent,
    CmdLayerListIndex,
    CmdLayerSelectionAdd,
    CmdLayerSelectionRemove,
    CmdLayerSelectionToggle,
    CmdLayerSelectionClear,
    CmdLayerSelectionSelectOnly,
    CmdLayerSelectionSetActive,
    CmdLayerSelectionDiscard,
    CmdLayerSelectionVisibility,
    CmdImageContrastLimits,
    CmdImageGamma,
    CmdImageColormap,
    CmdImageInterpolation,
    CmdImageRendering,
    CmdImageIsoThreshold,
    CmdImageAttenuation,
    CmdPointsSize,
    CmdPointsSymbol,
    CmdPointsFaceColor,
    CmdPointsBorderColor,
    CmdPointsBorderWidth,
    CmdPointsOutOfSliceDisplay,
    CmdPointsShading,
    CmdPointsAntialiasing,
    CmdPointsCanvasSizeLimits,
    CmdShapesEdgeWidth,
    CmdShapesEdgeColor,
    CmdShapesFaceColor,
    CmdShapesZIndex,
    CmdShapesText,
    CmdShapesCurrentEdgeWidth,
    CmdShapesCurrentEdgeColor,
    CmdShapesCurrentFaceColor,
    CmdLabelsContour,
    CmdLabelsNEditDimensions,
    CmdLabelsBrushSize,
    CmdLabelsColormap,
    CmdLabelsContiguous,
    CmdLabelsRendering,
    CmdLabelsIsoGradientMode,
    CmdLabelsSelectedLabel,
    CmdLabelsMode,
    CmdDataIngest,
    CmdLoadMarkerData,
    CmdShowMask,
    CmdShowDensity,
    CmdUpdateDensity,
    CmdComputeNeighborhood,
    CmdSetDataset,
    CmdSetMarker,
    CmdListDatasets,
    CmdGetDatasetInfo,
    CmdClearCache,
]

BaseCommandAdapter = TypeAdapter(BaseNapariCommand)

__all__ = [
    "BaseCommandAdapter",
    "BaseNapariCommand",
    "CmdBindKey",
    "CmdCameraAngles",
    "CmdCameraCenter",
    "CmdCameraMousePan",
    "CmdCameraMouseZoom",
    "CmdCameraPerspective",
    "CmdCameraReset",
    "CmdCameraSetViewDirection",
    "CmdCameraUpdate",
    "CmdCameraZoom",
    "CmdCenterOn",
    "CmdDimsAxisLabels",
    "CmdDimsNdisplay",
    "CmdDimsOrder",
    "CmdDimsPoint",
    "CmdDimsRange",
    "CmdDimsReset",
    "CmdDimsRoll",
    "CmdDimsSetAxisLabel",
    "CmdDimsSetPoint",
    "CmdDimsSetRange",
    "CmdDimsTranspose",
    "CmdDimsUpdate",
    "CmdCloseViewer",
    "CmdExportFigure",
    "CmdExportRois",
    "CmdFitToLayer",
    "CmdFitToView",
    "CmdHelp",
    "CmdLayerListAppend",
    "CmdLayerListClear",
    "CmdLayerListExtend",
    "CmdLayerListGetExtent",
    "CmdLayerListIndex",
    "CmdLayerListInsert",
    "CmdLayerListLinkLayers",
    "CmdLayerListMove",
    "CmdLayerListMoveMultiple",
    "CmdLayerListPop",
    "CmdLayerListRemove",
    "CmdLayerListRemoveSelected",
    "CmdLayerListReverse",
    "CmdLayerListSave",
    "CmdLayerListSelectAll",
    "CmdLayerListSelectNext",
    "CmdLayerListSelectPrevious",
    "CmdLayerListToggleSelectedVisibility",
    "CmdLayerListUnlinkLayers",
    "CmdLayerSelectionAdd",
    "CmdLayerSelectionClear",
    "CmdLayerSelectionDiscard",
    "CmdLayerSelectionRemove",
    "CmdLayerSelectionSelectOnly",
    "CmdLayerSelectionSetActive",
    "CmdLayerSelectionToggle",
    "CmdLayerSelectionVisibility",
    "CmdLayerVisibility",
    "CmdListLayers",
    "CmdOpenFile",
    "CmdOpenSample",
    "CmdPanelToggle",
    "CmdResetView",
    "CmdScreenshot",
    "CmdSetZoom",
    "CmdShowViewer",
    "CmdUpdateConsole",
    "CmdViewerModelAddImage",
    "CmdViewerModelAddLabels",
    "CmdViewerModelAddLayer",
    "CmdViewerModelAddPoints",
    "CmdViewerModelAddShapes",
    "CmdViewerModelAddSurface",
    "CmdViewerModelAddTracks",
    "CmdViewerModelAddVectors",
    "CmdViewerModelHelp",
    "CmdViewerModelReset",
    "CmdViewerModelTheme",
    "CmdViewerModelTitle",
    "CmdViewerModelUpdate",
    "CmdViewerModelUpdateStatusFromCursor",
    "CmdZoomBox",
    "CmdImageContrastLimits",
    "CmdImageGamma",
    "CmdImageColormap",
    "CmdImageInterpolation",
    "CmdImageRendering",
    "CmdImageIsoThreshold",
    "CmdImageAttenuation",
    "CmdPointsSize",
    "CmdPointsSymbol",
    "CmdPointsFaceColor",
    "CmdPointsBorderColor",
    "CmdPointsBorderWidth",
    "CmdPointsOutOfSliceDisplay",
    "CmdPointsShading",
    "CmdPointsAntialiasing",
    "CmdPointsAntialiasing",
    "CmdPointsCanvasSizeLimits",
    "CmdShapesEdgeWidth",
    "CmdShapesEdgeColor",
    "CmdShapesFaceColor",
    "CmdShapesZIndex",
    "CmdShapesText",
    "CmdShapesCurrentEdgeWidth",
    "CmdShapesCurrentEdgeColor",
    "CmdShapesCurrentFaceColor",
    "CmdLabelsContour",
    "CmdLabelsNEditDimensions",
    "CmdLabelsBrushSize",
    "CmdLabelsColormap",
    "CmdLabelsContiguous",
    "CmdLabelsRendering",
    "CmdLabelsIsoGradientMode",
    "CmdLabelsSelectedLabel",
    "CmdLabelsMode",
    "CmdDataIngest",
    "CmdLoadMarkerData",
    "CmdShowMask",
    "CmdShowDensity",
    "CmdUpdateDensity",
    "CmdComputeNeighborhood",
    "CmdSetDataset",
    "CmdSetMarker",
    "CmdListDatasets",
    "CmdGetDatasetInfo",
    "CmdClearCache",
]
