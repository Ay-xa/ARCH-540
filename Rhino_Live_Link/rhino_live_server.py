"""
Rhino / Grasshopper Live Link  --  this script runs INSIDE Rhino.

How to start it later:
  1. Open the Rhino file and the Grasshopper definition you want to show.
  2. In Rhino's command line type:  RunPythonScript   and pick this file.
  3. Open  http://localhost:8765  in any browser.

What it does:
  - serves the web page (index.html in this folder)
  - streams everything currently visible in Rhino and in the Grasshopper preview
  - lets the web page move the Grasshopper number sliders
Nothing here changes your files; it only reads geometry and moves sliders.
"""
import os
import sys
import json
import types
import threading
import http.server
import socketserver
from urllib.parse import urlparse

import System
import Rhino
import Rhino.Geometry as rg
import Grasshopper
from Grasshopper.Kernel import IGH_Component, IGH_Param, IGH_PreviewObject
from Grasshopper.Kernel.Special import GH_NumberSlider

PORT = 8765
WEB_DIR = os.path.dirname(os.path.abspath(__file__))
UI_TIMEOUT_SECONDS = 30


# ---------------------------------------------------------------- persistent state
def _store():
    st = sys.modules.get("rhino_live_link_state")
    if st is None:
        st = types.ModuleType("rhino_live_link_state")
        st.server = None
        st.change_counter = 0
        st.rhino_events_attached = False
        st.gh_docs_hooked = set()
        sys.modules["rhino_live_link_state"] = st
    return st


def _bump(*args):
    _store().change_counter += 1


# ---------------------------------------------------------------- run on Rhino's UI thread
def on_ui(fn):
    result = {}
    done = threading.Event()

    def wrapper():
        try:
            result["value"] = fn()
        except Exception as exc:  # noqa: BLE001 - surfaced to the browser
            result["error"] = "%s: %s" % (type(exc).__name__, exc)
        finally:
            done.set()

    Rhino.RhinoApp.InvokeOnUiThread(System.Action(wrapper))
    if not done.wait(UI_TIMEOUT_SECONDS):
        raise RuntimeError("Rhino is busy (a command or dialog may be open)")
    if "error" in result:
        raise RuntimeError(result["error"])
    return result.get("value")


# ---------------------------------------------------------------- grasshopper helpers
def gh_doc():
    canvas = Grasshopper.Instances.ActiveCanvas
    return canvas.Document if canvas is not None else None


def hook_gh_doc(gd):
    st = _store()
    if gd is None:
        return
    key = str(gd.DocumentID)
    if key in st.gh_docs_hooked:
        return
    gd.SolutionEnd += _bump
    st.gh_docs_hooked.add(key)


def dec(d):
    return System.Decimal.ToDouble(d)


def collect_sliders(gd):
    out = []
    if gd is None:
        return out
    for obj in gd.Objects:
        if isinstance(obj, GH_NumberSlider):
            s = obj.Slider
            piv = obj.Attributes.Pivot
            out.append({
                "id": str(obj.InstanceGuid),
                "name": obj.NickName or obj.Name,
                "min": dec(s.Minimum),
                "max": dec(s.Maximum),
                "value": dec(s.Value),
                "decimals": int(s.DecimalPlaces),
                "_y": float(piv.Y), "_x": float(piv.X),
            })
    out.sort(key=lambda d: (d["_y"], d["_x"]))
    for d in out:
        d.pop("_y", None)
        d.pop("_x", None)
    return out


def set_slider(slider_id, value):
    gd = gh_doc()
    if gd is None:
        raise RuntimeError("No Grasshopper definition is open")
    for obj in gd.Objects:
        if isinstance(obj, GH_NumberSlider) and str(obj.InstanceGuid) == slider_id:
            s = obj.Slider
            value = max(dec(s.Minimum), min(dec(s.Maximum), float(value)))
            obj.SetSliderValue(System.Decimal(value))
            obj.ExpireSolution(True)
            Grasshopper.Instances.RedrawCanvas()
            doc = Rhino.RhinoDoc.ActiveDoc
            if doc is not None:
                doc.Views.Redraw()
            return get_state()
    raise RuntimeError("Slider not found (was it deleted?)")


# ---------------------------------------------------------------- geometry -> json
def color_hex(col):
    return "#%02x%02x%02x" % (col.R, col.G, col.B)


def mesh_json(mesh, source, color):
    mesh.Faces.ConvertQuadsToTriangles()
    verts = [round(float(x), 4) for x in mesh.Vertices.ToFloatArray()]
    faces = [int(i) for i in mesh.Faces.ToIntArray(True)]
    return {"type": "mesh", "src": source, "c": color, "v": verts, "i": faces}


def curve_json(curve, source, color):
    pc = curve.ToPolyline(0.02, 0.2, 0.05, 200)
    if pc is None:
        return None
    pts = []
    for k in range(pc.PointCount):
        p = pc.Point(k)
        pts.extend([round(p.X, 4), round(p.Y, 4), round(p.Z, 4)])
    return {"type": "curve", "src": source, "c": color, "p": pts}


def add_geometry(items, g, source, color=None):
    if g is None:
        return
    if isinstance(g, rg.Extrusion):
        g = g.ToBrep()
    elif isinstance(g, rg.Surface):
        g = g.ToBrep()

    if isinstance(g, rg.Brep):
        meshes = rg.Mesh.CreateFromBrep(g, rg.MeshingParameters.FastRenderMesh)
        if meshes:
            m = rg.Mesh()
            for mm in meshes:
                m.Append(mm)
            items.append(mesh_json(m, source, color))
    elif isinstance(g, rg.Mesh):
        items.append(mesh_json(g.DuplicateMesh(), source, color))
    elif isinstance(g, rg.Curve):
        cj = curve_json(g, source, color)
        if cj:
            items.append(cj)
    elif isinstance(g, rg.Line):
        cj = curve_json(rg.LineCurve(g), source, color)
        if cj:
            items.append(cj)
    elif isinstance(g, rg.Point3d):
        items.append({"type": "point", "src": source, "c": color, "p": [g.X, g.Y, g.Z]})
    elif isinstance(g, rg.Point):
        p = g.Location
        items.append({"type": "point", "src": source, "c": color, "p": [p.X, p.Y, p.Z]})


def gh_geometry(gd):
    items = []
    if gd is None:
        return items
    for obj in gd.Objects:
        if isinstance(obj, GH_NumberSlider):
            continue
        if isinstance(obj, IGH_PreviewObject) and obj.Hidden:
            continue
        if isinstance(obj, IGH_Component):
            params = list(obj.Params.Output)
        elif isinstance(obj, IGH_Param):
            params = [obj]
        else:
            continue
        for p in params:
            try:
                data = p.VolatileData
            except Exception:  # noqa: BLE001
                continue
            for goo in data.AllData(True):
                try:
                    g = goo.ScriptVariable()
                except Exception:  # noqa: BLE001
                    continue
                add_geometry(items, g, "gh")
    return items


def rhino_geometry(doc):
    items = []
    if doc is None:
        return items
    for obj in doc.Objects:
        if not obj.Visible:
            continue
        lyr = doc.Layers[obj.Attributes.LayerIndex]
        if not lyr.IsVisible:
            continue
        add_geometry(items, obj.Geometry, "rhino", color_hex(obj.Attributes.DrawColor(doc)))
    return items


# ---------------------------------------------------------------- state
def get_version():
    doc = Rhino.RhinoDoc.ActiveDoc
    gd = gh_doc()
    hook_gh_doc(gd)
    parts = [_store().change_counter, doc.Objects.Count if doc else 0]
    if gd is not None:
        parts.append(gd.ObjectCount)
        parts.extend(round(s["value"], 6) for s in collect_sliders(gd))
    return str(abs(hash(tuple(parts))))


def get_state():
    doc = Rhino.RhinoDoc.ActiveDoc
    gd = gh_doc()
    hook_gh_doc(gd)
    return {
        "version": get_version(),
        "rhinoFile": os.path.basename(doc.Path) if (doc and doc.Path) else "(unsaved)",
        "ghFile": os.path.basename(gd.FilePath) if (gd and gd.FilePath) else ("(unsaved definition)" if gd else "(no Grasshopper open)"),
        "units": str(doc.ModelUnitSystem) if doc else "",
        "sliders": collect_sliders(gd),
        "gh": gh_geometry(gd),
        "rhino": rhino_geometry(doc),
    }


# ---------------------------------------------------------------- http
class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _send(self, code, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else json.dumps(body, separators=(",", ":")).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = urlparse(self.path).path
        try:
            if path in ("/", "/index.html"):
                with open(os.path.join(WEB_DIR, "index.html"), "rb") as f:
                    self._send(200, f.read(), "text/html; charset=utf-8")
            elif path == "/api/version":
                self._send(200, {"version": on_ui(get_version)})
            elif path == "/api/state":
                self._send(200, on_ui(get_state))
            else:
                self._send(404, {"error": "not found"})
        except Exception as exc:  # noqa: BLE001
            self._send(500, {"error": str(exc)})

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            n = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(n) or b"{}")
            if path == "/api/set":
                sid = payload.get("id")
                val = float(payload.get("value"))
                self._send(200, on_ui(lambda: set_slider(sid, val)))
            else:
                self._send(404, {"error": "not found"})
        except Exception as exc:  # noqa: BLE001
            self._send(500, {"error": str(exc)})


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def start():
    st = _store()
    if st.server is not None:
        try:
            st.server.shutdown()
            st.server.server_close()
        except Exception:  # noqa: BLE001
            pass
        st.server = None

    if not st.rhino_events_attached:
        Rhino.RhinoDoc.AddRhinoObject += _bump
        Rhino.RhinoDoc.DeleteRhinoObject += _bump
        Rhino.RhinoDoc.UndeleteRhinoObject += _bump
        Rhino.RhinoDoc.ReplaceRhinoObject += _bump
        Rhino.RhinoDoc.ModifyObjectAttributes += _bump
        Rhino.RhinoDoc.LayerTableEvent += _bump
        st.rhino_events_attached = True

    hook_gh_doc(gh_doc())

    srv = Server(("127.0.0.1", PORT), Handler)
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    st.server = srv
    msg = "Rhino Live Link running at http://localhost:%d  (page: %s)" % (PORT, os.path.join(WEB_DIR, "index.html"))
    Rhino.RhinoApp.WriteLine(msg)
    print(msg)


start()
