#!/usr/bin/env python3
"""Massing_v01 本地小服务：页面 ↔ state.json 的搬运工（PLAN_massing_v01 §3）。

  GET  /              工具页面 massing-tool.html（页面运行在 http://localhost:8768）
  GET  /shared/<f>    共享引擎文件（Passivehouse_Tool/01_Prototypes/_shared/ 下的 wwr-climate.js / wwr-engine.js）
  GET  /state         state.json 原文
  POST /state         只接受 building / ops / windows / run / shading；只改这些字段和 updated_by / updated_at，其余（handle / results）保留给 Grasshopper 写
  读图（2026-10-03 第四刀步 3）：
  GET  /vision        {mode:'api'|'claude'}：rhino/api_key.txt 存在就能直接调模型，否则走「交给 Claude」收件夹
  POST /inbox         {note, images:[{name, dataUrl}]} → 存到 02_Rules/inbox/<id>/（图 + request.json），mode=api 时顺手调模型写 card.json
  GET  /inbox         收件夹列表（每条：id, at, note, images, status, card）
  GET  /inbox/<id>/<f> 收件夹里的图
  POST /inbox/<id>/read   只在 api 模式：对这一条（重新）调模型写 card.json
  POST /inbox/<id>/card   页面改过的卡写回 card.json（status 不变）
  POST /inbox/<id>/status {status:'applied'|'library'|'claude'|'pending'} 记状态

不做任何几何计算。启动：双击 start_server.bat，或 `python server.py`。加 --no-browser 不自动打开浏览器。
"""
import json, re, os, sys, threading, webbrowser, datetime, urllib.parse
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

PORT = 8768
HERE = os.path.dirname(os.path.abspath(__file__))                       # .../Massing_v01/rhino
ROOT = os.path.dirname(HERE)                                             # .../Massing_v01  （massing-tool.html 在这里）
REPO = os.path.abspath(os.path.join(ROOT, "..", "..", "..", ".."))       # .../ARCH-540
SHARED = os.path.join(REPO, "Passivehouse_Tool", "01_Prototypes", "_shared")
STATE = os.path.join(HERE, "state.json")
RULES = os.path.join(REPO, "Openning_Shade_Relation_Tool", "02_Rules")
INBOX = os.path.join(RULES, "inbox")
API_KEY_FILE = os.path.join(HERE, "api_key.txt")            # 不进 git；一行 key
VISION_MODEL = "claude-opus-5-5"                              # 读图用的模型
IMG_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp", ".gif": "image/gif"}
LOCK = threading.Lock()
NUM = (int, float)
EDGES = ("A", "B", "C", "D")


def num(v, lo, hi, name):
    if isinstance(v, bool) or not isinstance(v, NUM) or not (lo <= v <= hi):
        raise ValueError("%s must be a number in [%s, %s]" % (name, lo, hi))
    return round(float(v), 4)


def now():
    # 带毫秒：GH 只比较这个字符串判断文件变没变，两次写入落在同一秒也不能被当成没变
    return datetime.datetime.now().isoformat(timespec="milliseconds")


# ---------------- 读图收件夹 ----------------
def api_key():
    try:
        with open(API_KEY_FILE, "r", encoding="utf-8") as f:
            k = f.read().strip()
        return k or None
    except Exception:
        return None


def inbox_list():
    out = []
    if not os.path.isdir(INBOX):
        return out
    for name in sorted(os.listdir(INBOX)):
        d = os.path.join(INBOX, name)
        rq = os.path.join(d, "request.json")
        if not os.path.isfile(rq):
            continue
        try:
            with open(rq, "r", encoding="utf-8") as f:
                r = json.load(f)
        except Exception:
            continue
        card = None
        cp = os.path.join(d, "card.json")
        if os.path.isfile(cp):
            try:
                with open(cp, "r", encoding="utf-8") as f:
                    card = json.load(f)
            except Exception as e:
                card = {"error": "card.json 读不出来: %s" % e}
        r["card"] = card
        r["images"] = ["/inbox/%s/%s" % (name, im) for im in r.get("files", [])]
        out.append(r)
    return out


def inbox_save(body):
    import base64
    note = str(body.get("note", ""))[:2000]
    images = body.get("images") or []
    if not isinstance(images, list) or not images:
        raise ValueError("at least one image")
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = re.sub(r"[^0-9A-Za-z]+", "_", note)[:20].strip("_") or "img"          # id 只用 ASCII，URL 和文件名都省事
    rid = "%s_%s" % (stamp, slug)
    d = os.path.join(INBOX, rid)
    os.makedirs(d, exist_ok=True)
    files = []
    for i, im in enumerate(images[:6]):
        data_url = str(im.get("dataUrl", ""))
        m = re.match(r"^data:(image/[a-z]+);base64,(.+)$", data_url, re.S)
        if not m:
            raise ValueError("image %d is not a data url" % i)
        ext = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp", "image/gif": ".gif"}.get(m.group(1), ".png")
        fn = "img%d%s" % (i + 1, ext)
        with open(os.path.join(d, fn), "wb") as f:
            f.write(base64.b64decode(m.group(2)))
        files.append(fn)
    req = {"id": rid, "at": now(), "note": note, "files": files, "status": "pending"}
    with open(os.path.join(d, "request.json"), "w", encoding="utf-8") as f:
        json.dump(req, f, ensure_ascii=False, indent=2)
    return req


def inbox_update(rid, **kw):
    d = os.path.join(INBOX, rid)
    rq = os.path.join(d, "request.json")
    with open(rq, "r", encoding="utf-8") as f:
        r = json.load(f)
    r.update(kw)
    with open(rq, "w", encoding="utf-8") as f:
        json.dump(r, f, ensure_ascii=False, indent=2)
    return r


VISION_PROMPT = """你是一个建筑遮阳装置的分析员。用户给你一张或几张遮阳装置的图（可能是运动分析图、照片或线稿）和一句描述。
请按下面的「八个问题」逐条回答，再判断它最接近机构库里的哪个条目，并给出可以直接用的参数。只输出一个 JSON 对象，不要别的文字。

JSON 格式（字段名必须一致）：
{
  "summary": "一两句话说这个装置怎么动",
  "answers": {"1 挡哪个方向的太阳": "...", "2 元素的方向": "...", "3 单元尺寸（宽 / 深 / 厚）": "...", "4 单元密度与排布": "...", "5 透不透（穿孔率）": "...", "6 动不动（怎么动）": "...", "7 在玻璃哪一侧": "...", "8 盖住窗的哪部分": "..."},
  "closest": "pivot | bifoldV | bifoldH | umbrella | none",
  "confidence": 0.0 到 1.0,
  "differences": ["和最接近条目的不同之处，一条一句"],
  "evidence": ["你在图里看到的依据，一条一句"],
  "shading": {"type": "同 closest（none 时填 bifoldV 作占位）", "unitW": 单元宽 m, "tilt": 代表性折角 度, "tiltRange": [最小, 最大], "standoff": 离墙 m, "thick": 板厚 m, "skin": 表皮厚 mm, "holeD": 孔径 mm, "perfMin": 穿孔率下限 0–0.9, "perfMax": 穿孔率上限 0–0.9},
  "newEntryNeeded": true 或 false,
  "notes": "给设计者的一句提醒（近似在哪里）"
}
看不出来的数值给合理估计并在 evidence 里说明是估计；不要编造图里没有的东西。

下面是分析规则（SHADING_RULES.md）和机构库（MECHANISMS.md），作为对照：
"""


def vision_call(rid):
    """对收件夹里一条调模型，写 card.json。需要 api_key.txt。"""
    import base64, urllib.request
    key = api_key()
    if not key:
        raise ValueError("no api key")
    d = os.path.join(INBOX, rid)
    with open(os.path.join(d, "request.json"), "r", encoding="utf-8") as f:
        req = json.load(f)
    docs = ""
    for fn in ("SHADING_RULES.md", "MECHANISMS.md"):
        try:
            with open(os.path.join(RULES, fn), "r", encoding="utf-8") as f:
                docs += "\n\n===== %s =====\n" % fn + f.read()[:30000]
        except Exception:
            pass
    content = []
    for fn in req.get("files", []):
        ext = os.path.splitext(fn)[1].lower()
        with open(os.path.join(d, fn), "rb") as f:
            b64 = base64.b64encode(f.read()).decode("ascii")
        content.append({"type": "image", "source": {"type": "base64", "media_type": IMG_TYPES.get(ext, "image/png"), "data": b64}})
    content.append({"type": "text", "text": VISION_PROMPT + docs + "\n\n用户的描述：" + (req.get("note") or "（无）")})
    payload = {"model": VISION_MODEL, "max_tokens": 2000, "messages": [{"role": "user", "content": content}]}
    http_req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=json.dumps(payload).encode("utf-8"),
                                      headers={"content-type": "application/json", "x-api-key": key, "anthropic-version": "2023-06-01"})
    with urllib.request.urlopen(http_req, timeout=120) as resp:
        out = json.loads(resp.read().decode("utf-8"))
    text = "".join(b.get("text", "") for b in out.get("content", []) if b.get("type") == "text")
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError("model returned no json: " + text[:200])
    card = json.loads(m.group(0))
    card.update({"id": rid, "at": now(), "by": "api:" + VISION_MODEL})
    with open(os.path.join(d, "card.json"), "w", encoding="utf-8") as f:
        json.dump(card, f, ensure_ascii=False, indent=2)
    inbox_update(rid, status="read")
    return card


def safe_rid(rid):
    if not re.match(r"^[0-9A-Za-z_\u4e00-\u9fff-]+$", rid or "") or not os.path.isdir(os.path.join(INBOX, rid)):
        raise ValueError("unknown inbox id")
    return rid


def check_building(b):
    if not isinstance(b, dict):
        raise ValueError("building must be an object")
    out = {
        "floors": int(num(b.get("floors"), 1, 30, "building.floors")),
        "H": num(b.get("H"), 2.6, 6, "building.H"),
        "slab": num(b.get("slab", 0.35), 0.15, 1.0, "building.slab"),
        "L": num(b.get("L"), 6, 80, "building.L"),
        "W": num(b.get("W"), 6, 60, "building.W"),
        "az0": num(b.get("az0"), 0, 360, "building.az0"),
    }
    g = b.get("groups")
    if isinstance(g, dict) and isinstance(g.get("list"), list):        # 2026-10-03：任意组数 [{n, setback}]
        lst = []
        for gr in g["list"][:8]:
            gr = gr if isinstance(gr, dict) else {}
            sb = gr.get("setback") or {}
            lst.append({"n": int(num(gr.get("n", 0), 0, 30, "groups.list.n")),
                        "setback": dict((k, num(sb.get(k, 0), 0, 30, "groups.list.setback." + k)) for k in EDGES)})
        if not lst:
            raise ValueError("groups.list must have at least one group")
        for gr0, gr in zip(g["list"][:8], lst):
            shf = (gr0 or {}).get("shift") or {}
            gr["shift"] = {"x": num(shf.get("x", 0), -30, 30, "groups.list.shift.x"), "y": num(shf.get("y", 0), -30, 30, "groups.list.shift.y")}
        out["groups"] = {"list": lst}
    elif isinstance(g, dict):
        sb = g.get("setback") or {}
        out["groups"] = {"podium": int(num(g.get("podium", out["floors"]), 0, 30, "groups.podium")),
                         "setback": dict((k, num(sb.get(k, 0), 0, 30, "groups.setback." + k)) for k in EDGES)}
    return out


def check_ops(ops):
    if not isinstance(ops, list):
        raise ValueError("ops must be a list")
    out = []
    for i, o in enumerate(ops[:20]):
        if not isinstance(o, dict):
            raise ValueError("ops items must be objects")
        if o.get("type") not in ("notch", "court", "split"):
            raise ValueError("ops[%d].type: notch / court / split" % i)
        if o.get("propagate", "up") != "up":
            raise ValueError("ops[%d].propagate: only 'up' in Massing_v01" % i)
        if not re.match(r"^(all|g[1-8])$", str(o.get("apply", "all"))):
            raise ValueError("ops[%d].apply must be all or g1…g8" % i)
        common = {"id": str(o.get("id") or "%s%02d" % (o["type"], i + 1))[:16], "type": o["type"], "apply": o.get("apply", "all"),
                  "floor": int(num(o.get("floor", 1), 1, 30, "ops.floor")), "propagate": "up",
                  "at": now()}                              # 页面改了就盖新时间戳；GH 用它和 handle.at 比谁后动
        if o["type"] == "notch":
            if o.get("edge") not in EDGES:
                raise ValueError("ops[%d].edge must be A/B/C/D" % i)
            common.update({"edge": o["edge"], "pos": num(o.get("pos"), 0, 1, "ops.pos"),
                           "width": num(o.get("width"), 0, 80, "ops.width"), "depth": num(o.get("depth"), 0, 60, "ops.depth")})
        elif o["type"] == "court":
            common.update({"pos_u": num(o.get("pos_u"), 0, 1, "ops.pos_u"), "pos_v": num(o.get("pos_v"), 0, 1, "ops.pos_v"),
                           "width": num(o.get("width"), 0, 80, "ops.width"), "depth": num(o.get("depth"), 0, 60, "ops.depth")})
        else:                                               # split（2026-10-03）：沿一条线切成两块，中间留 gap 的缝
            if o.get("axis", "x") not in ("x", "y"):
                raise ValueError("ops[%d].axis must be x/y" % i)
            common.update({"axis": o.get("axis", "x"), "pos": num(o.get("pos", 0.5), 0, 1, "ops.pos"), "gap": num(o.get("gap", 4), 0.5, 20, "ops.gap")})
        out.append(common)
    ids = [o["id"] for o in out]
    if len(set(ids)) != len(ids):
        raise ValueError("ops ids must be unique")
    return out


def check_windows(w):
    if not isinstance(w, dict):
        raise ValueError("windows must be an object")
    return {"wwr": num(w.get("wwr"), 0, 1, "windows.wwr"), "sill": num(w.get("sill"), 0, 3, "windows.sill")}


def check_run(r):
    if not isinstance(r, dict):
        raise ValueError("run must be an object")
    out = {"seq": int(num(r.get("seq"), 0, 1e9, "run.seq"))}
    if r.get("period") is not None:
        if r["period"] not in ("summer", "winter", "annual"):
            raise ValueError("run.period must be summer/winter/annual")
        out["period"] = r["period"]
    if r.get("clim") is not None:
        if r["clim"] not in ("apNow", "hbNow", "f2080"):
            raise ValueError("run.clim must be apNow/hbNow/f2080")
        out["clim"] = r["clim"]
    out["sun"] = bool(r.get("sun", True))          # 2026-10-03：False = 暂停 Ladybug 日照（页面「跑日照」勾、装置扫描时）
    return out


def check_shading(sh):
    if not isinstance(sh, dict):
        raise ValueError("shading must be an object")
    if sh.get("type") not in ("none", "pivot", "bifoldV", "bifoldH", "umbrella"):
        raise ValueError("shading.type must be none/pivot/bifoldV/bifoldH/umbrella")
    out = {"type": sh["type"],
           "unitW": num(sh.get("unitW", 3.0), 0.4, 6, "shading.unitW"),
           "tilt": num(sh.get("tilt", 45), 0, 90, "shading.tilt"),
           "standoff": num(sh.get("standoff", 0.4), 0, 2, "shading.standoff"),
           "thick": num(sh.get("thick", 0.15), 0.001, 0.3, "shading.thick"),
           "skin": num(sh.get("skin", 3), 0.5, 20, "shading.skin"),
           "holeD": num(sh.get("holeD", 5), 0, 30, "shading.holeD"),
           "perfMin": num(sh.get("perfMin", 0.1), 0, 0.9, "shading.perfMin"),
           "perfMax": num(sh.get("perfMax", 0.3), 0, 0.9, "shading.perfMax"),
           "floors": sh.get("floors", "all") if sh.get("floors", "all") in ("all", "2+") else "all",
           "fixed": sh.get("fixed", "alt") if sh.get("fixed", "alt") in ("alt", "same", "rand") else "alt",
           # 2026-10-03 从 Strip Window 补回的排布参数 + 打孔开关
           "groupMode": str(sh.get("groupMode", "fill")) if str(sh.get("groupMode", "fill")) in ("fill", "1", "2", "3", "mix") else "fill",
           "gapPanel": num(sh.get("gapPanel", 0), 0, 2, "shading.gapPanel"),
           "gapGroup": num(sh.get("gapGroup", 0), 0, 10, "shading.gapGroup"),
           "perf": bool(sh.get("perf", True))}
    fac = sh.get("facades")
    if fac is not None:                                   # 2026-10-03：按立面分设 {A|B|C|D|court: {on, tilt}}
        if not isinstance(fac, dict):
            raise ValueError("shading.facades must be an object")
        out["facades"] = {}
        for k, v in fac.items():
            if k not in ("A", "B", "C", "D", "court"):
                raise ValueError("shading.facades key must be A/B/C/D/court")
            if not isinstance(v, dict):
                raise ValueError("shading.facades.%s must be an object" % k)
            out["facades"][k] = {"on": bool(v.get("on", True)), "tilt": num(v.get("tilt", out["tilt"]), 0, 90, "shading.facades.%s.tilt" % k)}
    return out


CHECK = {"building": check_building, "ops": check_ops, "windows": check_windows, "run": check_run, "shading": check_shading}


def read_state():
    with open(STATE, "r", encoding="utf-8") as f:
        return json.load(f)


def write_state(d):
    tmp = STATE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    os.replace(tmp, STATE)


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def log_message(self, fmt, *args):
        sys.stdout.write("%s %s\n" % (self.address_string(), fmt % args)); sys.stdout.flush()

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def _json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        if n > 1024 * 1024:
            raise ValueError("body too large")
        obj = json.loads(self.rfile.read(n).decode("utf-8") or "{}")
        if not isinstance(obj, dict):
            raise ValueError("body must be an object")
        return obj

    def do_GET(self):
        route = urllib.parse.unquote(self.path.split("?")[0])      # 收件夹 id 里可能有非 ASCII，先解码
        if route == "/state":
            try:
                with LOCK:
                    return self._json(200, read_state())
            except Exception as e:
                return self._json(500, {"error": str(e)})
        if route == "/vision":
            return self._json(200, {"mode": "api" if api_key() else "claude", "model": VISION_MODEL})
        if route == "/inbox":
            try:
                return self._json(200, {"items": inbox_list(), "mode": "api" if api_key() else "claude"})
            except Exception as e:
                return self._json(500, {"error": str(e)})
        if route.startswith("/inbox/"):
            parts = route.split("/")
            if len(parts) == 4:
                try:
                    rid = safe_rid(parts[2]); fn = os.path.basename(parts[3])
                    p = os.path.join(INBOX, rid, fn)
                    ext = os.path.splitext(fn)[1].lower()
                    if ext not in IMG_TYPES or not os.path.isfile(p):
                        return self._json(404, {"error": "not found"})
                    with open(p, "rb") as f:
                        data = f.read()
                    self.send_response(200); self.send_header("Content-Type", IMG_TYPES[ext]); self.send_header("Content-Length", str(len(data))); self.end_headers()
                    return self.wfile.write(data)
                except Exception as e:
                    return self._json(400, {"error": str(e)})
        if route.startswith("/shared/"):
            name = os.path.basename(route[len("/shared/"):])
            p = os.path.join(SHARED, name)
            if not name.endswith(".js") or not os.path.isfile(p):
                return self._json(404, {"error": "not found"})
            with open(p, "rb") as f:
                data = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/javascript; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            return self.wfile.write(data)
        if self.path == "/" or self.path.startswith("/?"):
            self.path = "/massing-tool.html" + (self.path[1:] if self.path.startswith("/?") else "")
        return super().do_GET()

    def do_POST(self):
        route = urllib.parse.unquote(self.path.split("?")[0])      # 收件夹 id 里可能有非 ASCII，先解码
        try:
            if route == "/state":
                incoming = self._body()
                changes = {}
                for k, v in incoming.items():
                    if k not in CHECK:
                        raise ValueError("field not allowed: " + k)
                    changes[k] = CHECK[k](v)
                with LOCK:
                    d = read_state()
                    d.update(changes)
                    d["updated_by"] = "tool"
                    d["updated_at"] = now()
                    write_state(d)
                return self._json(200, d)
            if route == "/inbox":
                req = inbox_save(self._body())
                if api_key():
                    try:
                        req["card"] = vision_call(req["id"]); req["status"] = "read"
                    except Exception as e:
                        req["error"] = "模型调用失败：%s" % e
                return self._json(200, req)
            m = re.match(r"^/inbox/([^/]+)/(read|card|status)$", route)
            if m:
                rid = safe_rid(m.group(1)); action = m.group(2)
                if action == "read":
                    return self._json(200, vision_call(rid))
                if action == "card":
                    card = self._body()
                    with open(os.path.join(INBOX, rid, "card.json"), "w", encoding="utf-8") as f:
                        json.dump(card, f, ensure_ascii=False, indent=2)
                    return self._json(200, {"ok": True})
                if action == "status":
                    st = str(self._body().get("status", "pending"))
                    if st not in ("pending", "read", "applied", "library", "claude"):
                        raise ValueError("bad status")
                    return self._json(200, inbox_update(rid, status=st))
            return self._json(404, {"error": "not found"})
        except Exception as e:
            return self._json(400, {"error": str(e)})


def main():
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    url = "http://localhost:%d/" % PORT
    print("Massing_v01 bridge  ->  %s   (Ctrl+C to stop)" % url)
    print("state file:", STATE)
    print("shared engine:", SHARED)
    if "--no-browser" not in sys.argv:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
