# napari_llm_mask.py — SOX10 mask + density + boundary + AI intents + GUI + cached outputs
# - Only the TIFF shows at launch; other layers are created hidden
# - Ollama natural commands supported
# - GUI: tweak mask color, density colormap/sigma, zoom to densest

import os, re, json, requests
from typing import Annotated, Literal
import numpy as np
from tifffile import imread, imwrite, TiffFile
import anndata as ad
import napari
from qtpy import QtWidgets
from qtpy.QtCore import Qt
from qtpy.QtGui import QColor
from pydantic import BaseModel, Field, confloat, ValidationError, TypeAdapter
from skimage import measure
from skimage.draw import polygon
from skimage.measure import approximate_polygon
from scipy.ndimage import gaussian_filter

# ======================
# CONFIG
# ======================
IMAGE_PATH  = '/Volumes/HITS/lsp-analysis/cycif-production/143-buchbinder-stable-melanoma/p143_ORION/LSP16767/registration/LSP16767.ome.tif'
H5AD_PATH   = 'LSP16767_10232025.h5ad'
MARKER_COL  = 'SOX10_positive'

# outputs: ~/Desktop/AC215/Milestone2/processed/<image-basename>/
OUTPUT_ROOT = os.path.expanduser('~/Desktop/AC215/Milestone2/processed')

# Geometry / rasterization
DOWNSAMPLE = 1
ELLIPSE_VERTS = 36
RASTER_CHUNK  = 5000
ORIENTATION_IS_DEGREES = False

# ======================
# Command schema (with first-class intents)
# ======================
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

class CmdShowMask(BaseModel):
    action: Literal["special_show_mask"]
    color: str | None = None

class CmdShowDensity(BaseModel):
    action: Literal["special_show_density"]

class CmdUpdateDensity(BaseModel):
    action: Literal["special_update_density"]
    sigma: float | None = None
    color: str | None = None
    force: bool = False

class CmdUnknown(BaseModel):
    action: Literal["unknown"]
    text: str

Allowed = (CmdLayerVisibility | CmdPanelToggle | CmdZoomBox | CmdCenterOn | CmdSetZoom |
           CmdFitToLayer | CmdListLayers | CmdHelp |
           CmdShowMask | CmdShowDensity | CmdUpdateDensity |
           CmdUnknown)
ALLOWED_ADAPTER = TypeAdapter(Allowed)

# ======================
# Helpers
# ======================
def _set_binary_labels_color(ly, rgba):
    """Recolor a 0/1 Labels layer and force napari to honor it."""
    cmap = {0: (0, 0, 0, 0), 1: tuple(map(float, rgba))}
    try:
        ly.color = cmap
    except Exception:
        ly.colors = cmap  # older napari
    try:
        ly.color_mode = 'direct'
    except Exception:
        pass
    try:
        ly.refresh()
    except Exception:
        vis = ly.visible
        ly.visible = False
        ly.visible = vis

def _parse_color(c, alpha: float | None = None):
    NAMED = {"red":(1,0,0,1),"green":(0,1,0,1),"blue":(0,0,1,1),
             "cyan":(0,1,1,1),"magenta":(1,0,1,1),"yellow":(1,1,0,1),
             "white":(1,1,1,1),"black":(0,0,0,1),"orange":(1,0.5,0,1),
             "purple":(0.5,0,0.5,1),"pink":(1,0.75,0.8,1)}
    if isinstance(c,str):
        s=c.strip().lower()
        if s in NAMED:
            r,g,b,a=NAMED[s]; 
            if alpha is not None:a=float(alpha)
            return (r,g,b,a)
        if s.startswith("#"):
            s=s.lstrip("#")
            if len(s) in (6,8):
                r=int(s[0:2],16)/255; g=int(s[2:4],16)/255; b=int(s[4:6],16)/255
                a=int(s[6:8],16)/255 if len(s)==8 else (1 if alpha is None else float(alpha))
                if alpha is not None:a=float(alpha)
                return (r,g,b,a)
    if hasattr(c,"__iter__"):
        vals=list(c)
        if len(vals)==3:r,g,b=vals;a=1 if alpha is None else float(alpha)
        elif len(vals)==4:r,g,b,a=vals
        else:raise ValueError("Color tuple must have length 3 or 4.")
        if max(r,g,b,a)>1:r,g,b,a=r/255,g/255,b/255,a/255
        return (float(r),float(g),float(b),float(a))
    raise ValueError(f"Unrecognized color: {c!r}")

def find_layer(viewer,name):
    q=name.lower().strip()
    for ly in viewer.layers:
        if ly.name.lower()==q:return ly
    candidates=[ly for ly in viewer.layers if q in ly.name.lower()]
    return candidates[0] if len(candidates)==1 else None

def _get_vispy_camera(viewer):
    qtv = getattr(viewer.window, "_qt_viewer", None) or getattr(viewer.window, "qt_viewer", None)
    if qtv is None: return None
    canvas = getattr(qtv, "canvas", None)
    if canvas is not None and hasattr(canvas, "scene"): return getattr(canvas.scene, "camera", None)
    view = getattr(qtv, "view", None)
    return getattr(view, "camera", None) if view is not None else None

def set_view_box(viewer,x1,y1,x2,y2):
    xlo,xhi = sorted([float(x1),float(x2)])
    ylo,yhi = sorted([float(y1),float(y2)])
    cam=_get_vispy_camera(viewer)
    if cam and hasattr(cam,"set_range"):
        cam.set_range(x=(xlo,xhi),y=(ylo,yhi))
    viewer.camera.center=((xlo+xhi)/2,(ylo+yhi)/2)
    return f"Zoomed to ({xlo:.1f},{ylo:.1f})–({xhi:.1f},{yhi:.1f})"

def zoom_to_dense_region(viewer, density_layer_name, zoom_margin=300):
    ly=find_layer(viewer,density_layer_name)
    if not ly:return f"[warn] Density layer '{density_layer_name}' not found."
    data=np.array(ly.data)
    if data.ndim!=2 or data.max()<=0:return "[warn] density map empty."
    y,x=np.unravel_index(np.argmax(data),data.shape)
    H,W=data.shape
    x1,x2=max(0,x-zoom_margin),min(W,x+zoom_margin)
    y1,y2=max(0,y-zoom_margin),min(H,y+zoom_margin)
    set_view_box(viewer,x1,y1,x2,y2)
    return f"Zoomed to dense region near ({x},{y})."

def _basename_noext(p: str) -> str:
    b = os.path.basename(p); return os.path.splitext(b)[0]

def _output_dir_for_image(raw_image_path: str) -> str:
    sub = _basename_noext(raw_image_path)
    outdir = os.path.join(OUTPUT_ROOT, sub)
    os.makedirs(outdir, exist_ok=True)
    return outdir

def get_output_paths(raw_image_path: str, marker_col: str, sigma: float):
    outdir = _output_dir_for_image(raw_image_path)
    base = _basename_noext(raw_image_path)
    sigma_tag = int(round(float(sigma)))
    labels_tif = os.path.join(outdir, f"{base}_rebuilt_labels.tif")
    mask_tif   = os.path.join(outdir, f"{base}_{marker_col}_mask.tif")
    dens_npy   = os.path.join(outdir, f"{base}_{marker_col}_density_sigma{sigma_tag}.npy")
    bnd_npz    = os.path.join(outdir, f"{base}_{marker_col}_density_boundary_sigma{sigma_tag}_p95.npz")
    return outdir, labels_tif, mask_tif, dens_npy, bnd_npz

def save_boundary_paths_npz(paths: list[np.ndarray], out_path: str):
    np.savez_compressed(out_path, **{f"p{i}": arr for i, arr in enumerate(paths)})

def load_boundary_paths_npz(path: str) -> list[np.ndarray]:
    if not os.path.exists(path): return []
    with np.load(path, allow_pickle=False) as z:
        keys = sorted([k for k in z.files if k.startswith("p")], key=lambda s:int(s[1:]))
        return [z[k] for k in keys]

# ======================
# Regex parser (natural phrases + density/boundary intents)
# ======================
def parse_command_regex(text:str)->Allowed:
    t=text.strip().lower()

    # mask on/off
    if re.search(r"(turn\s*off|hide).*(tumou?r|sox10).*(mask)", t):
        return CmdLayerVisibility(action="layer_visibility", op="hide", name=f"{MARKER_COL}_mask")
    if re.search(r"(turn\s*on|show).*(tumou?r|sox10).*(mask)", t):
        return CmdLayerVisibility(action="layer_visibility", op="show", name=f"{MARKER_COL}_mask")

    # density on/off (and synonyms)
    if re.search(r"(turn\s*on|show).*(sox10|tumou?r)?.*(density(\s*map)?)", t):
        return CmdLayerVisibility(action="layer_visibility", op="show", name=f"{MARKER_COL}_density")
    if re.search(r"(turn\s*off|hide).*(sox10|tumou?r)?.*(density(\s*map)?)", t):
        return CmdLayerVisibility(action="layer_visibility", op="hide", name=f"{MARKER_COL}_density")

    # boundary on/off (optional)
    if re.search(r"(turn\s*on|show).*(boundary|contour|outline)", t):
        return CmdLayerVisibility(action="layer_visibility", op="show", name=f"{MARKER_COL}_density_boundary")
    if re.search(r"(turn\s*off|hide).*(boundary|contour|outline)", t):
        return CmdLayerVisibility(action="layer_visibility", op="hide", name=f"{MARKER_COL}_density_boundary")

    # "zoom to densest/denset region"
    if re.search(r"zoom.*dense(st|t)\b", t):
        return CmdShowDensity(action="special_show_density")

    # generic "show dense region" intent
    if re.search(r"(show|display).*(dense\s*region|tumou?r\s*core|density\s*region)", t):
        return CmdShowDensity(action="special_show_density")

    # "make it yellow" / "make mask #ff00ff"
    m = re.match(r"(make(\s+the)?(\s+tumou?r)?(\s+mask)?)\s+(#[0-9a-f]{6}|\w+)$", t)
    if m:
        color = m.group(5)
        return CmdShowMask(action="special_show_mask", color=color)

    m = re.match(r"show\s+(?:the\s+)?(?:tumou?r|sox10).*(?:mask)(?:\s+color\s*=\s*([#\w]+))?$", t)
    if m:
        return CmdShowMask(action="special_show_mask", color=m.group(1) if m.group(1) else None)

    m = re.match(r"update\s+density(?:\s+sigma\s*=\s*([0-9.]+))?(?:\s+color\s*=\s*([#\w]+))?(?:\s+(force))?$", t)
    if m:
        sigma = float(m.group(1)) if m.group(1) else None
        color = m.group(2) if m.group(2) else None
        force = bool(m.group(3))
        return CmdUpdateDensity(action="special_update_density", sigma=sigma, color=color, force=force)

    m=re.match(r"(show|hide|toggle)\s+layer\s+(.+)$",t)
    if m:return CmdLayerVisibility(action="layer_visibility",op=m.group(1),name=m.group(2).strip())

    if t in {"layers","list layers"}: return CmdListLayers(action="list_layers")
    if t in {"help","?"}: return CmdHelp(action="help")
    return CmdUnknown(action="unknown",text=text)

# ======================
# LLM backend (Ollama)
# ======================
SYS_PROMPT = """You convert short natural instructions into JSON commands for a napari viewer.

Return JSON ONLY that validates one of these:
- {"action":"layer_visibility","op":"show|hide|toggle","name":"<layer name>"}
- {"action":"panel_toggle","op":"open|close","name":"<panel name>"}
- {"action":"zoom_box","box":[x1,y1,x2,y2]}
- {"action":"center_on","point":[x,y]}
- {"action":"set_zoom","zoom":1.25}
- {"action":"fit_to_layer","name":"<layer name>"}
- {"action":"list_layers"}
- {"action":"help"}
- {"action":"special_show_mask","color":"#00ffcc"}
- {"action":"special_show_density"}
- {"action":"special_update_density","sigma":250,"color":"inferno","force":false}

Examples:
- "turn on tumor SOX10 density" -> {"action":"layer_visibility","op":"show","name":"SOX10_positive_density"}
- "zoom to densest" -> {"action":"special_show_density"}
"""

def llm_ollama(text:str)->dict:
    base=os.getenv("OLLAMA_BASE_URL","http://127.0.0.1:11434").rstrip("/")
    model=os.getenv("OLLAMA_MODEL","llama3.1")
    payload={"model":model,"messages":[{"role":"system","content":SYS_PROMPT},{"role":"user","content":text}],
             "options":{"temperature":0},"stream":False}
    r=requests.post(f"{base}/api/chat",json=payload,timeout=300)
    if r.status_code==200:
        j=r.json(); content=(j.get("message",{}) or {}).get("content") or j.get("response")
        if not content: raise RuntimeError("empty response")
        return json.loads(content)
    raise RuntimeError(f"Ollama error {r.status_code}:{r.text[:120]}")

def llm_parse_command(text:str)->Allowed:
    try:
        raw=llm_ollama(text) if os.getenv("LLM_BACKEND","ollama")=="ollama" else {}
    except Exception:
        return CmdUnknown(action="unknown", text=text)
    try:
        return ALLOWED_ADAPTER.validate_python(raw)
    except ValidationError:
        return CmdHelp(action="help")

# ======================
# Execute actions
# ======================
def execute(cmd:Allowed,viewer):
    a=cmd.action

    if a=="layer_visibility":
        name = cmd.name
        color_match = re.search(r"color\s*=\s*([#\w(),.\s]+)", name)
        target_name = re.sub(r"color\s*=\s*([#\w(),.\s]+)", "", name).strip()
        msg = set_layer_visibility(viewer, target_name, cmd.op)
        if color_match:
            color_str = color_match.group(1).strip()
            ly = find_layer(viewer, target_name)
            if ly is not None:
                try:
                    from napari.layers import Labels, Image
                    if isinstance(ly, Labels):
                        rgba = _parse_color(color_str)
                        _set_binary_labels_color(ly, rgba)
                        msg += f"; recolored labels to {color_str}"
                    elif isinstance(ly, Image):
                        ly.colormap = color_str
                        msg += f"; set colormap to {color_str}"
                except Exception as e:
                    msg += f" [color error: {e}]"
        return msg

    if a=="panel_toggle":
        return toggle_panel(viewer, cmd.name, open_it=(cmd.op=="open"))
    if a=="zoom_box":
        x1,y1,x2,y2=cmd.box; return set_view_box(viewer,x1,y1,x2,y2)
    if a=="center_on":
        x,y=cmd.point; viewer.camera.center=(float(x),float(y)); return f"Centered on ({x},{y})"
    if a=="set_zoom":
        viewer.camera.zoom=float(cmd.zoom); return f"Set zoom to {float(cmd.zoom):.2f}"
    if a=="fit_to_layer":
        ly=find_layer(viewer,cmd.name)
        if not ly: return f"Layer '{cmd.name}' not found."
        (ymin,xmin),(ymax,xmax)=ly.extent.world[0][:2],ly.extent.world[1][:2]
        return set_view_box(viewer,xmin,ymin,xmax,ymax)
    if a=="list_layers":
        return "Layers: " + (", ".join([l.name for l in viewer.layers]) or "(none)")
    if a=="help":
        return ("Examples:\n"
                "- turn off the tumor mask\n- show tumor cell mask color=#00ffd0\n"
                "- turn on tumor SOX10 density\n- zoom to densest\n"
                "- update density sigma=250 color=inferno\n")

    if a=="special_show_mask":
        ly=find_layer(viewer,f"{MARKER_COL}_mask")
        if not ly: return "[warn] Mask layer not found."
        ly.visible=True; viewer.layers.selection.active=ly
        if getattr(cmd,"color",None):
            try:
                rgba=_parse_color(cmd.color)
                _set_binary_labels_color(ly, rgba)
                return f"Showing tumor mask; recolored to {cmd.color}."
            except Exception as e:
                return f"Showing tumor mask; [color error: {e}]"
        return "Showing tumor (SOX10⁺) mask."

    if a=="special_show_density":
        ly=find_layer(viewer,f"{MARKER_COL}_density")
        if ly:
            ly.visible=True; viewer.layers.selection.active=ly
            msg=zoom_to_dense_region(viewer,ly.name)
            return f"Showing SOX10⁺ density map. {msg}"
        return "[warn] Density layer not found."

    if a=="special_update_density":
        sigma = float(cmd.sigma) if cmd.sigma is not None else 200.0
        cmap  = cmd.color or "magma"
        force = bool(cmd.force)
        adata=ad.read_h5ad(H5AD_PATH); obs=adata.obs.copy()
        density, lname = _ensure_density_layer(
            viewer, IMAGE_PATH, obs, MARKER_COL,
            sigma=sigma, colormap=cmap,
            force_recompute=force,
            layer_name=f"{MARKER_COL}_density",
            visible=True
        )
        bname=f"{MARKER_COL}_density_boundary"
        b_layer=find_layer(viewer,bname)
        if b_layer is not None: viewer.layers.remove(b_layer)
        paths=density_to_boundary_paths(density,percentile=95.0,simplify_tol=4.0,min_vertices=20)
        if paths:
            viewer.add_shapes(paths,shape_type="path",edge_color="white",face_color=(0,0,0,0),
                              edge_width=2,name=bname,blending="translucent").visible=True
        msg=zoom_to_dense_region(viewer,lname)
        return f"Density updated (sigma={sigma}, cmap={cmap}, force={force}). {msg}"

    return "Sorry, I didn't understand."

# ======================
# Basic utilities
# ======================
def toggle_panel(viewer, name: str, open_it: bool):
    docks = getattr(viewer.window, "_dock_widgets", {})
    target_key = None
    lname = name.lower().strip()
    for k in docks.keys():
        if k.lower() == lname:
            target_key = k; break
    if target_key is None:
        matches = [k for k in docks.keys() if lname in k.lower()]
        if len(matches) == 1:
            target_key = matches[0]
        elif len(matches) > 1:
            return f"Ambiguous panel '{name}'. Matches: {', '.join(matches)}"
        else:
            return f"Panel '{name}' not found. Panels: {', '.join(docks.keys()) or '(none)'}"
    docks[target_key].setVisible(open_it)
    return f"{'Opened' if open_it else 'Closed'} panel '{target_key}'"

def set_layer_visibility(viewer, name, op):
    ly = find_layer(viewer, name)
    if not ly: return f"Layer '{name}' not found."
    if op=="show": ly.visible=True
    elif op=="hide": ly.visible=False
    else: ly.visible = not ly.visible
    return f"{'Shown' if ly.visible else 'Hidden'} layer '{ly.name}'"

# ======================
# Mask + density + boundary core
# ======================
def density_to_boundary_paths(density, percentile=95.0, simplify_tol=4.0, min_vertices=20):
    vals=density[density>0]
    if vals.size==0:return []
    level=np.quantile(vals,percentile/100)
    raw=measure.find_contours(density,level=level)
    out=[]
    for c in raw:
        if len(c)>min_vertices:
            c=approximate_polygon(c,simplify_tol)
            if len(c)>min_vertices: out.append(c)
    return out

def _to_2d_gray_safe(arr):
    a=np.squeeze(arr)
    if a.ndim==2:return a
    if a.ndim==3 and a.shape[-1] in (3,4):
        rgb=a[...,:3].astype(float)
        return (0.2989*rgb[...,0]+0.587*rgb[...,1]+0.114*rgb[...,2]).astype(a.dtype)
    return _to_2d_gray_safe(a[0])

def load_image_for_mask(path):
    with TiffFile(path) as tf:arr=tf.series[0].asarray()
    img=_to_2d_gray_safe(arr)
    return img

def rebuild_labels_from_obs_safe(obs,shape):
    H,W=shape;labels=np.zeros((H,W),np.int32)
    cx,cy=obs["X_centroid"],obs["Y_centroid"]
    maj,minr,theta=obs["MajorAxisLength"],obs["MinorAxisLength"],obs["Orientation"]
    a,b=np.maximum(maj/2,1),np.maximum(minr/2,1)
    if ORIENTATION_IS_DEGREES:
        theta=np.deg2rad(theta)
    angles=np.linspace(0,2*np.pi,ELLIPSE_VERTS,endpoint=False)
    cosA,sinA=np.cos(angles),np.sin(angles)
    for x,y,aa,bb,th,cid in zip(cx,cy,a,b,theta,obs["CellID"]):
        ex = x + aa*cosA*np.cos(th) - bb*sinA*np.sin(th)
        ey = y + aa*cosA*np.sin(th) + bb*sinA*np.cos(th)
        rr,cc=polygon(ey,ex,shape=(H,W))
        bg=(labels[rr,cc]==0); labels[rr[bg],cc[bg]]=int(cid)
    return labels

def _ensure_labels(raw_image_path, obs, force_recompute=False):
    H,W=load_image_for_mask(raw_image_path).shape
    _, labels_tif, _, _, _ = get_output_paths(raw_image_path, MARKER_COL, 0)
    if (not force_recompute) and os.path.exists(labels_tif):
        labels=imread(labels_tif)
        if labels.shape==(H,W): return labels
    labels=rebuild_labels_from_obs_safe(obs,(H,W))
    try: imwrite(labels_tif, labels, dtype=np.int32)
    except Exception: pass
    return labels

def _ensure_mask(raw_image_path, obs, marker_col, force_recompute=False):
    _, labels_tif, mask_tif, _, _ = get_output_paths(raw_image_path, marker_col, 0)
    img=load_image_for_mask(raw_image_path); H,W=img.shape
    if (not force_recompute) and os.path.exists(labels_tif):
        labels=imread(labels_tif)
    else:
        labels=_ensure_labels(raw_image_path, obs, force_recompute=force_recompute)
    s=obs[marker_col]
    if s.dtype==bool: pos_bool=s
    else: pos_bool=s.astype(str).str.strip().str.lower().isin(["true","t","yes","y","1"])
    pos_ids=np.unique(obs.loc[pos_bool,"CellID"].astype(int))
    if (not force_recompute) and os.path.exists(mask_tif):
        m=imread(mask_tif).astype(np.uint8)
        if m.shape==(H,W): return m
    m=np.isin(labels,pos_ids).astype(np.uint8)
    try: imwrite(mask_tif,m,dtype=np.uint8)
    except Exception: pass
    return m

def _ensure_density_layer(viewer, raw_image_path, obs, marker_col,
                          sigma=200.0, colormap="magma",
                          force_recompute=False, layer_name=None,
                          visible=False):
    if 'CellID' not in obs.columns: raise ValueError("obs must contain 'CellID'")
    if marker_col not in obs.columns: raise ValueError(f"obs missing '{marker_col}'")
    s=obs[marker_col]
    if s.dtype==bool: pos_bool=s
    else: pos_bool=obs[marker_col].astype(str).str.strip().str.lower().isin(["true","t","yes","y","1"])
    pos_cells=obs.loc[pos_bool]

    img=load_image_for_mask(raw_image_path); H,W=img.shape
    _, _, _, dens_npy, _ = get_output_paths(raw_image_path, marker_col, sigma)

    if (not force_recompute) and os.path.exists(dens_npy):
        density=np.load(dens_npy)
    else:
        density=np.zeros((H,W),np.float32)
        if len(pos_cells)>0:
            y=np.clip(pos_cells["Y_centroid"].astype(int),0,H-1)
            x=np.clip(pos_cells["X_centroid"].astype(int),0,W-1)
            density[y,x]=1
            density=gaussian_filter(density,float(sigma))
            mx=float(density.max()); 
            if mx>0: density/=mx
        np.save(dens_npy,density)

    lname = layer_name or f"{marker_col}_density"
    existing=find_layer(viewer,lname)
    if existing is None:
        viewer.add_image(density,name=lname,colormap=colormap,opacity=0.6,
                         blending="additive",contrast_limits=(0,1),visible=visible)
    else:
        existing.data = density
        existing.colormap = colormap
        existing.opacity = 0.6
        existing.contrast_limits = (0,1)
        existing.blending="additive"
        existing.visible = visible or existing.visible
    return density, lname

def add_marker_mask_from_h5ad(
    viewer,
    raw_image_path: str,
    h5ad_path: str,
    marker_col: str,
    labels_name: str | None = None,
    mask_color=(1,0,0,1),
    bg_alpha: float = 0.0,
    show_density: bool = True,
    density_sigma: float = 200.0,
    density_color: str = "magma",
    draw_density_boundary: bool = True,
    boundary_percentile: float = 95.0,
    boundary_width: float = 2.0,
    boundary_color = "white",
    force_recompute: bool = False,
    initial_visible_mask: bool = False,
    initial_visible_density: bool = False,
    initial_visible_boundary: bool = False,
):
    outdir, labels_tif, mask_tif, dens_npy, bnd_npz = get_output_paths(raw_image_path, marker_col, density_sigma)

    # 1) base image (visible)
    img=load_image_for_mask(raw_image_path)
    base_name=os.path.basename(raw_image_path)
    if find_layer(viewer, base_name) is None:
        viewer.add_image(img,name=base_name,visible=True)
    print(f"[info] image: {img.shape} → outputs in {outdir}")

    # 2) obs
    adata=ad.read_h5ad(h5ad_path)
    obs=adata.obs.copy()

    # 3) mask (hidden initially)
    pos_mask=_ensure_mask(raw_image_path, obs, marker_col, force_recompute=force_recompute)
    fg_rgba=_parse_color(mask_color); bg_rgba=(0,0,0,float(bg_alpha))
    color_map={0:bg_rgba,1:fg_rgba}
    lname=labels_name or f"{marker_col}_mask"
    ly=find_layer(viewer,lname)
    if ly is None:
        ly=viewer.add_labels(pos_mask,name=lname,opacity=1.0,blending="translucent",visible=initial_visible_mask)
    else:
        ly.data=pos_mask; ly.visible=initial_visible_mask
    try: ly.color=color_map
    except Exception: ly.colors=color_map
    try: ly.color_mode = 'direct'
    except Exception: pass

    # 4) density (hidden initially)
    density=None
    if show_density:
        density, dname = _ensure_density_layer(
            viewer, raw_image_path, obs, marker_col,
            sigma=density_sigma, colormap=density_color,
            force_recompute=force_recompute,
            layer_name=f"{marker_col}_density",
            visible=initial_visible_density
        )

    # 5) boundary (hidden initially)
    if draw_density_boundary and density is not None:
        paths=[]
        if (not force_recompute) and os.path.exists(bnd_npz):
            paths=load_boundary_paths_npz(bnd_npz)
        else:
            paths=density_to_boundary_paths(density,percentile=boundary_percentile,
                                            simplify_tol=4.0,min_vertices=20)
            save_boundary_paths_npz(paths,bnd_npz)
        if paths:
            try: edge_rgba=_parse_color(boundary_color)
            except Exception: edge_rgba=(1,1,1,1)
            edge_colors=np.tile(np.array(edge_rgba,dtype=float),(len(paths),1))
            face_colors=np.tile(np.array([0,0,0,0],dtype=float),(len(paths),1))
            bname=f"{marker_col}_density_boundary"
            b_layer=find_layer(viewer,bname)
            if b_layer is not None: viewer.layers.remove(b_layer)
            viewer.add_shapes(paths,shape_type="path",edge_color=edge_colors,face_color=face_colors,
                              edge_width=boundary_width,name=bname,blending="translucent",
                              visible=initial_visible_boundary)

    print("[info] layers:", [L.name for L in viewer.layers])
    return lname

# ======================
# Docks
# ======================
class CommandDock(QtWidgets.QWidget):
    def __init__(self,viewer):
        super().__init__();self.viewer=viewer
        self.setLayout(QtWidgets.QVBoxLayout())
        self.input=QtWidgets.QLineEdit()
        self.input.setPlaceholderText("try: 'turn off the tumor mask', 'turn on tumor SOX10 density', 'make it yellow', 'zoom to densest', 'update density sigma=250 color=inferno'")
        self.run_btn=QtWidgets.QPushButton("Run")
        self.out=QtWidgets.QPlainTextEdit();self.out.setReadOnly(True)
        row=QtWidgets.QHBoxLayout();row.addWidget(self.input);row.addWidget(self.run_btn)
        self.layout().addLayout(row);self.layout().addWidget(self.out)
        self.run_btn.clicked.connect(self.on_run);self.input.returnPressed.connect(self.on_run)
    def write(self,msg):self.out.appendPlainText(msg)
    def on_run(self):
        text=self.input.text().strip(); 
        if not text:return
        cmd=parse_command_regex(text); src="regex"
        if isinstance(cmd,CmdUnknown) and cmd.action=="unknown": 
            try:cmd=llm_parse_command(text);src="LLM"
            except Exception as e:self.write(f"[LLM ERROR] {e}")
        try:resp=execute(cmd,self.viewer)
        except Exception as e:resp=f"Error: {e}"
        self.write(f"> {text} [{src}]\n{resp}\n");self.input.clear()

class DensityControlDock(QtWidgets.QWidget):
    def __init__(self, viewer):
        super().__init__()
        self.viewer = viewer
        self.setLayout(QtWidgets.QVBoxLayout())
        g = QtWidgets.QGroupBox("SOX10⁺ Mask & Density")
        self.layout().addWidget(g)
        form = QtWidgets.QFormLayout(); g.setLayout(form)

        self.mask_color_preview = QtWidgets.QLabel("      ")
        self.mask_color_preview.setStyleSheet("background:#ff3333; border:1px solid #444;")
        self.btn_pick_mask_color = QtWidgets.QPushButton("Pick mask color…")
        self.btn_pick_mask_color.clicked.connect(self._pick_mask_color)
        row_mask = QtWidgets.QHBoxLayout(); row_mask.addWidget(self.mask_color_preview); row_mask.addWidget(self.btn_pick_mask_color)
        form.addRow("Mask color:", row_mask)

        self.combo_cmap = QtWidgets.QComboBox()
        self.combo_cmap.addItems(["magma","viridis","plasma","inferno","gray","cyan","blue","green","red","magenta","yellow","turbo"])
        self.combo_cmap.setCurrentText("magma")
        form.addRow("Density colormap:", self.combo_cmap)

        self.sigma_spin = QtWidgets.QDoubleSpinBox(); self.sigma_spin.setRange(1.0,2000.0); self.sigma_spin.setDecimals(1); self.sigma_spin.setSingleStep(10.0); self.sigma_spin.setValue(200.0)
        self.sigma_slider = QtWidgets.QSlider(Qt.Horizontal); self.sigma_slider.setMinimum(1); self.sigma_slider.setMaximum(2000); self.sigma_slider.setSingleStep(10); self.sigma_slider.setValue(200)
        self.sigma_spin.valueChanged.connect(lambda v: self.sigma_slider.setValue(int(round(v))))
        self.sigma_slider.valueChanged.connect(lambda v: self.sigma_spin.setValue(float(v)))
        row_sigma = QtWidgets.QHBoxLayout(); row_sigma.addWidget(self.sigma_spin); row_sigma.addWidget(self.sigma_slider)
        form.addRow("Sigma (px):", row_sigma)

        self.chk_recompute = QtWidgets.QCheckBox("Force recompute (ignore cache)")
        form.addRow("", self.chk_recompute)

        btn_row = QtWidgets.QHBoxLayout()
        self.btn_apply_mask = QtWidgets.QPushButton("Apply mask color")
        self.btn_apply_density = QtWidgets.QPushButton("Update density")
        self.btn_zoom_dense = QtWidgets.QPushButton("Zoom to densest")
        btn_row.addWidget(self.btn_apply_mask); btn_row.addWidget(self.btn_apply_density); btn_row.addWidget(self.btn_zoom_dense)
        self.layout().addLayout(btn_row)

        self.btn_apply_mask.clicked.connect(lambda _checked=False: self._apply_mask_color())
        self.btn_apply_density.clicked.connect(lambda _checked=False: self._update_density())
        self.btn_zoom_dense.clicked.connect(lambda _checked=False: self._zoom_dense())

    def _pick_mask_color(self):
        qc = QtWidgets.QColorDialog.getColor()
        if qc.isValid():
            self.mask_color_preview.setStyleSheet(f"background:{qc.name()}; border:1px solid #444;")
            self._apply_mask_color(color_override=qc)

    def _apply_mask_color(self, color_override=None):
        ly = find_layer(self.viewer, f"{MARKER_COL}_mask")
        if ly is None:
            print("[GUI] mask layer not found."); return
        if isinstance(color_override, QColor):
            r,g,b,a = color_override.getRgbF(); rgba = (float(r),float(g),float(b),float(a))
        else:
            style = self.mask_color_preview.styleSheet()
            m = re.search(r'background:\s*(#[0-9a-fA-F]{6})', style); hexc = m.group(1) if m else "#ff3333"
            rgba = _parse_color(hexc)
        _set_binary_labels_color(ly, rgba)
        print(f"[GUI] mask color set to {rgba}")

    def _update_density(self):
        base_name = os.path.basename(IMAGE_PATH)
        if find_layer(self.viewer, base_name) is None:
            img = load_image_for_mask(IMAGE_PATH); self.viewer.add_image(img, name=base_name)
        adata = ad.read_h5ad(H5AD_PATH); obs = adata.obs.copy()
        sigma = float(self.sigma_spin.value()); cmap = self.combo_cmap.currentText(); force = self.chk_recompute.isChecked()
        density, lname = _ensure_density_layer(
            self.viewer, IMAGE_PATH, obs, MARKER_COL,
            sigma=sigma, colormap=cmap, force_recompute=force,
            layer_name=f"{MARKER_COL}_density", visible=True
        )
        bname = f"{MARKER_COL}_density_boundary"
        b_layer = find_layer(self.viewer, bname)
        if b_layer is not None: self.viewer.layers.remove(b_layer)
        paths = density_to_boundary_paths(density, percentile=95.0, simplify_tol=4.0, min_vertices=20)
        if paths:
            self.viewer.add_shapes(paths, shape_type="path",
                                   edge_color="white", face_color=(0,0,0,0),
                                   edge_width=2, name=bname, blending="translucent").visible=True
        print(f"[GUI] density updated (sigma={sigma}, cmap={cmap}, force={force})")

    def _zoom_dense(self):
        msg = zoom_to_dense_region(self.viewer, f"{MARKER_COL}_density"); print(f"[GUI] {msg}")

# ======================
# MAIN
# ======================
if __name__=="__main__":
    os.environ.setdefault("LLM_BACKEND","ollama")
    force = bool(int(os.getenv("FORCE_RECOMPUTE","0")))
    viewer=napari.Viewer()

    try:
        add_marker_mask_from_h5ad(
            viewer,
            IMAGE_PATH,
            H5AD_PATH,
            MARKER_COL,
            mask_color="#ff3333",
            show_density=True,
            density_sigma=200.0,
            density_color="magma",
            draw_density_boundary=True,
            boundary_percentile=95.0,
            boundary_width=2.0,
            boundary_color="white",
            force_recompute=force,
            initial_visible_mask=False,
            initial_visible_density=False,
            initial_visible_boundary=False,
        )
        print("Ready. Base TIFF visible; mask/density/boundary are hidden.")
    except Exception as e:
        print(f"[WARN] Could not build mask: {e}")

    viewer.window.add_dock_widget(CommandDock(viewer), name="Command", area="right")
    viewer.window.add_dock_widget(DensityControlDock(viewer), name="Mask & Density Controls", area="right")

    print("Launching napari…")
    napari.run()