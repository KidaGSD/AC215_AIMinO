from aimino_frontend.aimino_core import command_models as cm


def test_dims_ndisplay_adapter_accepts():
    payload = {"action": "dims_ndisplay", "ndisplay": 3}
    cmd = cm.BaseCommandAdapter.validate_python(payload)
    assert cmd.action == "dims_ndisplay"
    assert cmd.ndisplay == 3


def test_fit_to_layer_adapter_accepts():
    payload = {"action": "fit_to_layer", "name": "nuclei"}
    cmd = cm.BaseCommandAdapter.validate_python(payload)
    assert cmd.action == "fit_to_layer"
    assert cmd.name == "nuclei"
