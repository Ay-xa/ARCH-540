#!/usr/bin/env python3
"""Version_07 本地小服务：页面 ↔ windows.json 的搬运工（PLAN_v07 §4.3）。

  GET  /            工具页面 wwr-tool.html（同目录静态文件，页面运行在 http://localhost:8765）
  GET  /state       windows.json 原文
  POST /state       {"target_wwr": 0.18} 和/或 {"orientation": "S"}；只改这些字段和 updated_by / updated_at，其余保留

不做任何几何计算。启动：双击 start_server.bat，或 `python server.py`。加 --no-browser 不自动打开浏览器。
"""
import json, os, sys, threading, webbrowser, datetime
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

PORT = 8765
HERE = os.path.dirname(os.path.abspath(__file__))          # .../Version_07/rhino
ROOT = os.path.dirname(HERE)                                # .../Version_07  （wwr-tool.html、zoning-config.js 在这里）
STATE = os.path.join(HERE, "windows.json")
ALLOWED = {"target_wwr": (int, float, type(None)), "orientation": (str,)}
LOCK = threading.Lock()


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

    def do_GET(self):
        if self.path.split("?")[0] == "/state":
            try:
                with LOCK:
                    return self._json(200, read_state())
            except Exception as e:
                return self._json(500, {"error": str(e)})
        if self.path == "/" or self.path.startswith("/?"):
            self.path = "/wwr-tool.html" + (self.path[1:] if self.path.startswith("/?") else "")
        return super().do_GET()

    def do_POST(self):
        if self.path.split("?")[0] != "/state":
            return self._json(404, {"error": "not found"})
        try:
            n = int(self.headers.get("Content-Length") or 0)
            incoming = json.loads(self.rfile.read(n).decode("utf-8") or "{}")
            if not isinstance(incoming, dict):
                raise ValueError("body must be an object")
            changes = {}
            for k, v in incoming.items():
                if k not in ALLOWED:
                    raise ValueError("field not allowed: " + k)
                if not isinstance(v, ALLOWED[k]) or isinstance(v, bool):
                    raise ValueError("bad type for " + k)
                changes[k] = v
            if "target_wwr" in changes and changes["target_wwr"] is not None:
                changes["target_wwr"] = round(float(changes["target_wwr"]), 4)
            with LOCK:
                d = read_state()
                d.update(changes)
                d["updated_by"] = "tool"
                # 带毫秒：GH 只比较这个字符串判断文件变没变，两次写入落在同一秒也不能被当成没变
                d["updated_at"] = datetime.datetime.now().isoformat(timespec="milliseconds")
                write_state(d)
            return self._json(200, d)
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
