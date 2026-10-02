#!/usr/bin/env python3
"""Massing_v01 本地小服务：页面 ↔ state.json 的搬运工（PLAN_massing_v01 §3）。

  GET  /              工具页面 massing-tool.html（页面运行在 http://localhost:8768）
  GET  /shared/<f>    共享引擎文件（Passivehouse_Tool/01_Prototypes/_shared/ 下的 wwr-climate.js / wwr-engine.js）
  GET  /state         state.json 原文
  POST /state         只接受 building / ops / windows / run / shading；只改这些字段和 updated_by / updated_at，其余（handle / results）保留给 Grasshopper 写

不做任何几何计算。启动：双击 start_server.bat，或 `python server.py`。加 --no-browser 不自动打开浏览器。
"""
import json, os, sys, threading, webbrowser, datetime
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

PORT = 8768
HERE = os.path.dirname(os.path.abspath(__file__))                       # .../Massing_v01/rhino
ROOT = os.path.dirname(HERE)                                             # .../Massing_v01  （massing-tool.html 在这里）
REPO = os.path.abspath(os.path.join(ROOT, "..", "..", "..", ".."))       # .../ARCH-540
SHARED = os.path.join(REPO, "Passivehouse_Tool", "01_Prototypes", "_shared")
STATE = os.path.join(HERE, "state.json")
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


def check_building(b):
    if not isinstance(b, dict):
        raise ValueError("building must be an object")
    return {
        "floors": int(num(b.get("floors"), 1, 30, "building.floors")),
        "H": num(b.get("H"), 2.6, 6, "building.H"),
        "slab": num(b.get("slab", 0.35), 0.15, 1.0, "building.slab"),
        "L": num(b.get("L"), 6, 80, "building.L"),
        "W": num(b.get("W"), 6, 60, "building.W"),
        "az0": num(b.get("az0"), 0, 360, "building.az0"),
    }


def check_ops(ops):
    if not isinstance(ops, list):
        raise ValueError("ops must be a list")
    out = []
    for i, o in enumerate(ops[:20]):
        if not isinstance(o, dict):
            raise ValueError("ops items must be objects")
        if o.get("type") not in ("notch", "court"):
            raise ValueError("ops[%d].type: notch / court in Massing_v01" % i)
        if o.get("propagate", "up") != "up":
            raise ValueError("ops[%d].propagate: only 'up' in Massing_v01" % i)
        common = {"id": str(o.get("id") or "%s%02d" % (o["type"], i + 1))[:16], "type": o["type"],
                  "floor": int(num(o.get("floor", 1), 1, 30, "ops.floor")), "propagate": "up",
                  "width": num(o.get("width"), 0, 80, "ops.width"), "depth": num(o.get("depth"), 0, 60, "ops.depth"),
                  "at": now()}                              # 页面改了就盖新时间戳；GH 用它和 handle.at 比谁后动
        if o["type"] == "notch":
            if o.get("edge") not in EDGES:
                raise ValueError("ops[%d].edge must be A/B/C/D" % i)
            common.update({"edge": o["edge"], "pos": num(o.get("pos"), 0, 1, "ops.pos")})
        else:
            common.update({"pos_u": num(o.get("pos_u"), 0, 1, "ops.pos_u"), "pos_v": num(o.get("pos_v"), 0, 1, "ops.pos_v")})
        out.append(common)
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
    return out


def check_shading(sh):
    if not isinstance(sh, dict):
        raise ValueError("shading must be an object")
    if sh.get("type") not in ("none", "bifoldV"):
        raise ValueError("shading.type must be none/bifoldV (Massing_v01)")
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
           "fixed": sh.get("fixed", "alt") if sh.get("fixed", "alt") in ("alt", "same") else "alt"}
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
        route = self.path.split("?")[0]
        if route == "/state":
            try:
                with LOCK:
                    return self._json(200, read_state())
            except Exception as e:
                return self._json(500, {"error": str(e)})
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
                    d.update(changes)
                    d["updated_by"] = "tool"
                    d["updated_at"] = now()
                    write_state(d)
                return self._json(200, d)
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
