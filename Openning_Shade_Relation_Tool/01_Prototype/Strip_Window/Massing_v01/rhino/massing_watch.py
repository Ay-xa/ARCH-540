# massing_watch.py — Grasshopper「Python 3 Script」组件「massing watch」的源码（2026-10-03）
# 作用：Trigger 每 0.5 s 只触发这个小组件；它看 state.json 的修改时间 / 大小和所有手柄点（名字以 notch / court 开头）的坐标，
#       有变化才让「massing sync」重算。这样楼板 / 窗条 / 装置的预览不会每半秒清一次（以前整栋模型在闪）。
# 输入：path（state.json）。输出：status。
import os, scriptcontext as sc, Rhino, Grasshopper as gh, System
import Rhino.Geometry as rg

SYNC_GUID = "59ab856d-c7e5-44ce-99c9-578fe8373b83"     # massing sync 组件的 InstanceGuid


def key(path):
    try:
        st = os.stat(path); k = [st.st_mtime_ns, st.st_size]
    except Exception:
        k = [0, 0]
    rdoc = Rhino.RhinoDoc.ActiveDoc
    pts = []
    for o in rdoc.Objects:
        nm = o.Name or ""
        if isinstance(o.Geometry, rg.Point) and nm.startswith(("notch", "court", "split")):
            p = o.Geometry.Location
            pts.append((nm, round(p.X, 3), round(p.Y, 3)))
    return tuple(k) + tuple(sorted(pts))


def main(path):
    if not path:
        return "no path"
    k = key(path)
    if sc.sticky.get("massing_watch_key") == k:
        return "idle"
    sc.sticky["massing_watch_key"] = k
    ghdoc = ghenv.Component.OnPingDocument()
    comp = ghdoc.FindObject(System.Guid(SYNC_GUID), True) if ghdoc else None
    if comp is None:
        return "sync component not found"
    def fire(d):
        comp.ExpireSolution(False)
    ghdoc.ScheduleSolution(5, gh.Kernel.GH_Document.GH_ScheduleDelegate(fire))
    return "changed -> sync"


status = main(path)
