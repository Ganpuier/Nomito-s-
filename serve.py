"""本地服务：每5分钟更新热榜 + 提供网页服务"""
import http.server, threading, subprocess, json, time, webbrowser, os, signal

PORT = 8080
DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(DIR)

def update_hotlist():
    """每5分钟跑一次爬虫"""
    while True:
        try:
            subprocess.run(
                [sys.executable, 'zhihu_hot.py'],
                capture_output=True, timeout=30
            )
            with open('hotlist.json', encoding='utf-8') as f:
                data = json.load(f)
            print(f'[{time.strftime("%H:%M:%S")}] 热榜已更新 ({len(data)} 条)')
        except Exception as e:
            print(f'[{time.strftime("%H:%M:%S")}] 更新失败: {e}')
        time.sleep(300)  # 5 分钟

import sys

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=DIR, **kw)
    def log_message(self, fmt, *args):
        pass  # 静默日志

if __name__ == '__main__':
    import sys
    # 先抓一次
    subprocess.run([sys.executable, 'zhihu_hot.py'], capture_output=True)

    # 启动后台更新线程
    t = threading.Thread(target=update_hotlist, daemon=True)
    t.start()

    # 启动 HTTP 服务
    server = http.server.HTTPServer(('0.0.0.0', PORT), Handler)
    print(f'→ http://localhost:{PORT}')
    webbrowser.open(f'http://localhost:{PORT}')

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
