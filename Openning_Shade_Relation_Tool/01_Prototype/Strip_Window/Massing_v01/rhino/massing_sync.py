# massing_sync.py — Grasshopper「Python 3 Script」组件「massing sync」的源码（Massing_v01，PLAN_massing_v01 §4）
# 由 Trigger 每 0.5 s 触发。输入：path（state.json 路径）。
# 输出：floors（楼板 Brep）、windows（窗条面）、status（文字）；给 Ladybug 的 winMesh（每扇窗条一个网格，沿长度分格）、winFaces（每个网格的面数）、
#       epw（气象文件路径）、north（Ladybug 的 north_：+Y 到北的逆时针角度）、m0 / m1（分析期起止月）。
# 做的事：读 json → 周界（矩形减凹口，三层同形）→ 楼板预览 → 立面分段 → 窗条预览 → 写回 handle / results。
# 手柄：Rhino「Handles」图层上名为 ops.id 的点。谁后动谁算数：ops.at（页面）与 handle.at（Rhino）比时间戳。
# GH 只写 handle / results / updated_by / updated_at；其余字段原样保留。
import json, os, math, datetime
import Rhino
import Rhino.Geometry as rg
import scriptcontext as sc

TOL = 0.005          # m；手柄位置差小于这个值视为没动
OFF = 0.02           # 窗条面往外偏移，避免和楼板面重叠闪烁
EPW_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(path)) if 'path' in dir() and path else ".", "..", "..", "..", "..", "..", "Passivehouse_Tool", "02_Data", "EPW"))
EPW = {"apNow": "CAN_BC_Vancouver.Intl.AP.718920_CWEC2020.epw", "hbNow": "CAN_BC_Vancouver.Harbour.CS.712010_TMYx.2009-2023.epw", "f2080": "MORPHED_SSP585_2080s_CAN_BC_VANCOUVER-INTL-A_CWEC2020.epw"}
PERIOD = {"summer": (6, 8), "winter": (12, 2), "annual": (1, 12)}


def now():
    return datetime.datetime.now().isoformat(timespec="milliseconds")


def read(p):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def write(p, d):
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    os.replace(tmp, p)


def edges(L, W):
    # 逆时针：A 底边(y=0) → B 右边(x=L) → C 顶边(y=W) → D 左边(x=0)。每条：起点 S、方向 u、向内法线 n、长度 E、名字
    return [((0.0, 0.0), (1.0, 0.0), (0.0, 1.0), L, "A"),
            ((L, 0.0), (0.0, 1.0), (-1.0, 0.0), W, "B"),
            ((L, W), (-1.0, 0.0), (0.0, -1.0), L, "C"),
            ((0.0, W), (0.0, -1.0), (1.0, 0.0), W, "D")]


def notch_limits(L, W, op):
    E = L if op["edge"] in "AC" else W
    dmax = (W if op["edge"] in "AC" else L) / 2.0
    return E, dmax


def outline(L, W, op):
    """返回 (顶点列表, 每条边的名字)；第 i 条边从 pts[i] 到 pts[(i+1)%n]"""
    pts, names = [], []
    for S, u, n, E, name in edges(L, W):
        if op and op["edge"] == name and op["width"] > 0.01 and op["depth"] > 0.01:
            w = min(op["width"], E)
            d = min(op["depth"], notch_limits(L, W, op)[1])
            c = op["pos"] * E
            a, b = max(0.0, c - w / 2.0), min(E, c + w / 2.0)
            if b - a < 0.01:
                pts.append(S); names.append(name); continue
            P = lambda t, k: (S[0] + u[0] * t + n[0] * k, S[1] + u[1] * t + n[1] * k)
            for p, nm in ((S, name + "1"), (P(a, 0), name + "2"), (P(a, d), name + "3"), (P(b, d), name + "4"), (P(b, 0), name + "5")):
                pts.append(p); names.append(nm)
        else:
            pts.append(S); names.append(name)
    # 去掉零长度的边（凹口贴着端点时）
    out_p, out_n = [], []
    m = len(pts)
    for i in range(m):
        p, q = pts[i], pts[(i + 1) % m]
        if math.hypot(q[0] - p[0], q[1] - p[1]) > 1e-6:
            out_p.append(p); out_n.append(names[i])
    return out_p, out_n


def norm(a):
    return (a % 360.0 + 360.0) % 360.0


def segments(pts, names, az0):
    segs = []
    m = len(pts)
    for i in range(m):
        p, q = pts[i], pts[(i + 1) % m]
        dx, dy = q[0] - p[0], q[1] - p[1]
        ln = math.hypot(dx, dy)
        nx, ny = dy / ln, -dx / ln                       # 逆时针多边形的外法线
        az = norm(math.degrees(math.atan2(nx, ny)) + az0 - 180.0)   # A 边(外法线 −Y)朝向 = az0
        segs.append({"edge": names[i], "az": round(az, 1), "len": round(ln, 3), "p": [round(p[0], 3), round(p[1], 3)], "q": [round(q[0], 3), round(q[1], 3)]})
    return segs


def area(pts):
    s = 0.0
    for i in range(len(pts)):
        p, q = pts[i], pts[(i + 1) % len(pts)]
        s += p[0] * q[1] - q[0] * p[1]
    return abs(s) / 2.0


def find_handle(rdoc, name):
    for o in rdoc.Objects:
        if o.Name == name and isinstance(o.Geometry, rg.Point):
            return o
    return None


def handle_to_params(pt, L, W, op):
    for S, u, n, E, name in edges(L, W):
        if name == op["edge"]:
            vx, vy = pt.X - S[0], pt.Y - S[1]
            t = (vx * u[0] + vy * u[1]) / E
            d = vx * n[0] + vy * n[1]
            _, dmax = notch_limits(L, W, op)
            return min(max(t, 0.0), 1.0), min(max(d, 0.0), dmax)
    return op["pos"], op["depth"]


def params_to_point(L, W, op):
    for S, u, n, E, name in edges(L, W):
        if name == op["edge"]:
            return rg.Point3d(S[0] + u[0] * op["pos"] * E + n[0] * op["depth"], S[1] + u[1] * op["pos"] * E + n[1] * op["depth"], 0.0)
    return rg.Point3d(0, 0, 0)


def build(d):
    b, w = d["building"], d["windows"]
    L, W, H, N, slab = float(b["L"]), float(b["W"]), float(b["H"]), int(b["floors"]), float(b.get("slab", 0.35))
    op = d["ops"][0] if d.get("ops") else None
    pts, names = outline(L, W, op)
    segs = segments(pts, names, float(b["az0"]))
    winH = float(w["wwr"]) * (H - slab)
    sill = float(w["sill"])
    floors, wins, meshes, faces = [], [], [], []
    poly = rg.Polyline([rg.Point3d(p[0], p[1], 0.0) for p in pts] + [rg.Point3d(pts[0][0], pts[0][1], 0.0)])
    for i in range(N):
        crv = poly.ToNurbsCurve(); crv.Translate(rg.Vector3d(0, 0, i * H))
        ext = rg.Extrusion.Create(crv, H, True)
        if ext: floors.append(ext.ToBrep())
        if winH > 0.01:
            for s in segs:
                p, q = s["p"], s["q"]
                dx, dy = q[0] - p[0], q[1] - p[1]; ln = math.hypot(dx, dy); nx, ny = dy / ln * OFF, -dx / ln * OFF
                z0, z1 = i * H + sill, i * H + sill + winH
                srf = rg.NurbsSurface.CreateFromCorners(rg.Point3d(p[0] + nx, p[1] + ny, z0), rg.Point3d(q[0] + nx, q[1] + ny, z0),
                                                        rg.Point3d(q[0] + nx, q[1] + ny, z1), rg.Point3d(p[0] + nx, p[1] + ny, z1))
                if srf: wins.append(srf)
                # Ladybug 分析网格：沿长度每 ~1 m 一格，一行；顶点顺序与窗面相同，法线朝外
                nc = max(1, int(round(ln)))
                m = rg.Mesh()
                for k in range(nc + 1):
                    t = k / float(nc)
                    m.Vertices.Add(p[0] + dx * t + nx, p[1] + dy * t + ny, z0); m.Vertices.Add(p[0] + dx * t + nx, p[1] + dy * t + ny, z1)
                for k in range(nc):
                    m.Faces.AddFace(2 * k, 2 * k + 2, 2 * k + 3, 2 * k + 1)
                m.Normals.ComputeNormals(); m.Compact()
                meshes.append(m); faces.append(nc)
    for s in segs:
        s["winArea"] = round(s["len"] * winH, 3)
    res = {"seq": int(d.get("run", {}).get("seq", 0)), "at": "", "floorsSame": True, "nSeg": len(segs),
           "floors": [{"i": i + 1, "area": round(area(pts), 2)} for i in range(N)],
           "perimeter": [[round(p[0], 3), round(p[1], 3)] for p in pts],
           "segments": segs, "winH": round(winH, 3), "warnings": []}
    if op and op["width"] > min(L, W):
        res["warnings"].append("notch width clipped to the edge length")
    return floors, wins, res, meshes, faces


def run(path):
    st = sc.sticky
    rdoc = Rhino.RhinoDoc.ActiveDoc
    if not path or not os.path.isfile(path):
        return [], [], "no state.json at: %s" % path
    d = read(path)
    b = d["building"]; L, W = float(b["L"]), float(b["W"])
    op = d["ops"][0] if d.get("ops") else None
    changed_file = st.get("massing_stamp") != d.get("updated_at")
    handle_moved, handle_written = False, False
    note = ""
    if op:
        hid = op["id"]
        h = (d.get("handle") or {}).get(hid) or {}
        obj = find_handle(rdoc, hid)
        if obj is not None:
            pt = obj.Geometry.Location
            pos_p, dep_p = handle_to_params(pt, L, W, op)
            ops_at, h_at = op.get("at", ""), h.get("at", "")
            if ops_at > h_at:
                # 页面后动：以 ops 为准，把 Rhino 的点挪过去，并把 handle 记成同一时间戳（避免来回触发）
                target = params_to_point(L, W, op)
                if target.DistanceTo(pt) > TOL:
                    rdoc.Objects.Replace(obj.Id, target)
                    note = "handle moved to page values"
                if h.get("pos") != op["pos"] or h.get("depth") != op["depth"] or h_at != ops_at:
                    d.setdefault("handle", {})[hid] = {"pos": op["pos"], "depth": op["depth"], "at": ops_at}
                    handle_written = True
            else:
                # Rhino 后动（或相等）：点离上次记录的位置远了 → 用户拖过 → 写 handle，并用点的值
                if abs(pos_p - float(h.get("pos", op["pos"]))) * (L if op["edge"] in "AC" else W) > TOL or abs(dep_p - float(h.get("depth", op["depth"]))) > TOL:
                    d.setdefault("handle", {})[hid] = {"pos": round(pos_p, 4), "depth": round(dep_p, 3), "at": now()}
                    handle_written = True; handle_moved = True
                    note = "handle dragged in Rhino"
                hv = d["handle"].get(hid) if d.get("handle") else None
                if hv:
                    op = dict(op, pos=float(hv["pos"]), depth=float(hv["depth"]))
                    d["ops"][0] = dict(d["ops"][0], pos=float(hv["pos"]), depth=float(hv["depth"]))   # 只在内存里用，不写回 ops
    run = d.get("run", {}) if isinstance(d.get("run"), dict) else {}
    epw = os.path.join(EPW_DIR, EPW.get(run.get("clim", "apNow"), EPW["apNow"]))
    m0, m1 = PERIOD.get(run.get("period", "summer"), PERIOD["summer"])
    north = (float(b["az0"]) - 180.0) % 360.0
    cached = st.get("massing_out")
    if not changed_file and not handle_moved and cached and len(cached) == 6:
        f, w_, status, meshes, faces, nseg = cached
        return f, w_, status, meshes, faces, epw, north, m0, m1, nseg
    floors, wins, res, meshes, faces = build(d)
    prev = st.get("massing_res")
    if handle_written or changed_file or prev != res:
        res["at"] = now()
        fresh = read(path)                       # 重新读一次，只覆盖 GH 自己的字段
        if handle_written:
            fresh["handle"] = d["handle"]
        old = fresh.get("results") or {}
        if old.get("sun") and old.get("segments") == res["segments"] and old.get("winH") == res["winH"] and (fresh.get("run") or {}).get("period") == old["sun"].get("period"):
            res["sun"] = old["sun"]              # 几何和分析期没变：保留上次的日照结果，不让页面空等
        fresh["results"] = res
        fresh["updated_by"] = "gh"
        fresh["updated_at"] = now()
        write(path, fresh)
        st["massing_stamp"] = fresh["updated_at"]
        st["massing_res"] = dict(res, at="")
    else:
        st["massing_stamp"] = d.get("updated_at")
    status = "seq %d | %d floors | %d segments | notch %s pos %.2f w %.1f d %.1f | %s" % (
        res["seq"], len(res["floors"]), len(res["segments"]), op["edge"] if op else "-", op["pos"] if op else 0, op["width"] if op else 0, op["depth"] if op else 0, note or "ok")
    st["massing_out"] = (floors, wins, status, meshes, faces, res["nSeg"])
    return floors, wins, status, meshes, faces, epw, north, m0, m1, res["nSeg"]


floors, windows, status, winMesh, winFaces, epw, north, m0, m1, nSeg = run(path)
