# massing_rad.py — Grasshopper「Python 3 Script」组件「massing sun」的源码（Massing_v01 第 7 步，2026-10-03 加自遮挡）
# 第一刀的 Ladybug 指标 = 直射日照小时（LB Direct Sun Hours，不需要 Radiance）；入射辐射要装 Radiance 以后再接。
# 输入：path（state.json）、results（LB Direct Sun Hours 的逐面结果 h，遮挡 = 楼板 + 遮阳装置，与 winMesh 的面顺序一致）、
#       resMass（第二个 LB Direct Sun Hours：遮挡只有楼板，没有装置）、vecs（LB SunPath 的太阳向量，从太阳指向地面，只含地平线以上）、
#       faces（每扇窗条的面数）、nSeg（立面段数）。分析期名从 json 的 run.period 读。输出：status。
# 做的事：
#   1. 按面数把两组结果归到每扇窗条，再按「窗序号 % 段数」归到立面段（现在窗与段一一对应）。
#   2. 自由墙面的日照小时 = 太阳向量里「照得到这段墙外法线」的个数（每个向量 = 1/timestep 小时，这里 timestep = 1）。
#   3. 受晒比例 expo = 只有楼板遮挡的小时 ÷ 自由墙面的小时，写进 results.sun.expo，页面交给引擎 seg.expo 折减直射。
#   写回 results.sun = {period, unit, perSegment, massOnly, free, expo, perWindow, at}。
import json, os, math, datetime
import scriptcontext as sc


def now():
    return datetime.datetime.now().isoformat(timespec="milliseconds")


def resolve_state_path(p):
    """2026-10-02 让 gh 文件搬到别的电脑也能用：path 面板留空或写相对名（如 state.json）时，
    按 massing.gh 自己所在的文件夹找；写了存在的绝对路径就照用。"""
    p = (p or "").strip() if isinstance(p, str) else ""
    if p and os.path.isabs(p) and os.path.isfile(p):
        return p
    try:
        base = os.path.dirname(ghenv.Component.OnPingDocument().FilePath)
    except Exception:
        base = ""
    return os.path.join(base, p or "state.json") if base else p


def per_segment(results, cnt, n):
    vals = [float(v) for v in (results or []) if v is not None]
    if not vals or not cnt or sum(cnt) != len(vals) or not n:
        return None, None
    per_win, i = [], 0
    for c in cnt:
        chunk = vals[i:i + c]; i += c
        per_win.append(sum(chunk) / len(chunk))
    seg = [[] for _ in range(n)]
    for k, v in enumerate(per_win):
        seg[k % n].append(v)
    return [round(sum(x) / len(x), 1) if x else None for x in seg], [round(v, 1) for v in per_win]


def free_hours(segments, vecs):
    # 每段墙的外法线（模型坐标，与 massing_sync.segments_of 同一规则）；太阳向量已按 north_ 转到模型坐标
    out = []
    vs = [(float(v.X), float(v.Y), float(v.Z)) for v in (vecs or [])]
    for s in segments:
        p, q = s["p"], s["q"]
        dx, dy = q[0] - p[0], q[1] - p[1]
        ln = math.hypot(dx, dy)
        if ln < 1e-9:
            out.append(None); continue
        nx, ny = dy / ln, -dx / ln
        out.append(float(sum(1 for v in vs if nx * v[0] + ny * v[1] < 0.0)))
    return out


def main(path, results, resMass, vecs, faces, nSeg):
    path = resolve_state_path(path)
    if not path or not os.path.isfile(path):
        return "no state.json"
    cnt = [int(c) for c in (faces or [])]
    n = int(nSeg) if nSeg else 0
    rad, per_win = per_segment(results, cnt, n)
    if rad is None:
        return "waiting: %d values, %d faces" % (len(results or []), sum(cnt) if cnt else 0)
    mass, _ = per_segment(resMass, cnt, n)
    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)
    own = sc.sticky.get("massing_stamp") == d.get("updated_at")     # 读到的还是 massing sync 自己最后写的那版？
    period = (d.get("run") or {}).get("period", "summer")
    segs = (d.get("results") or {}).get("segments") or []
    free = free_hours(segs, vecs) if (mass is not None and len(segs) == n and vecs) else None
    expo = None
    if free is not None:
        expo = [None if (m is None or fr is None or fr <= 0) else round(min(1.0, m / fr), 3) for m, fr in zip(mass, free)]
    key = (tuple(rad), tuple(mass) if mass else None, tuple(expo) if expo else None, str(period))
    cur = (d.get("results") or {}).get("sun") or {}
    if sc.sticky.get("massing_sun_key") == key and cur and not cur.get("stale") and cur.get("perSegment"):
        return "sun hours unchanged"

    sun = {"period": str(period), "unit": "h", "perSegment": rad, "perWindow": per_win, "at": now()}
    if mass is not None:
        sun["massOnly"] = mass
    if expo is not None:
        sun["free"] = free; sun["expo"] = expo
    d.setdefault("results", {})["sun"] = sun
    d["updated_by"] = "gh"; d["updated_at"] = now()
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)
    sc.sticky["massing_sun_key"] = key
    if own:
        sc.sticky["massing_stamp"] = d["updated_at"]    # 让 massing sync 知道这次写入是自己人，不必重算
    # 2026-10-02 修：如果页面在 sync 算完之后、日照写回之前又改了参数（Ladybug 跑几秒到几十秒），
    # 就不接管时间戳——让 massing sync 看到文件变了去重算，否则页面那次修改会被吞掉（首层退台改回 0 却没重建）。
    msg = "sun hours written: " + ", ".join("%s" % r for r in rad)
    if expo is not None:
        msg += " | expo: " + ", ".join("%s" % e for e in expo)
    elif mass is None:
        msg += " | (no resMass yet, expo skipped)"
    return msg


status = main(path, results, resMass, vecs, faces, nSeg)
