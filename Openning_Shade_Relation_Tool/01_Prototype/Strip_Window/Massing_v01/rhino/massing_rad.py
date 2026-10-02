# massing_rad.py — Grasshopper「Python 3 Script」组件「massing sun」的源码（Massing_v01 第 7 步）
# 第一刀的 Ladybug 指标 = 直射日照小时（LB Direct Sun Hours，不需要 Radiance）；入射辐射要装 Radiance 以后再接。
# 输入：path（state.json）、results（LB Direct Sun Hours 的逐面结果 h，与 winMesh 的面顺序一致）、faces（每扇窗条的面数）、
#       nSeg（立面段数）。分析期名从 json 的 run.period 读。输出：status。
# 做的事：按面数把结果归到每扇窗条，再按「窗序号 % 段数」归到立面段（窗按层、再按段排列），写回 results.sun。
import json, os, datetime
import scriptcontext as sc


def now():
    return datetime.datetime.now().isoformat(timespec="milliseconds")


def main(path, results, faces, nSeg):
    if not path or not os.path.isfile(path):
        return "no state.json"
    vals = [float(v) for v in (results or []) if v is not None]
    cnt = [int(c) for c in (faces or [])]
    if not vals or not cnt or sum(cnt) != len(vals) or not nSeg:
        return "waiting: %d values, %d faces" % (len(vals), sum(cnt) if cnt else 0)
    per_win, i = [], 0
    for c in cnt:
        chunk = vals[i:i + c]; i += c
        per_win.append(sum(chunk) / len(chunk))
    n = int(nSeg)
    seg = [[] for _ in range(n)]
    for k, v in enumerate(per_win):
        seg[k % n].append(v)
    rad = [round(sum(x) / len(x), 1) if x else None for x in seg]
    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)
    period = (d.get("run") or {}).get("period", "summer")
    key = (tuple(rad), str(period))
    if sc.sticky.get("massing_sun_key") == key and (d.get("results") or {}).get("sun"):
        return "sun hours unchanged"

    d.setdefault("results", {})["sun"] = {"period": str(period), "unit": "h", "perSegment": rad,
                                                 "perWindow": [round(v, 1) for v in per_win], "at": now()}
    d["updated_by"] = "gh"; d["updated_at"] = now()
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)
    sc.sticky["massing_sun_key"] = key
    sc.sticky["massing_stamp"] = d["updated_at"]        # 让 massing sync 知道这次写入是自己人，不必重算
    return "sun hours written: " + ", ".join("%s" % r for r in rad)


status = main(path, results, faces, nSeg)
