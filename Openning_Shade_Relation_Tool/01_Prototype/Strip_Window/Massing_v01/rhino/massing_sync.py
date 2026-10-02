# massing_sync.py — Grasshopper「Python 3 Script」组件「massing sync」的源码（Massing_v01，PLAN_massing_v01 §4）
# 由 Trigger 每 0.5 s 触发。输入：path（state.json 路径）。
# 输出：floors（楼板 Brep）、windows（窗条面）、status（文字）；给 Ladybug 的 winMesh（每扇窗条一个网格，沿长度分格）、winFaces（每个网格的面数）、
#       epw（气象文件路径）、north（Ladybug 的 north_：+Y 到北的逆时针角度）、m0 / m1（分析期起止月）、nSeg（立面段总数，含所有楼层）、
#       devMesh（遮阳装置的面片，给预览和 Direct Sun Hours 的 context）。
# 楼层组（第二刀）：building.groups = {podium: 下面几层算第 1 组, setback: {A,B,C,D} 第 2 组四条边各自向内退多少}。
#   每层按自己的矩形生成周界；每个操作 apply = all / g1 / g2 决定作用在哪一组。
# 拓扑操作（json 的 ops）：
#   notch  凹口：edge（A/B/C/D）、pos（沿边 0–1）、width、depth。深度可到对面墙前 WALL（深过一半就是 U 形）。手柄 = 凹口中心（底边中点，按第 1 层矩形）。
#   court  庭院：pos_u / pos_v（中心在矩形上的比例坐标）、width（沿 L）、depth（沿 W）。手柄 = 庭院中心（按第 1 层矩形）。
# 周界 = 外圈（逆时针，外法线向外）+ 每个庭院一个内圈（顺时针，"外法线"朝天井）；内圈的墙段命名 Y1–Y4。
# 手柄：Rhino「Handles」图层上名为 op.id 的点。谁后动谁算数：op.at（页面）与 handle.at（Rhino）比时间戳。
# 遮阳装置：机构库四个条目（pivot / bifoldV / bifoldH / umbrella），参数卡在 json 的 shading；沿每层每段墙排布，每段写回 dev。
#   面状类 {kind:'areal', screen, screenDay, view, units}；横轴折板 {kind:'knee', c, fA, gapH, D, tS, tD, …}。
# 写回 results.segments 是扁平列表，每项带 floor；窗条网格与它一一对应、顺序相同（日照写回脚本按序归到段）。
# GH 只写 handle / results / updated_by / updated_at；其余字段原样保留。
import json, os, math, datetime
import Rhino
import Rhino.Geometry as rg
import scriptcontext as sc

TOL = 0.005          # m；手柄位置差小于这个值视为没动
OFF = 0.02           # 窗条面往外偏移，避免和楼板面重叠闪烁
WALL = 1.0           # m；庭院离外墙、凹口离对面墙至少留这么厚
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


# ---------------- 楼层组 ----------------
def group_list(b):
    """楼层组列表 [{n, setback{A,B,C,D}, floors[...]}]（2026-10-03 放开到任意组数）。
    从 F1 起按每组层数依次分配，最后一组拿剩下的楼层。兼容旧格式 {podium, setback}。"""
    N = int(b["floors"]); g = b.get("groups") or {}
    lst = g.get("list")
    if not isinstance(lst, list) or not lst:
        podium = int(g.get("podium", N))
        lst = [{"n": podium, "setback": {}}, {"n": max(0, N - podium), "setback": g.get("setback") or {}}] if 0 <= podium < N else [{"n": N, "setback": {}}]
    out, used = [], 0
    for k, gr in enumerate(lst):
        n = max(0, N - used) if k == len(lst) - 1 else max(0, min(int((gr or {}).get("n", 0)), N - used))
        out.append({"n": n, "setback": dict((gr or {}).get("setback") or {}), "floors": list(range(used + 1, used + n + 1))})
        used += n
    return out


def floor_rect(b, i):
    """第 i 层（0 起）的外矩形 (x0, y0, x1, y1) 和组号（1 起）：每组四边各自从基底向内退 setback"""
    L, W = float(b["L"]), float(b["W"])
    k, sb = 1, {}
    for gi, gr in enumerate(group_list(b)):
        if (i + 1) in gr["floors"]:
            k, sb = gi + 1, gr["setback"]; break
    x0, y0 = float(sb.get("D", 0) or 0), float(sb.get("A", 0) or 0)
    x1, y1 = L - float(sb.get("B", 0) or 0), W - float(sb.get("C", 0) or 0)
    if x1 - x0 < 2 * WALL or y1 - y0 < 2 * WALL:               # 退过头：留一个最小矩形
        cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
        x0, x1 = min(x0, cx - WALL), max(x1, cx + WALL); y0, y1 = min(y0, cy - WALL), max(y1, cy + WALL)
    return (x0, y0, x1, y1), k


def applies(op, group):
    a = op.get("apply", "all")
    return a == "all" or a == "g%d" % group


# ---------------- 周界 ----------------
def edges(rect):
    # 逆时针：A 底边 → B 右边 → C 顶边 → D 左边。每条：起点 S、方向 u、向内法线 n、长度 E、名字
    x0, y0, x1, y1 = rect
    return [((x0, y0), (1.0, 0.0), (0.0, 1.0), x1 - x0, "A"),
            ((x1, y0), (0.0, 1.0), (-1.0, 0.0), y1 - y0, "B"),
            ((x1, y1), (-1.0, 0.0), (0.0, -1.0), x1 - x0, "C"),
            ((x0, y1), (0.0, -1.0), (1.0, 0.0), y1 - y0, "D")]


def notch_limits(rect, op):
    x0, y0, x1, y1 = rect
    E = (x1 - x0) if op["edge"] in "AC" else (y1 - y0)
    dmax = max(0.0, ((y1 - y0) if op["edge"] in "AC" else (x1 - x0)) - WALL)     # 可以切到对面墙前 WALL：深过一半就是 U 形
    return E, dmax


def rects_clash(r, others):
    return any(not (r[2] <= o[0] - WALL or r[0] >= o[2] + WALL or r[3] <= o[1] - WALL or r[1] >= o[3] + WALL) for o in others)


def outer_loop(rect, notches, warnings=None, floor=0):
    """外圈：任意个凹口（2026-10-03）。先加的优先；后加的和已接受的凹口挨在 WALL 以内就忽略并写警告。
    段名：每条边从 1 编号，一个凹口占 4 个名（前段、两壁、底），多个凹口接着编——单凹口时与以前完全相同（B1…B5）。
    返回 (顶点, 边名, 接受的凹口矩形)"""
    accepted, per_edge = [], {}
    for nt in notches:
        if nt.get("width", 0) <= 0.01 or nt.get("depth", 0) <= 0.01:
            continue
        r = notch_rect(rect, nt)
        if not r:
            continue
        if rects_clash(r, accepted):
            if warnings is not None:
                warnings.append("F%d: notch %s too close to an earlier notch, ignored" % (floor, nt.get("id")))
            continue
        accepted.append(r); per_edge.setdefault(nt["edge"], []).append(nt)
    pts, names = [], []
    for S, u, n, E, name in edges(rect):
        lst = sorted(per_edge.get(name, []), key=lambda o: o["pos"])
        if not lst:
            pts.append(S); names.append(name); continue
        P = lambda t, k: (S[0] + u[0] * t + n[0] * k, S[1] + u[1] * t + n[1] * k)
        c, prev = 1, S
        for nt in lst:
            w = min(nt["width"], E); d = min(nt["depth"], notch_limits(rect, nt)[1]); cp = nt["pos"] * E
            a, b = max(0.0, cp - w / 2.0), min(E, cp + w / 2.0)
            if b - a < 0.01 or d < 0.01:
                continue
            pts.append(prev); names.append(name + str(c)); c += 1
            for q, nm in ((P(a, 0), name + str(c)), (P(a, d), name + str(c + 1)), (P(b, d), name + str(c + 2))):
                pts.append(q); names.append(nm)
            c += 3; prev = P(b, 0)
        pts.append(prev); names.append(name + str(c) if c > 1 else name)
    out_p, out_n = [], []
    m = len(pts)
    for i in range(m):
        p, q = pts[i], pts[(i + 1) % m]
        if math.hypot(q[0] - p[0], q[1] - p[1]) > 1e-6:
            out_p.append(p); out_n.append(names[i])
    return out_p, out_n, accepted


def court_rect(rect, op):
    x0, y0, x1, y1 = rect
    Lr, Wr = x1 - x0, y1 - y0
    w = min(float(op["width"]), max(0.0, Lr - 2 * WALL)); d = min(float(op["depth"]), max(0.0, Wr - 2 * WALL))
    if w < 0.5 or d < 0.5:
        return None
    cx = min(max(x0 + float(op["pos_u"]) * Lr, x0 + WALL + w / 2.0), x1 - WALL - w / 2.0)
    cy = min(max(y0 + float(op["pos_v"]) * Wr, y0 + WALL + d / 2.0), y1 - WALL - d / 2.0)
    return (cx - w / 2.0, cy - d / 2.0, cx + w / 2.0, cy + d / 2.0)


def notch_rect(rect, notch):
    if not notch or notch["depth"] <= 0.01 or notch["width"] <= 0.01:
        return None
    x0, y0, x1, y1 = rect
    E, dmax = notch_limits(rect, notch); d = min(notch["depth"], dmax); w = notch["width"]; pos = notch["pos"]
    e = notch["edge"]
    if e == "A": return (max(x0, x0 + pos * E - w / 2), y0, min(x1, x0 + pos * E + w / 2), y0 + d)
    if e == "C": return (max(x0, x1 - pos * E - w / 2), y1 - d, min(x1, x1 - pos * E + w / 2), y1)
    if e == "B": return (x1 - d, max(y0, y0 + pos * E - w / 2), x1, min(y1, y0 + pos * E + w / 2))
    return (x0, max(y0, y1 - pos * E - w / 2), x0 + d, min(y1, y1 - pos * E + w / 2))


def court_loop(rect, tag):
    """内圈：顺时针（这样 (dy, −dx) 指向天井）。边名 1 底、2 左、3 顶、4 右"""
    x0, y0, x1, y1 = rect
    return [(x1, y0), (x0, y0), (x0, y1), (x1, y1)], [tag + "1", tag + "2", tag + "3", tag + "4"]


def norm(a):
    return (a % 360.0 + 360.0) % 360.0


def segments_of(pts, names, az0, loop, floor):
    segs = []
    m = len(pts)
    for i in range(m):
        p, q = pts[i], pts[(i + 1) % m]
        dx, dy = q[0] - p[0], q[1] - p[1]
        ln = math.hypot(dx, dy)
        nx, ny = dy / ln, -dx / ln
        az = norm(math.degrees(math.atan2(nx, ny)) + az0 - 180.0)
        segs.append({"floor": floor, "edge": names[i], "loop": loop, "az": round(az, 1), "len": round(ln, 3), "p": [round(p[0], 3), round(p[1], 3)], "q": [round(q[0], 3), round(q[1], 3)]})
    return segs


def area(pts):
    s = 0.0
    for i in range(len(pts)):
        p, q = pts[i], pts[(i + 1) % len(pts)]
        s += p[0] * q[1] - q[0] * p[1]
    return abs(s) / 2.0


# ---------------- 手柄（按第 1 层矩形解释） ----------------
def find_handle(rdoc, name):
    for o in rdoc.Objects:
        if o.Name == name and isinstance(o.Geometry, rg.Point):
            return o
    return None


def ensure_handles(rdoc, ops, rect, notes):
    """2026-10-03：每条操作一个手柄点（凹口红、庭院蓝），新操作补点，删掉的操作删点"""
    import System
    ids = set(op["id"] for op in ops if op.get("type") in HANDLE_KEYS)
    for op in ops:
        if op.get("type") in HANDLE_KEYS and find_handle(rdoc, op["id"]) is None:
            attr = Rhino.DocObjects.ObjectAttributes()
            attr.Name = op["id"]
            li = rdoc.Layers.FindName("Handles")
            if li is not None:
                attr.LayerIndex = li.Index
            attr.ObjectColor = System.Drawing.Color.FromArgb(200, 40, 40) if op["type"] == "notch" else System.Drawing.Color.FromArgb(40, 90, 200)
            attr.ColorSource = Rhino.DocObjects.ObjectColorSource.ColorFromObject
            rdoc.Objects.AddPoint(params_to_point(rect, op), attr)
            notes.append("%s handle created" % op["id"])
    for o in list(rdoc.Objects):
        nm = o.Name or ""
        if isinstance(o.Geometry, rg.Point) and (nm.startswith("notch") or nm.startswith("court")) and nm not in ids:
            rdoc.Objects.Delete(o.Id, True); notes.append("%s handle removed" % nm)


def handle_to_params(pt, rect, op):
    if op["type"] == "notch":
        for S, u, n, E, name in edges(rect):
            if name == op["edge"]:
                vx, vy = pt.X - S[0], pt.Y - S[1]
                t = (vx * u[0] + vy * u[1]) / E
                d = vx * n[0] + vy * n[1]
                _, dmax = notch_limits(rect, op)
                return {"pos": round(min(max(t, 0.0), 1.0), 4), "depth": round(min(max(d, 0.0), dmax), 3)}
        return {}
    if op["type"] == "court":
        x0, y0, x1, y1 = rect
        return {"pos_u": round(min(max((pt.X - x0) / (x1 - x0), 0.0), 1.0), 4), "pos_v": round(min(max((pt.Y - y0) / (y1 - y0), 0.0), 1.0), 4)}
    return {}


def params_to_point(rect, op):
    if op["type"] == "notch":
        for S, u, n, E, name in edges(rect):
            if name == op["edge"]:
                return rg.Point3d(S[0] + u[0] * op["pos"] * E + n[0] * op["depth"], S[1] + u[1] * op["pos"] * E + n[1] * op["depth"], 0.0)
    if op["type"] == "court":
        r = court_rect(rect, op)
        if r:
            return rg.Point3d((r[0] + r[2]) / 2.0, (r[1] + r[3]) / 2.0, 0.0)
        x0, y0, x1, y1 = rect
        return rg.Point3d(x0 + op["pos_u"] * (x1 - x0), y0 + op["pos_v"] * (y1 - y0), 0.0)
    return rg.Point3d(0, 0, 0)


HANDLE_KEYS = {"notch": ("pos", "depth"), "court": ("pos_u", "pos_v")}


def differs(a, b, keys, rect, op):
    x0, y0, x1, y1 = rect
    for k in keys:
        if k == "pos":
            scale = (x1 - x0) if op.get("edge") in "AC" else (y1 - y0)
        elif k == "pos_u":
            scale = x1 - x0
        elif k == "pos_v":
            scale = y1 - y0
        else:
            scale = 1.0
        if abs(float(a.get(k, 0)) - float(b.get(k, 0))) * scale > TOL:
            return True
    return False


# ---------------- 遮阳装置（机构库） ----------------
def rng_(seed):
    x = (seed * 1103515245 + 12345) & 0x7fffffff
    while True:
        x = (x * 1103515245 + 12345) & 0x7fffffff
        yield (x >> 8) / float(1 << 23)


def _frame(seg):
    p, q, ln = seg["p"], seg["q"], seg["len"]
    dx, dy = q[0] - p[0], q[1] - p[1]
    return p, (dx / ln, dy / ln), (dy / ln, -dx / ln), ln


def _quad(A, B, z0, z1):
    m = rg.Mesh()
    m.Vertices.Add(A[0], A[1], z0); m.Vertices.Add(B[0], B[1], z0); m.Vertices.Add(B[0], B[1], z1); m.Vertices.Add(A[0], A[1], z1)
    m.Faces.AddFace(0, 1, 2, 3); m.Normals.ComputeNormals(); return m


def _perf(sh, seed):
    K = 1.0 / (1.0 + 0.75 * float(sh["skin"]) / float(sh["holeD"])) if float(sh["holeD"]) > 0 else 0.0
    lo, hi = float(sh["perfMin"]), float(sh["perfMax"])
    r = rng_(seed)
    return K, (lambda: lo + (hi - lo) * next(r))


def _areal(ln, n_units, proj, ratios, K):
    opqS = sum(proj * (1.0 - x) for x in ratios); opqD = sum(proj * (1.0 - x * K) for x in ratios)
    return {"kind": "areal", "screen": round(1.0 - opqS / ln, 4), "screenDay": round(1.0 - opqD / ln, 4), "view": round(1.0 - n_units * proj / ln, 4), "units": n_units}


NONE = {"kind": "areal", "screen": 1.0, "screenDay": 1.0, "view": 1.0, "units": 0}


def dev_bifoldV(seg, sh, z0, H, seed):
    p, (ux, uy), (nx, ny), ln = _frame(seg)
    w = float(sh["unitW"]); n_units = int(ln // w) if w > 0 else 0
    if n_units <= 0: return [], NONE
    th = math.radians(float(sh["tilt"])); cT, sT = math.cos(th), math.sin(th)
    a = w / 2.0; t = float(sh["thick"]); dst = float(sh["standoff"])
    proj = min(w, 2 * a * cT + 2 * t * sT)
    K, nxt = _perf(sh, seed); off = (ln - n_units * w) / 2.0
    meshes, ratios = [], []
    for k in range(n_units):
        ratios.append(nxt())
        sign = 1 if (sh.get("fixed", "alt") == "same" or k % 2 == 0) else -1
        s0 = off + k * w; fx = s0 if sign > 0 else s0 + w
        P = lambda u_, o_: (p[0] + ux * u_ + nx * (dst + o_), p[1] + uy * u_ + ny * (dst + o_))
        f = P(fx, 0.0); knee = P(fx + sign * a * cT, a * sT); e = P(fx + sign * 2 * a * cT, 0.0)
        meshes.append(_quad(f, knee, z0, z0 + H)); meshes.append(_quad(knee, e, z0, z0 + H))
    return meshes, _areal(ln, n_units, proj, ratios, K)


def dev_pivot(seg, sh, z0, H, seed):
    p, (ux, uy), (nx, ny), ln = _frame(seg)
    w = float(sh["unitW"]); n_units = int(ln // w) if w > 0 else 0
    if n_units <= 0: return [], NONE
    th = math.radians(float(sh["tilt"])); cT, sT = math.cos(th), math.sin(th)
    t = float(sh["thick"]); dst = float(sh["standoff"])
    proj = min(w, w * cT + t * sT)
    K, nxt = _perf(sh, seed); off = (ln - n_units * w) / 2.0
    meshes, ratios = [], []
    for k in range(n_units):
        ratios.append(nxt())
        sign = 1 if (sh.get("fixed", "alt") == "same" or k % 2 == 0) else -1
        cx = off + k * w + w / 2.0
        C = (p[0] + ux * cx + nx * dst, p[1] + uy * cx + ny * dst)
        hx, hy = (w / 2.0) * (cT * ux * sign + sT * nx), (w / 2.0) * (cT * uy * sign + sT * ny)
        A, B = (C[0] - hx, C[1] - hy), (C[0] + hx, C[1] + hy)
        if sign < 0: A, B = B, A
        meshes.append(_quad(A, B, z0, z0 + H))
    return meshes, _areal(ln, n_units, proj, ratios, K)


def dev_bifoldH(seg, sh, z0, H, seed, band):
    p, (ux, uy), (nx, ny), ln = _frame(seg)
    w = float(sh["unitW"]); n_units = int(ln // w) if w > 0 else 0
    if n_units <= 0: return [], NONE
    th = math.radians(float(sh["tilt"])); cT, sT = math.cos(th), math.sin(th)
    a = H / 2.0; dst = float(sh["standoff"])
    K, nxt = _perf(sh, seed); off = (ln - n_units * w) / 2.0
    meshes, ratios = [], []
    yk, yb = H - a * cT, H - 2 * a * cT
    for k in range(n_units):
        ratios.append(nxt())
        s0 = off + k * w
        P = lambda u_, o_: (p[0] + ux * u_ + nx * (dst + o_), p[1] + uy * u_ + ny * (dst + o_))
        A0, B0 = P(s0, 0.0), P(s0 + w, 0.0); A1, B1 = P(s0, a * sT), P(s0 + w, a * sT)
        for (a0, b0, za, a1, b1, zb) in ((A0, B0, z0 + H, A1, B1, z0 + yk), (A1, B1, z0 + yk, A0, B0, z0 + yb)):
            m = rg.Mesh()
            m.Vertices.Add(a0[0], a0[1], za); m.Vertices.Add(b0[0], b0[1], za); m.Vertices.Add(b1[0], b1[1], zb); m.Vertices.Add(a1[0], a1[1], zb)
            m.Faces.AddFace(0, 1, 2, 3); m.Normals.ComputeNormals(); meshes.append(m)
    s_, wh = band["sill"], band["winH"]
    ov = max(0.0, min(s_ + wh, H) - max(s_, yb))
    fA = min(1.0, ov / wh) if wh > 0 else 0.0
    openHead = min(yb, s_ + wh); gapH = max(0.0, yk - openHead); D = dst + a * sT
    tS = sum(ratios) / len(ratios); tD = tS * K
    c = n_units * w / ln
    return meshes, {"kind": "knee", "c": round(c, 4), "fA": round(fA, 4), "gapH": round(gapH, 3), "D": round(D, 3), "tS": round(tS, 4), "tD": round(tD, 4),
                    "screen": round(1.0 - c * fA * (1.0 - tS), 4), "screenDay": round(1.0 - c * fA * (1.0 - tD), 4), "view": round(1.0 - c * fA, 4), "units": n_units}


def _star_cover(R, r, w, wh):
    poly = []
    for i in range(12):
        t = math.pi / 2 + i * math.pi / 6; rr = R if i % 2 == 0 else r
        poly.append((rr * math.cos(t), rr * math.sin(t)))
    def inside(x, y):
        inn = False; j = 11
        for i in range(12):
            xi, yi = poly[i]; xj, yj = poly[j]
            if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi: inn = not inn
            j = i
        return inn
    NX, NY, hit = 36, 18, 0
    for j in range(NY):
        y = -wh / 2.0 + (j + 0.5) * wh / NY
        for i in range(NX):
            x = -w / 2.0 + (i + 0.5) * w / NX
            if inside(x, y): hit += 1
    return hit / float(NX * NY)


def dev_umbrella(seg, sh, z0, H, seed, band):
    p, (ux, uy), (nx, ny), ln = _frame(seg)
    w = float(sh["unitW"]); n_units = int(ln // w) if w > 0 else 0
    if n_units <= 0: return [], NONE
    th = math.radians(float(sh["tilt"])); cT, sT = math.cos(th), math.sin(th)
    dst = float(sh["standoff"]); R = w / math.sqrt(3.0); rA = R * math.cos(math.pi / 6)
    K, nxt = _perf(sh, seed); off = (ln - n_units * w) / 2.0
    zc = z0 + band["sill"] + band["winH"] / 2.0
    cover = _star_cover(R, rA * cT, w, band["winH"])
    meshes, ratios = [], []
    for k in range(n_units):
        ratios.append(nxt())
        cx = off + k * w + w / 2.0
        C = (p[0] + ux * cx + nx * dst, p[1] + uy * cx + ny * dst, zc)
        m = rg.Mesh(); m.Vertices.Add(C[0], C[1], C[2])
        for i in range(6):
            t = math.pi / 2 + i * math.pi / 3
            m.Vertices.Add(C[0] + R * math.cos(t) * ux, C[1] + R * math.cos(t) * uy, C[2] + R * math.sin(t))
        for i in range(6):
            t = math.pi / 2 + i * math.pi / 3 + math.pi / 6; rr = rA * cT
            m.Vertices.Add(C[0] + rr * math.cos(t) * ux + rA * sT * nx, C[1] + rr * math.cos(t) * uy + rA * sT * ny, C[2] + rr * math.sin(t))
        for i in range(6):
            m.Faces.AddFace(0, 1 + i, 7 + i); m.Faces.AddFace(0, 7 + i, 1 + (i + 1) % 6)
        m.Normals.ComputeNormals(); meshes.append(m)
    return meshes, _areal(ln, n_units, w * cover, ratios, K)


FACADE_KEYS = ("A", "B", "C", "D", "court")


def facade_key(seg):
    """段属于哪个立面：外圈按边名首字母（凹口壁 B2 归 B 边），庭院内墙归 court"""
    return "court" if str(seg.get("loop", "")).startswith("court") else str(seg.get("edge", "A"))[0]


def facade_setting(sh, seg):
    """2026-10-03：按立面分设。shading.facades = {A|B|C|D|court: {on, tilt}}；缺的立面 = 装、折角用 shading.tilt"""
    fc = (sh.get("facades") or {}).get(facade_key(seg)) or {}
    on = bool(fc.get("on", True))
    tilt = float(fc.get("tilt", sh.get("tilt", 45)))
    return on, tilt


def device_units(seg, sh, i_floor, z0, H, s_idx, band):
    seed = 991 + s_idx * 17 + i_floor * 101
    t = sh.get("type", "none")
    if t == "bifoldV": return dev_bifoldV(seg, sh, z0, H, seed)
    if t == "pivot": return dev_pivot(seg, sh, z0, H, seed)
    if t == "bifoldH": return dev_bifoldH(seg, sh, z0, H, seed, band)
    if t == "umbrella": return dev_umbrella(seg, sh, z0, H, seed, band)
    return [], NONE


# ---------------- 生成 ----------------
def slab_brep(pts, holes, H):
    """一层楼板实体：平面面（外圈 + 洞）再沿法线拉 H。2026-10-03 改法：Extrusion.AddInnerProfile 在外圈不从原点出发时
    （退台层）会把洞放错位置，ToBrep 报「2d curve is not inside surface domain」，顶层只画出一部分。"""
    def closed(ps):
        return rg.Polyline([rg.Point3d(q[0], q[1], 0.0) for q in ps] + [rg.Point3d(ps[0][0], ps[0][1], 0.0)]).ToNurbsCurve()
    breps = rg.Brep.CreatePlanarBreps([closed(pts)] + [closed(h) for h in holes], 0.001)
    if not breps:
        return None
    face = breps[0].Faces[0]
    n = face.NormalAt(face.Domain(0).Mid, face.Domain(1).Mid)
    return rg.Brep.CreateFromOffsetFace(face, H if n.Z > 0 else -H, 0.001, False, True)


def floor_outline(b, i, ops, warnings):
    """第 i 层：返回 (外圈顶点, 边名, 洞列表, 组号, 矩形)"""
    rect, group = floor_rect(b, i)
    notches = [o for o in ops if o.get("type") == "notch" and applies(o, group)]
    courts = [o for o in ops if o.get("type") == "court" and applies(o, group)]
    pts, names, nrects = outer_loop(rect, notches, warnings, i + 1)
    holes, hole_names, crects = [], [], []
    for ci, co in enumerate(courts):
        r = court_rect(rect, co)
        if not r:
            warnings.append("F%d: courtyard %s too small, ignored" % (i + 1, co.get("id"))); continue
        if rects_clash(r, nrects):
            warnings.append("F%d: courtyard %s overlaps a notch, ignored" % (i + 1, co.get("id"))); continue
        if rects_clash(r, crects):
            warnings.append("F%d: courtyard %s too close to an earlier courtyard, ignored" % (i + 1, co.get("id"))); continue
        crects.append(r)
        hp, hn = court_loop(r, "Y" if ci == 0 else "Y%d_" % (ci + 1))
        holes.append(hp); hole_names.append(hn)
    return pts, names, holes, hole_names, group, rect


def build(d):
    b, w = d["building"], d["windows"]
    sh = d.get("shading") or {"type": "none"}
    L, W, H, N, slab = float(b["L"]), float(b["W"]), float(b["H"]), int(b["floors"]), float(b.get("slab", 0.35))
    ops = d.get("ops") or []
    warnings = []
    winH = float(w["wwr"]) * (H - slab)
    sill = float(w["sill"])
    band = {"sill": sill, "winH": winH}
    floors, wins, meshes, faces, dev, segs_all, floor_info = [], [], [], [], [], [], []
    for i in range(N):
        pts, names, holes, hole_names, group, rect = floor_outline(b, i, ops, warnings)
        segs = segments_of(pts, names, float(b["az0"]), "outer", i + 1)
        for ci, (hp, hn) in enumerate(zip(holes, hole_names)):
            segs += segments_of(hp, hn, float(b["az0"]), "court%d" % (ci + 1), i + 1)
        fb = slab_brep(pts, holes, H)
        if fb:
            fb.Translate(rg.Vector3d(0, 0, i * H)); floors.append(fb)
        else:
            warnings.append("F%d: slab solid failed" % (i + 1))
        use_dev = sh.get("type") in ("bifoldV", "pivot", "bifoldH", "umbrella") and (sh.get("floors", "all") == "all" or i >= 1)
        for si, s in enumerate(segs):
            p, q = s["p"], s["q"]
            dx, dy = q[0] - p[0], q[1] - p[1]; ln = math.hypot(dx, dy); nx, ny = dy / ln * OFF, -dx / ln * OFF
            z0, z1 = i * H + sill, i * H + sill + winH
            if winH > 0.01:
                srf = rg.NurbsSurface.CreateFromCorners(rg.Point3d(p[0] + nx, p[1] + ny, z0), rg.Point3d(q[0] + nx, q[1] + ny, z0),
                                                        rg.Point3d(q[0] + nx, q[1] + ny, z1), rg.Point3d(p[0] + nx, p[1] + ny, z1))
                if srf: wins.append(srf)
            nc = max(1, int(round(ln)))
            m = rg.Mesh()
            zz0, zz1 = (z0, z1) if winH > 0.01 else (i * H + 0.5, i * H + 0.6)     # 没窗时给一条极窄的网格占位，保持段与网格一一对应
            for k in range(nc + 1):
                t = k / float(nc)
                m.Vertices.Add(p[0] + dx * t + nx, p[1] + dy * t + ny, zz0); m.Vertices.Add(p[0] + dx * t + nx, p[1] + dy * t + ny, zz1)
            for k in range(nc):
                m.Faces.AddFace(2 * k, 2 * k + 2, 2 * k + 3, 2 * k + 1)
            m.Normals.ComputeNormals(); m.Compact()
            meshes.append(m); faces.append(nc)
            f_on, f_tilt = facade_setting(sh, s)
            if use_dev and f_on:
                sh_f = dict(sh); sh_f["tilt"] = f_tilt            # 这一面自己的折角
                ms, tr = device_units(s, sh_f, i, i * H, H, si, band)
                dev.extend(ms); s["dev"] = tr; s["dev"]["tilt"] = f_tilt
            else:
                s["dev"] = dict(NONE)
            s["winArea"] = round(ln * winH, 3)
        segs_all += segs
        floor_info.append({"i": i + 1, "group": group, "rect": [round(v, 3) for v in rect], "area": round(area(pts) - sum(area(hp) for hp in holes), 2),
                           "perimeter": [[round(p[0], 3), round(p[1], 3)] for p in pts],
                           "holes": [[[round(p[0], 3), round(p[1], 3)] for p in hp] for hp in holes]})
    res = {"seq": int(d.get("run", {}).get("seq", 0)), "at": "", "floorsSame": False, "nSeg": len(segs_all),
           "floors": floor_info, "segments": segs_all, "winH": round(winH, 3), "warnings": warnings,
           "shading": {"type": sh.get("type", "none"), "units": sum(s["dev"]["units"] for s in segs_all),
                       "facades": {k: {"on": facade_setting(sh, {"edge": k, "loop": "court1" if k == "court" else "outer"})[0],
                                       "tilt": facade_setting(sh, {"edge": k, "loop": "court1" if k == "court" else "outer"})[1]} for k in FACADE_KEYS}},
           "groups": {"list": group_list(b), "podium": group_list(b)[0]["n"]}}
    return floors, wins, res, meshes, faces, dev


def run(path):
    st = sc.sticky
    rdoc = Rhino.RhinoDoc.ActiveDoc
    if not path or not os.path.isfile(path):
        return [], [], "no state.json at: %s" % path, [], [], "", 0.0, 6, 8, 0, [], False
    d = read(path)
    b = d["building"]; L, W = float(b["L"]), float(b["W"])
    base_rect = (0.0, 0.0, L, W)
    ops = d.get("ops") or []
    changed_file = st.get("massing_stamp") != d.get("updated_at")
    handle_moved, handle_written = False, False
    notes = []
    if changed_file:
        ensure_handles(rdoc, ops, base_rect, notes)
        stale = [hid for hid in (d.get("handle") or {}) if hid not in set(o.get("id") for o in ops)]
        for hid in stale:
            del d["handle"][hid]; handle_written = True
    for idx, op in enumerate(ops):
        if op.get("type") not in HANDLE_KEYS:
            continue
        hid = op["id"]; keys = HANDLE_KEYS[op["type"]]
        h = (d.get("handle") or {}).get(hid) or {}
        obj = find_handle(rdoc, hid)
        if obj is None:
            continue
        pt = obj.Geometry.Location
        hv = handle_to_params(pt, base_rect, op)
        ops_at, h_at = op.get("at", ""), h.get("at", "")
        if ops_at > h_at:
            target = params_to_point(base_rect, op)
            if target.DistanceTo(pt) > TOL:
                rdoc.Objects.Replace(obj.Id, target); notes.append("%s moved to page values" % hid)
            rec = dict((k, op[k]) for k in keys); rec["at"] = ops_at
            if any(h.get(k) != rec[k] for k in keys) or h_at != ops_at:
                d.setdefault("handle", {})[hid] = rec; handle_written = True
        else:
            if differs(hv, h, keys, base_rect, op):
                rec = dict(hv); rec["at"] = now()
                d.setdefault("handle", {})[hid] = rec; handle_written = True; handle_moved = True
                notes.append("%s dragged in Rhino" % hid)
            rec = (d.get("handle") or {}).get(hid)
            if rec:
                d["ops"][idx] = dict(op, **dict((k, float(rec[k])) for k in keys if k in rec))
    run_ = d.get("run", {}) if isinstance(d.get("run"), dict) else {}
    epw = os.path.join(EPW_DIR, EPW.get(run_.get("clim", "apNow"), EPW["apNow"]))
    m0, m1 = PERIOD.get(run_.get("period", "summer"), PERIOD["summer"])
    north = (float(b["az0"]) - 180.0) % 360.0
    run_sun = bool(run_.get("sun", True))          # json run.sun：False = 不跑 Ladybug（接到两个 Direct Sun Hours 的 _run）
    cached = st.get("massing_out")
    if not changed_file and not handle_moved and cached and len(cached) == 7:
        f, w_, status, meshes, faces, nseg, dev = cached
        return f, w_, status, meshes, faces, epw, north, m0, m1, nseg, dev, run_sun
    floors, wins, res, meshes, faces, dev = build(d)
    prev = st.get("massing_res")
    if handle_written or changed_file or prev != res:
        res["at"] = now()
        fresh = read(path)
        if handle_written:
            fresh["handle"] = d["handle"]
        old = fresh.get("results") or {}
        geom = lambda segs: [dict((k, v) for k, v in s.items() if k not in ("dev",)) for s in (segs or [])]
        if old.get("sun") and old.get("segments") == res["segments"] and old.get("winH") == res["winH"] and (fresh.get("run") or {}).get("period") == old["sun"].get("period"):
            res["sun"] = old["sun"]
        elif old.get("sun") and geom(old.get("segments")) == geom(res["segments"]) and old.get("winH") == res["winH"] and (fresh.get("run") or {}).get("period") == old["sun"].get("period"):
            # 2026-10-03：只换了装置、墙段几何没变 → 受晒（只和楼板有关）照用，含装置的日照小时等 Ladybug 重算
            keep = dict(old["sun"]); keep.pop("perSegment", None); keep.pop("perWindow", None); keep["stale"] = True
            res["sun"] = keep
        fresh["results"] = res
        fresh["updated_by"] = "gh"
        fresh["updated_at"] = now()
        write(path, fresh)
        st["massing_stamp"] = fresh["updated_at"]
        st["massing_res"] = dict(res, at="")
    else:
        st["massing_stamp"] = d.get("updated_at")
    opsum = " ".join("%s(%s→%s)" % (o.get("type"), o.get("id"), o.get("apply", "all")) for o in d.get("ops") or [])
    status = "seq %d | %d floors in %d groups | %d segments | %s | device %s x%d | %s" % (
        res["seq"], len(res["floors"]), len(res["groups"]["list"]), len(res["segments"]), opsum, res["shading"]["type"], res["shading"]["units"], "; ".join(notes + res["warnings"]) or "ok")
    st["massing_out"] = (floors, wins, status, meshes, faces, res["nSeg"], dev)
    return floors, wins, status, meshes, faces, epw, north, m0, m1, res["nSeg"], dev, run_sun


floors, windows, status, winMesh, winFaces, epw, north, m0, m1, nSeg, devMesh, runSun = run(path)
