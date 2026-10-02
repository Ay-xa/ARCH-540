# context_gen.py — 给 Massing_v01 的主建筑生成周边环境（只为好看，不进任何计算）。2026-10-02
# 用法：在 Rhino 的脚本编辑器（或 MCP run_python）里整段运行；也可以改下面的参数再跑，旧的环境会先清掉。
# 生成：50×50 m 地块（薄底板 + 虚线边界）、周边两层独栋住宅（双坡 / 平屋顶）、树（针叶 / 阔叶）、人。
# 图层：Context::Lot / Houses / Trees / People / Ground。主建筑仍由 Grasshopper 实时生成，不动。
import os, json, math, random
import Rhino
import Rhino.Geometry as rg
import System.Drawing as sd

# ---------------- 参数 ----------------
SEED = 7                 # 换个数字就换一版环境
LOT = 50.0               # 主地块边长 m
AREA = 260.0             # 整片环境的边长 m
LOT_PX, LOT_PY = 16.0, 24.0        # 住宅用地：沿街宽 × 进深
ROAD = 8.0               # 街道宽
EMPTY = 0.15             # 空地比例（留给树）
N_PEOPLE = 60
TREE_DENSITY = 1.0       # 1 = 默认密度

doc = globals().get("__rhino_doc__") or Rhino.RhinoDoc.ActiveDoc
rnd = random.Random(SEED)

# 主建筑中心：从 state.json 读 L、W（建筑占 0..L × 0..W）
here = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else (os.path.dirname(doc.Path) if doc and doc.Path else os.getcwd())   # 没有 __file__ 时按打开的 massing.3dm 所在文件夹找
try:
    st = json.load(open(os.path.join(here, "state.json"), encoding="utf-8"))
    L, W = float(st["building"]["L"]), float(st["building"]["W"])
except Exception:
    L, W = 30.0, 16.0
CX, CY = L / 2.0, W / 2.0

# ---------------- 图层 ----------------
def layer(name, color, parent=None):
    full = (parent + "::" + name) if parent else name
    idx = doc.Layers.FindByFullPath(full, -1)
    if idx < 0:
        ly = Rhino.DocObjects.Layer(); ly.Name = name; ly.Color = color
        if parent:
            ly.ParentLayerId = doc.Layers[doc.Layers.FindByFullPath(parent, -1)].Id
        idx = doc.Layers.Add(ly)
    return idx

root = layer("Context", sd.Color.FromArgb(200, 200, 200))
LY = {"Ground": layer("Ground", sd.Color.FromArgb(232, 232, 226), "Context"),
      "Lot": layer("Lot", sd.Color.FromArgb(214, 214, 196), "Context"),
      "Houses": layer("Houses", sd.Color.FromArgb(250, 250, 250), "Context"),
      "Trees": layer("Trees", sd.Color.FromArgb(120, 150, 110), "Context"),
      "People": layer("People", sd.Color.FromArgb(90, 90, 90), "Context")}

# 清掉上一版
for k, idx in LY.items():
    for o in list(doc.Objects.FindByLayer(doc.Layers[idx])):
        doc.Objects.Delete(o.Id, True)

def attrs(key, name=None):
    a = Rhino.DocObjects.ObjectAttributes(); a.LayerIndex = LY[key]
    if name: a.Name = name
    return a

def add(geo, key, name=None):
    a = attrs(key, name)
    if isinstance(geo, rg.Brep): return doc.Objects.AddBrep(geo, a)
    if isinstance(geo, rg.Extrusion): return doc.Objects.AddExtrusion(geo, a)
    if isinstance(geo, rg.Curve): return doc.Objects.AddCurve(geo, a)
    if isinstance(geo, rg.Mesh): return doc.Objects.AddMesh(geo, a)
    return doc.Objects.Add(geo, a)

def box(x0, y0, x1, y1, z0, z1):
    return rg.Box(rg.Plane.WorldXY, rg.Interval(x0, x1), rg.Interval(y0, y1), rg.Interval(z0, z1)).ToBrep()

# ---------------- 地面与地块 ----------------
half = AREA / 2.0
add(box(CX - half, CY - half, CX + half, CY + half, -0.25, -0.12), "Ground", "ctx_ground")
lot = (CX - LOT / 2.0, CY - LOT / 2.0, CX + LOT / 2.0, CY + LOT / 2.0)
add(box(lot[0], lot[1], lot[2], lot[3], -0.12, -0.02), "Lot", "ctx_lot")
# 虚线边界做成一段段小薄片（Arctic 等显示模式里线型看不清，实体虚线一眼就看到）
DASH, GAP, DW = 2.0, 1.2, 0.35
corners = [(lot[0], lot[1]), (lot[2], lot[1]), (lot[2], lot[3]), (lot[0], lot[3])]
for k in range(4):
    (ax, ay), (bx, by) = corners[k], corners[(k + 1) % 4]
    ln = math.hypot(bx - ax, by - ay); ux, uy = (bx - ax) / ln, (by - ay) / ln
    t = 0.0
    while t < ln:
        t1 = min(ln, t + DASH)
        x0, y0, x1, y1 = ax + ux * t, ay + uy * t, ax + ux * t1, ay + uy * t1
        if abs(ux) > 0.5: b = box(min(x0, x1), y0 - DW / 2, max(x0, x1), y0 + DW / 2, -0.02, 0.03)
        else: b = box(x0 - DW / 2, min(y0, y1), x0 + DW / 2, max(y0, y1), -0.02, 0.03)
        a = attrs("Lot", "ctx_lot_dash"); a.ColorSource = Rhino.DocObjects.ObjectColorSource.ColorFromObject; a.ObjectColor = sd.Color.FromArgb(45, 45, 45)
        doc.Objects.AddBrep(b, a)
        t = t1 + GAP

# ---------------- 房子 ----------------
def rect_overlap(r, s, gap=0.0):
    return not (r[2] <= s[0] - gap or r[0] >= s[2] + gap or r[3] <= s[1] - gap or r[1] >= s[3] + gap)

keep_out = (lot[0] - ROAD, lot[1] - ROAD, lot[2] + ROAD, lot[3] + ROAD)     # 主地块 + 一圈街道
footprints = []     # (x0,y0,x1,y1) 轴对齐包围盒，给树和人避让

def house(cx, cy, w, d, ang, eave, ridge, flat):
    # 平面 w（沿脊）× d，脊沿局部 x；eave 檐口高；ridge 脊比檐口高多少
    T = rg.Transform.Rotation(ang, rg.Vector3d.ZAxis, rg.Point3d.Origin) * rg.Transform.Identity
    T = rg.Transform.Translation(cx, cy, 0.0) * rg.Transform.Rotation(ang, rg.Vector3d.ZAxis, rg.Point3d.Origin)
    body = box(-w / 2, -d / 2, w / 2, d / 2, 0.0, eave)
    body.Transform(T); add(body, "Houses")
    if not flat:
        tri = rg.Polyline([rg.Point3d(-w / 2, -d / 2, eave), rg.Point3d(-w / 2, d / 2, eave), rg.Point3d(-w / 2, 0.0, eave + ridge), rg.Point3d(-w / 2, -d / 2, eave)]).ToNurbsCurve()
        roof = rg.Extrusion.Create(tri, w, True)      # 沿三角形所在平面的法线（x 方向）挤出
        if roof:
            rb = roof.ToBrep()
            # Extrusion.Create 的方向可能朝 -x，拉到 x ∈ [-w/2, w/2]
            bb = rb.GetBoundingBox(True)
            rb.Transform(rg.Transform.Translation(-w / 2 - bb.Min.X, 0, 0))
            rb.Transform(T); add(rb, "Houses")
    else:
        cap = box(-w / 2 + 0.3, -d / 2 + 0.3, w / 2 - 0.3, d / 2 - 0.3, eave, eave + 0.6)
        cap.Transform(T); add(cap, "Houses")

# 街区网格：x 方向每 6 块地一条路，y 方向每 2 排（背靠背）一条路
blk_x = 6 * LOT_PX + ROAD; blk_y = 2 * LOT_PY + ROAD
nbx = int(AREA / blk_x) + 2; nby = int(AREA / blk_y) + 2
ox = CX - half - rnd.uniform(0, blk_x); oy = CY - half - rnd.uniform(0, blk_y)
n_house = 0
for bi in range(nbx):
    for bj in range(nby):
        bx0 = ox + bi * blk_x + ROAD; by0 = oy + bj * blk_y + ROAD
        for li in range(6):
            for row in range(2):
                x0 = bx0 + li * LOT_PX; y0 = by0 + row * LOT_PY
                cell = (x0, y0, x0 + LOT_PX, y0 + LOT_PY)
                if cell[2] < CX - half or cell[0] > CX + half or cell[3] < CY - half or cell[1] > CY + half:
                    continue
                if rect_overlap(cell, keep_out):
                    continue
                if rnd.random() < EMPTY:
                    continue
                # 房子朝街：row 0 的街在 y 小的一侧，row 1 在 y 大的一侧
                w = rnd.uniform(8.0, 12.0); d = rnd.uniform(9.0, 13.0)
                along = rnd.random() < 0.6          # 脊平行于街（沿 x）
                fw, fd = (w, d) if along else (d, w)
                fw = min(fw, LOT_PX - 3.0); fd = min(fd, LOT_PY - 6.0)
                cx = x0 + LOT_PX / 2 + rnd.uniform(-0.6, 0.6)
                front = 4.0 + rnd.uniform(0, 2.0)
                cy = (y0 + front + fd / 2) if row == 0 else (y0 + LOT_PY - front - fd / 2)
                ang = (0.0 if along else math.pi / 2) + rnd.uniform(-0.03, 0.03)
                eave = rnd.uniform(5.6, 6.8); flat = rnd.random() < 0.2
                house(cx, cy, w if along else d, d if along else w, ang, eave, rnd.uniform(2.2, 3.4), flat)
                footprints.append((cx - fw / 2 - 1.5, cy - fd / 2 - 1.5, cx + fw / 2 + 1.5, cy + fd / 2 + 1.5))
                n_house += 1

# ---------------- 树 ----------------
def tree(x, y, conifer):
    if conifer:
        h = rnd.uniform(6.0, 11.0); r = rnd.uniform(1.4, 2.4); trunk = rnd.uniform(1.0, 1.8)
        add(rg.Cylinder(rg.Circle(rg.Plane(rg.Point3d(x, y, 0), rg.Vector3d.ZAxis), 0.18), trunk).ToBrep(True, True), "Trees")
        cone = rg.Cone(rg.Plane(rg.Point3d(x, y, trunk + h), rg.Vector3d.ZAxis), -h, r)       # 顶点在上，向下张开
        add(cone.ToBrep(True), "Trees")
    else:
        trunk = rnd.uniform(2.0, 3.2); r = rnd.uniform(2.0, 3.2)
        add(rg.Cylinder(rg.Circle(rg.Plane(rg.Point3d(x, y, 0), rg.Vector3d.ZAxis), 0.2), trunk).ToBrep(True, True), "Trees")
        add(rg.Sphere(rg.Point3d(x, y, trunk + r * 0.8), r).ToBrep(), "Trees")

main_fp = (-4.0, -4.0, L + 4.0, W + 4.0)      # 主建筑 + 4 m
def free(x, y, gap=2.5):
    if rect_overlap((x, y, x, y), main_fp): return False
    for f in footprints:
        if rect_overlap((x, y, x, y), f, gap): return False
    return True

n_tree = 0
# 地块里：建筑四周
for _ in range(int(34 * TREE_DENSITY)):
    for _try in range(20):
        x = rnd.uniform(lot[0] + 2, lot[2] - 2); y = rnd.uniform(lot[1] + 2, lot[3] - 2)
        if free(x, y): tree(x, y, rnd.random() < 0.65); n_tree += 1; break
# 周边：按面积撒
for _ in range(int(AREA * AREA / 380 * TREE_DENSITY)):
    for _try in range(25):
        x = rnd.uniform(CX - half + 2, CX + half - 2); y = rnd.uniform(CY - half + 2, CY + half - 2)
        if rect_overlap((x, y, x, y), lot): continue
        if free(x, y): tree(x, y, rnd.random() < 0.65); n_tree += 1; break

# ---------------- 人 ----------------
def person(x, y):
    ang = rnd.uniform(0, math.pi)
    body = rg.Cylinder(rg.Circle(rg.Plane(rg.Point3d(x, y, 0), rg.Vector3d.ZAxis), 0.22), 1.25).ToBrep(True, True)
    add(body, "People")
    add(rg.Sphere(rg.Point3d(x, y, 1.5), 0.16).ToBrep(), "People")

n_people = 0
for _ in range(N_PEOPLE):
    for _try in range(20):
        if rnd.random() < 0.6:
            x = rnd.uniform(lot[0] + 1, lot[2] - 1); y = rnd.uniform(lot[1] + 1, lot[3] - 1)
        else:
            x = rnd.uniform(lot[0] - 30, lot[2] + 30); y = rnd.uniform(lot[1] - 30, lot[3] + 30)
        if free(x, y, 1.0): person(x, y); n_people += 1; break

doc.Views.Redraw()
print("context: %d houses, %d trees, %d people; lot %.0f m centred on (%.1f, %.1f)" % (n_house, n_tree, n_people, LOT, CX, CY))
