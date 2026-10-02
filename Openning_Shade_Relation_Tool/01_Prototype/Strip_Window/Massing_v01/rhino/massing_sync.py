# massing_sync.py — Grasshopper「Python 3 Script」组件「massing sync」的源码（Massing_v01，PLAN_massing_v01 §4）
# 由 Trigger 每 0.5 s 触发。输入：path（state.json 路径）。
# 输出：floors（楼板 Brep）、windows（窗条面）、status（文字）；给 Ladybug 的 winMesh（每扇窗条一个网格，沿长度分格）、winFaces（每个网格的面数）、
#       epw（气象文件路径）、north（Ladybug 的 north_：+Y 到北的逆时针角度）、m0 / m1（分析期起止月）、nSeg（立面段数）、
#       devMesh（遮阳装置的面片，给预览和 Direct Sun Hours 的 context）。
# 拓扑操作（json 的 ops，都从 F1 向上传播、三层同形）：
#   notch  凹口：edge（A/B/C/D）、pos（沿边 0–1）、width、depth。手柄 = 凹口中心（底边中点）。
#   court  庭院：pos_u / pos_v（中心在平面上的比例坐标）、width（沿 L）、depth（沿 W）。手柄 = 庭院中心。
# 周界 = 外圈（逆时针，外法线向外）+ 每个庭院一个内圈（顺时针，"外法线"朝天井）；内圈的墙段命名 Y1–Y4。
# 手柄：Rhino「Handles」图层上名为 op.id 的点。谁后动谁算数：op.at（页面）与 handle.at（Rhino）比时间戳。
# 遮阳装置（第二刀）：机构库四个条目（pivot 中轴转动板 / bifoldV 竖轴膝盖折板 / bifoldH 横轴膝盖折板 / umbrella 伞式六角折板），参数卡在 json 的 shading；
# 沿每段墙排布（含庭院内墙），每段写回 dev：面状类 {kind:'areal', screen, screenDay, view, units}；
# 横轴折板 {kind:'knee', c 盖住的长度比, fA 盖住的窗条高度比, gapH 膝盖到开口顶, D 挑檐深, tS/tD 透光}（页面把窗拆成屏后 / 挑檐下 / 无遮三部分交给引擎）。
# 规则与 Strip Window 页面相同：投影、逐板随机穿孔、漫射光孔壁因子 K = 1/(1+0.75·孔深/孔径)、六角星覆盖率采样。
# GH 只写 handle / results / updated_by / updated_at；其余字段原样保留。
import json, os, math, datetime
import Rhino
import Rhino.Geometry as rg
import scriptcontext as sc

TOL = 0.005          # m；手柄位置差小于这个值视为没动
OFF = 0.02           # 窗条面往外偏移，避免和楼板面重叠闪烁
WALL = 1.0           # m；庭院离外墙至少留这么厚
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


# ---------------- 周界 ----------------
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


def outer_loop(L, W, notch):
    """外圈：矩形减凹口。返回 (顶点, 边名)；第 i 条边从 pts[i] 到 pts[(i+1)%n]"""
    pts, names = [], []
    for S, u, n, E, name in edges(L, W):
        if notch and notch["edge"] == name and notch["width"] > 0.01 and notch["depth"] > 0.01:
            w = min(notch["width"], E)
            d = min(notch["depth"], notch_limits(L, W, notch)[1])
            c = notch["pos"] * E
            a, b = max(0.0, c - w / 2.0), min(E, c + w / 2.0)
            if b - a < 0.01:
                pts.append(S); names.append(name); continue
            P = lambda t, k: (S[0] + u[0] * t + n[0] * k, S[1] + u[1] * t + n[1] * k)
            for p, nm in ((S, name + "1"), (P(a, 0), name + "2"), (P(a, d), name + "3"), (P(b, d), name + "4"), (P(b, 0), name + "5")):
                pts.append(p); names.append(nm)
        else:
            pts.append(S); names.append(name)
    out_p, out_n = [], []
    m = len(pts)
    for i in range(m):
        p, q = pts[i], pts[(i + 1) % m]
        if math.hypot(q[0] - p[0], q[1] - p[1]) > 1e-6:
            out_p.append(p); out_n.append(names[i])
    return out_p, out_n


def court_rect(L, W, op):
    """庭院矩形（已夹到外墙以内 WALL）。返回 (x0, y0, x1, y1) 或 None"""
    w = min(float(op["width"]), max(0.0, L - 2 * WALL)); d = min(float(op["depth"]), max(0.0, W - 2 * WALL))
    if w < 0.5 or d < 0.5:
        return None
    cx = min(max(float(op["pos_u"]) * L, WALL + w / 2.0), L - WALL - w / 2.0)
    cy = min(max(float(op["pos_v"]) * W, WALL + d / 2.0), W - WALL - d / 2.0)
    return (cx - w / 2.0, cy - d / 2.0, cx + w / 2.0, cy + d / 2.0)


def notch_rect(L, W, notch):
    if not notch or notch["depth"] <= 0.01 or notch["width"] <= 0.01:
        return None
    e, pos, w, d = notch["edge"], notch["pos"], notch["width"], notch["depth"]
    if e == "A": return (max(0, pos * L - w / 2), 0, min(L, pos * L + w / 2), d)
    if e == "C": return (max(0, L - pos * L - w / 2), W - d, min(L, L - pos * L + w / 2), W)
    if e == "B": return (L - d, max(0, pos * W - w / 2), L, min(W, pos * W + w / 2))
    return (0, max(0, W - pos * W - w / 2), d, min(W, W - pos * W + w / 2))


def court_loop(rect, tag):
    """内圈：顺时针（这样 (dy, −dx) 指向天井，即这些墙的"室外"方向）。边名 1 底、2 左、3 顶、4 右"""
    x0, y0, x1, y1 = rect
    pts = [(x1, y0), (x0, y0), (x0, y1), (x1, y1)]
    return pts, [tag + "1", tag + "2", tag + "3", tag + "4"]


def norm(a):
    return (a % 360.0 + 360.0) % 360.0


def segments_of(pts, names, az0, loop):
    segs = []
    m = len(pts)
    for i in range(m):
        p, q = pts[i], pts[(i + 1) % m]
        dx, dy = q[0] - p[0], q[1] - p[1]
        ln = math.hypot(dx, dy)
        nx, ny = dy / ln, -dx / ln                       # 逆时针外圈：外法线；顺时针内圈：朝天井
        az = norm(math.degrees(math.atan2(nx, ny)) + az0 - 180.0)   # A 边(外法线 −Y)朝向 = az0
        segs.append({"edge": names[i], "loop": loop, "az": round(az, 1), "len": round(ln, 3), "p": [round(p[0], 3), round(p[1], 3)], "q": [round(q[0], 3), round(q[1], 3)]})
    return segs


def area(pts):
    s = 0.0
    for i in range(len(pts)):
        p, q = pts[i], pts[(i + 1) % len(pts)]
        s += p[0] * q[1] - q[0] * p[1]
    return abs(s) / 2.0


# ---------------- 手柄 ----------------
def find_handle(rdoc, name):
    for o in rdoc.Objects:
        if o.Name == name and isinstance(o.Geometry, rg.Point):
            return o
    return None


def handle_to_params(pt, L, W, op):
    """Rhino 点 → 操作参数（只含手柄控制的那几项）"""
    if op["type"] == "notch":
        for S, u, n, E, name in edges(L, W):
            if name == op["edge"]:
                vx, vy = pt.X - S[0], pt.Y - S[1]
                t = (vx * u[0] + vy * u[1]) / E
                d = vx * n[0] + vy * n[1]
                _, dmax = notch_limits(L, W, op)
                return {"pos": round(min(max(t, 0.0), 1.0), 4), "depth": round(min(max(d, 0.0), dmax), 3)}
        return {}
    if op["type"] == "court":
        return {"pos_u": round(min(max(pt.X / L, 0.0), 1.0), 4), "pos_v": round(min(max(pt.Y / W, 0.0), 1.0), 4)}
    return {}


def params_to_point(L, W, op):
    if op["type"] == "notch":
        for S, u, n, E, name in edges(L, W):
            if name == op["edge"]:
                return rg.Point3d(S[0] + u[0] * op["pos"] * E + n[0] * op["depth"], S[1] + u[1] * op["pos"] * E + n[1] * op["depth"], 0.0)
    if op["type"] == "court":
        r = court_rect(L, W, op)
        if r:
            return rg.Point3d((r[0] + r[2]) / 2.0, (r[1] + r[3]) / 2.0, 0.0)
        return rg.Point3d(op["pos_u"] * L, op["pos_v"] * W, 0.0)
    return rg.Point3d(0, 0, 0)


HANDLE_KEYS = {"notch": ("pos", "depth"), "court": ("pos_u", "pos_v")}


def differs(a, b, keys, L, W, op):
    for k in keys:
        if k == "pos":
            scale = L if op.get("edge") in "AC" else W
        elif k == "pos_u":
            scale = L
        elif k == "pos_v":
            scale = W
        else:
            scale = 1.0
        if abs(float(a.get(k, 0)) - float(b.get(k, 0))) * scale > TOL:
            return True
    return False


# ---------------- 遮阳装置 ----------------
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
    """竖向四边形面片：A→B 沿墙，z0→z1 向上。顶点顺序使法线 = (B−A) × z"""
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
    """#1 膝盖式折板·竖轴：两片等长，一端固定一端滑，折线向外凸"""
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
    """#0 中轴转动板：一片板绕自己的竖向中轴转一个倾角，相邻板正负交替"""
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
    """#2 膝盖式折板·横轴：顶边固定、底边上滑，膝盖向外凸。上部窗条按面状挡，膝盖以下的窗条在穿孔挑檐下"""
    p, (ux, uy), (nx, ny), ln = _frame(seg)
    w = float(sh["unitW"]); n_units = int(ln // w) if w > 0 else 0
    if n_units <= 0: return [], NONE
    th = math.radians(float(sh["tilt"])); cT, sT = math.cos(th), math.sin(th)
    a = H / 2.0; dst = float(sh["standoff"])
    K, nxt = _perf(sh, seed); off = (ln - n_units * w) / 2.0
    meshes, ratios = [], []
    yk, yb = H - a * cT, H - 2 * a * cT                         # 膝盖高、板底高（相对本层楼板顶）
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
    """六角星（外半径 R、内半径 r，尖角朝上）在 w × wh 的窗条矩形内的覆盖率，采样"""
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
    """#3 伞式六角折板：角点固定，折痕外端向外凸、向中心收，覆盖面积随 cos 折角缩小"""
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


def device_units(seg, sh, i_floor, z0, H, s_idx, band):
    """按参数卡的 type 分派到机构库条目。返回 (面片列表, 翻译 dict)"""
    seed = 991 + s_idx * 17 + i_floor * 101
    t = sh.get("type", "none")
    if t == "bifoldV": return dev_bifoldV(seg, sh, z0, H, seed)
    if t == "pivot": return dev_pivot(seg, sh, z0, H, seed)
    if t == "bifoldH": return dev_bifoldH(seg, sh, z0, H, seed, band)
    if t == "umbrella": return dev_umbrella(seg, sh, z0, H, seed, band)
    return [], NONE


# ---------------- 生成 ----------------
def build(d):
    b, w = d["building"], d["windows"]
    sh = d.get("shading") or {"type": "none"}
    L, W, H, N, slab = float(b["L"]), float(b["W"]), float(b["H"]), int(b["floors"]), float(b.get("slab", 0.35))
    ops = d.get("ops") or []
    notch = next((o for o in ops if o.get("type") == "notch"), None)
    courts = [o for o in ops if o.get("type") == "court"]
    warnings = []
    pts, names = outer_loop(L, W, notch)
    segs = segments_of(pts, names, float(b["az0"]), "outer")
    holes = []
    nr = notch_rect(L, W, notch)
    for ci, co in enumerate(courts):
        r = court_rect(L, W, co)
        if not r:
            warnings.append("courtyard %s too small, ignored" % co.get("id")); continue
        if nr and not (r[2] <= nr[0] - WALL or r[0] >= nr[2] + WALL or r[3] <= nr[1] - WALL or r[1] >= nr[3] + WALL):
            warnings.append("courtyard %s overlaps the notch, ignored" % co.get("id")); continue   # 简化：庭院与凹口不能挨着
        hp, hn = court_loop(r, "Y" if ci == 0 else "Y%d_" % (ci + 1))
        holes.append(hp)
        segs += segments_of(hp, hn, float(b["az0"]), "court%d" % (ci + 1))
    winH = float(w["wwr"]) * (H - slab)
    sill = float(w["sill"])
    floors, wins, meshes, faces, dev = [], [], [], [], []
    dev_tr = [None] * len(segs)
    poly = rg.Polyline([rg.Point3d(p[0], p[1], 0.0) for p in pts] + [rg.Point3d(pts[0][0], pts[0][1], 0.0)])
    hole_polys = [rg.Polyline([rg.Point3d(p[0], p[1], 0.0) for p in hp] + [rg.Point3d(hp[0][0], hp[0][1], 0.0)]) for hp in holes]
    plate_area = area(pts) - sum(area(hp) for hp in holes)
    # 楼板实体只在 z=0 做一次（AddInnerProfile 只认轮廓平面上的曲线），再逐层平移；否则 2 层以上的庭院洞会丢
    base_ext = rg.Extrusion.Create(poly.ToNurbsCurve(), H, True)
    if base_ext:
        for hp in hole_polys:
            base_ext.AddInnerProfile(hp.ToNurbsCurve())
    for i in range(N):
        if base_ext:
            fb = base_ext.ToBrep(); fb.Translate(rg.Vector3d(0, 0, i * H)); floors.append(fb)
        if winH > 0.01:
            for s in segs:
                p, q = s["p"], s["q"]
                dx, dy = q[0] - p[0], q[1] - p[1]; ln = math.hypot(dx, dy); nx, ny = dy / ln * OFF, -dx / ln * OFF
                z0, z1 = i * H + sill, i * H + sill + winH
                srf = rg.NurbsSurface.CreateFromCorners(rg.Point3d(p[0] + nx, p[1] + ny, z0), rg.Point3d(q[0] + nx, q[1] + ny, z0),
                                                        rg.Point3d(q[0] + nx, q[1] + ny, z1), rg.Point3d(p[0] + nx, p[1] + ny, z1))
                if srf: wins.append(srf)
                nc = max(1, int(round(ln)))
                m = rg.Mesh()
                for k in range(nc + 1):
                    t = k / float(nc)
                    m.Vertices.Add(p[0] + dx * t + nx, p[1] + dy * t + ny, z0); m.Vertices.Add(p[0] + dx * t + nx, p[1] + dy * t + ny, z1)
                for k in range(nc):
                    m.Faces.AddFace(2 * k, 2 * k + 2, 2 * k + 3, 2 * k + 1)
                m.Normals.ComputeNormals(); m.Compact()
                meshes.append(m); faces.append(nc)
        if sh.get("type") in ("bifoldV", "pivot", "bifoldH", "umbrella") and (sh.get("floors", "all") == "all" or i >= 1):
            for si, s in enumerate(segs):
                ms, tr = device_units(s, sh, i, i * H, H, si, {"sill": sill, "winH": winH})
                dev.extend(ms)
                if dev_tr[si] is None:
                    dev_tr[si] = tr
    for si, s in enumerate(segs):
        s["winArea"] = round(s["len"] * winH, 3)
        s["dev"] = dev_tr[si] if dev_tr[si] else dict(NONE)
    res = {"seq": int(d.get("run", {}).get("seq", 0)), "at": "", "floorsSame": True, "nSeg": len(segs),
           "floors": [{"i": i + 1, "area": round(plate_area, 2)} for i in range(N)],
           "perimeter": [[round(p[0], 3), round(p[1], 3)] for p in pts],
           "holes": [[[round(p[0], 3), round(p[1], 3)] for p in hp] for hp in holes],
           "segments": segs, "winH": round(winH, 3), "warnings": warnings,
           "shading": {"type": sh.get("type", "none"), "units": sum(x["units"] for x in dev_tr if x)}}
    if notch and notch["width"] > min(L, W):
        res["warnings"].append("notch width clipped to the edge length")
    return floors, wins, res, meshes, faces, dev


def run(path):
    st = sc.sticky
    rdoc = Rhino.RhinoDoc.ActiveDoc
    if not path or not os.path.isfile(path):
        return [], [], "no state.json at: %s" % path, [], [], "", 0.0, 6, 8, 0, []
    d = read(path)
    b = d["building"]; L, W = float(b["L"]), float(b["W"])
    ops = d.get("ops") or []
    changed_file = st.get("massing_stamp") != d.get("updated_at")
    handle_moved, handle_written = False, False
    notes = []
    for idx, op in enumerate(ops):
        if op.get("type") not in HANDLE_KEYS:
            continue
        hid = op["id"]; keys = HANDLE_KEYS[op["type"]]
        h = (d.get("handle") or {}).get(hid) or {}
        obj = find_handle(rdoc, hid)
        if obj is None:
            continue
        pt = obj.Geometry.Location
        hv = handle_to_params(pt, L, W, op)
        ops_at, h_at = op.get("at", ""), h.get("at", "")
        if ops_at > h_at:
            target = params_to_point(L, W, op)
            if target.DistanceTo(pt) > TOL:
                rdoc.Objects.Replace(obj.Id, target); notes.append("%s moved to page values" % hid)
            rec = dict((k, op[k]) for k in keys); rec["at"] = ops_at
            if any(h.get(k) != rec[k] for k in keys) or h_at != ops_at:
                d.setdefault("handle", {})[hid] = rec; handle_written = True
        else:
            if differs(hv, h, keys, L, W, op):
                rec = dict(hv); rec["at"] = now()
                d.setdefault("handle", {})[hid] = rec; handle_written = True; handle_moved = True
                notes.append("%s dragged in Rhino" % hid)
            rec = (d.get("handle") or {}).get(hid)
            if rec:
                d["ops"][idx] = dict(op, **dict((k, float(rec[k])) for k in keys if k in rec))   # 只在内存里用，不写回 ops
    run_ = d.get("run", {}) if isinstance(d.get("run"), dict) else {}
    epw = os.path.join(EPW_DIR, EPW.get(run_.get("clim", "apNow"), EPW["apNow"]))
    m0, m1 = PERIOD.get(run_.get("period", "summer"), PERIOD["summer"])
    north = (float(b["az0"]) - 180.0) % 360.0
    cached = st.get("massing_out")
    if not changed_file and not handle_moved and cached and len(cached) == 7:
        f, w_, status, meshes, faces, nseg, dev = cached
        return f, w_, status, meshes, faces, epw, north, m0, m1, nseg, dev
    floors, wins, res, meshes, faces, dev = build(d)
    prev = st.get("massing_res")
    if handle_written or changed_file or prev != res:
        res["at"] = now()
        fresh = read(path)
        if handle_written:
            fresh["handle"] = d["handle"]
        old = fresh.get("results") or {}
        if old.get("sun") and old.get("segments") == res["segments"] and old.get("winH") == res["winH"] and (fresh.get("run") or {}).get("period") == old["sun"].get("period"):
            res["sun"] = old["sun"]
        fresh["results"] = res
        fresh["updated_by"] = "gh"
        fresh["updated_at"] = now()
        write(path, fresh)
        st["massing_stamp"] = fresh["updated_at"]
        st["massing_res"] = dict(res, at="")
    else:
        st["massing_stamp"] = d.get("updated_at")
    opsum = " ".join("%s(%s)" % (o.get("type"), o.get("id")) for o in d.get("ops") or [])
    status = "seq %d | %d floors | %d segments | %s | holes %d | device %s x%d | %s" % (
        res["seq"], len(res["floors"]), len(res["segments"]), opsum, len(res["holes"]), res["shading"]["type"], res["shading"]["units"], "; ".join(notes) or "ok")
    st["massing_out"] = (floors, wins, status, meshes, faces, res["nSeg"], dev)
    return floors, wins, status, meshes, faces, epw, north, m0, m1, res["nSeg"], dev


floors, windows, status, winMesh, winFaces, epw, north, m0, m1, nSeg, devMesh = run(path)
