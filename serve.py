"""杂坛服务器：静态文件 + 评论区 API + 知乎热榜爬虫"""
import http.server, threading, subprocess, json, time, webbrowser, os, sys, urllib.parse

PORT = 8080
DIR = os.path.dirname(os.path.abspath(__file__))
COMMENTS_FILE = os.path.join(DIR, "comments.json")
DELETE_SECRET = os.environ.get("DELETE_SECRET", "zatan123")  # ← 改这个密码

os.chdir(DIR)


# ── 评论区数据 ──

def load_comments():
    if not os.path.exists(COMMENTS_FILE):
        return []
    with open(COMMENTS_FILE, encoding="utf-8") as f:
        comments = json.load(f)
    for i, c in enumerate(comments):
        if "id" not in c:
            c["id"] = int(time.time() * 1000) + i
    return comments


def save_comments(comments):
    with open(COMMENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(comments, f, ensure_ascii=False, indent=2)


# ── 知乎热榜 ──

def update_hotlist():
    while True:
        try:
            subprocess.run(
                [sys.executable, "zhihu_hot.py"], capture_output=True, timeout=30
            )
            with open("hotlist.json", encoding="utf-8") as f:
                data = json.load(f)
            print(f'[{time.strftime("%H:%M:%S")}] 热榜已更新 ({len(data)} 条)')
        except Exception as e:
            print(f'[{time.strftime("%H:%M:%S")}] 更新失败: {e}')
        time.sleep(300)


# ── HTTP Handler ──

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=DIR, **kw)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/comments":
            self.send_json(load_comments())
        elif parsed.path == "/api/comments/data":
            # 查看当前存储的原始数据（含 id，用于调试/id 定位）
            self.send_json({"comments": load_comments(), "total": len(load_comments())})
        else:
            super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        body = self.read_body()

        if parsed.path == "/api/comments":
            comments = load_comments()
            c = {
                "id": int(time.time() * 1000),
                "name": body.get("name", "匿名") or "匿名",
                "content": body.get("content", ""),
                "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            comments.append(c)
            save_comments(comments)
            self.send_json({"ok": True, "comment": c})

        elif parsed.path == "/api/comments/delete":
            if body.get("secret") != DELETE_SECRET:
                self.send_json({"ok": False, "error": "密码错误"}, 403)
                return
            comments = load_comments()
            target_id = body.get("id")
            new_cmts = [c for c in comments if c.get("id") != target_id]
            if len(new_cmts) == len(comments):
                self.send_json({"ok": False, "error": "未找到该留言"}, 404)
                return
            save_comments(new_cmts)
            self.send_json({"ok": True, "deleted_id": target_id})

        else:
            self.send_json({"error": "not found"}, 404)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    # ── helpers ──

    def read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length)) if length else {}

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body.encode())))
        self.end_headers()
        self.wfile.write(body.encode())

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

    def log_message(self, fmt, *args):
        pass  # 不输出静态文件日志


if __name__ == "__main__":
    subprocess.run([sys.executable, "zhihu_hot.py"], capture_output=True)
    t = threading.Thread(target=update_hotlist, daemon=True)
    t.start()

    server = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"→ http://localhost:{PORT}")
    print(f"  DELETE_SECRET={DELETE_SECRET}")
    webbrowser.open(f"http://localhost:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
