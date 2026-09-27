#!/usr/bin/env python3
"""Version_08 本地小服务：页面 ↔ windows.json 的搬运工（PLAN_v08 §5.2）。

  GET  /            工具页面 wwr-tool.html（同目录静态文件，页面运行在 http://localhost:8765）
  GET  /state       windows.json 原文
  POST /state       只接受 target_wwr、orientation、facade{width,floor_height,floors,sill,head}、photo{...}、pattern[{id,u,w}]；
                    只改这些字段和 updated_by / updated_at，其余保留
  POST /photo       {"name": "x.jpg", "dataUrl": "data:image/...;base64,..."} → 存为 rhino/facade_photo.<ext>（png / jpg / webp，≤ 10 MB）
  GET  /photo       当前照片

不做任何几何计算。启动：双击 start_server.bat，或 `python server.py`。加 --no-browser 不自动打开浏览器。
"""
import json, os, sys, threading, webbrowser, datetime, base64, glob
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

PORT = 8765
HERE = os.path.dirname(os.path.abspath(__file__))          # .../Version_08/rhino
ROOT = os.path.dirname(HERE)                                # .../Version_08  （wwr-tool.html、zoning-config.js 在这里）
STATE = os.path.join(HERE, "windows.json")
PHOTO_BASE = os.path.join(HERE, "facade_photo")             # + .png / .jpg / .webp
PHOTO_MAX = 10 * 1024 * 1024
LOCK = threading.Lock()
NUM = (int, float)


def num(v, lo, hi, name):
    if isinstance(v, bool) or not isinstance(v, NUM) or not (lo <= v <= hi):
        raise ValueError("%s must be a number in [%s, %s]" % (name, lo, hi))
    return round(float(v), 4)


def check_facade(f):
    if not isinstance(f, dict):
        raise ValueError("facade must be an object")
    out = {
        "width": num(f.get("width"), 1, 200, "facade.width"),
        "floor_height": num(f.get("floor_height"), 2, 6, "facade.floor_height"),
        "floors": int(num(f.get("floors"), 1, 50, "facade.floors")),
        "sill": num(f.get("sill"), 0, 1.5, "facade.sill"),
        "head": num(f.get("head"), 0.4, 6, "facade.head"),
    }
    if out["head"] <= out["sill"]:
        raise ValueError("facade.head must be above facade.sill")
    return out


def check_pattern(p):
    if not isinstance(p, list) or not p:
        raise ValueError("pattern must be a non-empty list")
    out = []
    for i, w in enumerate(p):
        if not isinstance(w, dict):
            raise ValueError("pattern items must be objects")
        out.append({"id": str(w.get("id") or "W%02d" % (i + 1))[:8], "u": num(w.get("u"), 0, 1, "u"), "w": num(w.get("w"), 0, 1, "w")})
    return out


def check_photo(p):
    if not isinstance(p, dict):
        raise ValueError("photo must be an object")
    keep = {}
    for k in ("file", "method", "date"):
        if k in p:
            keep[k] = str(p[k])[:120]
    for k in ("image_w", "image_h", "floors", "windows_per_floor"):
        if k in p:
            keep[k] = int(num(p[k], 0, 100000, k))
    for k in ("facade_box",):
        if k in p and p[k] is not None:
            keep[k] = [num(v, -1e5, 1e5, k) for v in list(p[k])[:4]]
    if "boxes" in p:
        keep["boxes"] = [[num(v, -1e5, 1e5, "box") for v in list(b)[:4]] for b in list(p["boxes"])[:200]]
    return keep


CHECK = {
    "target_wwr": lambda v: None if v is None else num(v, 0, 1, "target_wwr"),
    "orientation": lambda v: v if v in ("S", "E", "N", "W") else (_ for _ in ()).throw(ValueError("orientation must be S/E/N/W")),
    "facade": check_facade,
    "photo": check_photo,
    "pattern": check_pattern,
}
MAGIC = ((b"\x89PNG", "png", "image/png"), (b"\xff\xd8", "jpg", "image/jpeg"), (b"RIFF", "webp", "image/webp"))


def photo_path():
    hits = sorted(glob.glob(PHOTO_BASE + ".*"))
    return hits[0] if hits else None


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

    def log_message(self, fmt, *args):      # 只打一行，安静一点
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

    def _bytes(self, code, data, ctype):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        if n > PHOTO_MAX * 2:
            raise ValueError("body too large")
        obj = json.loads(self.rfile.read(n).decode("utf-8") or "{}")
        if not isinstance(obj, dict):
            raise ValueError("body must be an object")
        return obj

    def do_GET(self):
        route = self.path.split("?")[0]
        if route == "/state":
            try:
                with LOCK:
                    return self._json(200, read_state())
            except Exception as e:
                return self._json(500, {"error": str(e)})
        if route == "/photo":
            p = photo_path()
            if not p:
                return self._json(404, {"error": "no photo"})
            ext = p.rsplit(".", 1)[-1].lower()
            ctype = {"png": "image/png", "jpg": "image/jpeg", "webp": "image/webp"}.get(ext, "application/octet-stream")
            with open(p, "rb") as f:
                return self._bytes(200, f.read(), ctype)
        if self.path == "/" or self.path.startswith("/?"):
            self.path = "/wwr-tool.html" + (self.path[1:] if self.path.startswith("/?") else "")
        return super().do_GET()

    def do_POST(self):
        route = self.path.split("?")[0]
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
                    if "facade" in changes:                      # 保留 layer 等页面不写的键
                        d["facade"] = dict(d.get("facade") or {}, **changes.pop("facade"))
                    d.update(changes)
                    d["updated_by"] = "tool"
                    # 带毫秒：GH 只比较这个字符串判断文件变没变，两次写入落在同一秒也不能被当成没变
                    d["updated_at"] = datetime.datetime.now().isoformat(timespec="milliseconds")
                    write_state(d)
                return self._json(200, d)
            if route == "/photo":
                incoming = self._body()
                url = str(incoming.get("dataUrl") or "")
                if not url.startswith("data:image/") or ";base64," not in url:
                    raise ValueError("dataUrl must be a base64 image data URL")
                raw = base64.b64decode(url.split(";base64,", 1)[1], validate=True)
                if len(raw) > PHOTO_MAX:
                    raise ValueError("photo larger than 10 MB")
                ext = None
                for magic, e, _ in MAGIC:
                    if raw.startswith(magic) and (e != "webp" or raw[8:12] == b"WEBP"):
                        ext = e
                if not ext:
                    raise ValueError("only png / jpg / webp")
                with LOCK:
                    for old in glob.glob(PHOTO_BASE + ".*"):
                        os.remove(old)
                    with open(PHOTO_BASE + "." + ext, "wb") as f:
                        f.write(raw)
                return self._json(200, {"file": "facade_photo." + ext, "bytes": len(raw)})
            return self._json(404, {"error": "not found"})
        except Exception as e:
            return self._json(400, {"error": str(e)})

def main():
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    url = "http://localhost:%d/" % PORT
    print("WWR tool + windows.json bridge  ->  %s   (Ctrl+C to stop)" % url)
    print("state file:", STATE)
    if "--no-browser" not in sys.argv:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
