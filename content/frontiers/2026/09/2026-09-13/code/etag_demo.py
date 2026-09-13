"""Local-only conditional GET experiment. Python 3.10+, standard library only."""
import hashlib
import json
import platform
import sys
import threading
import urllib.error
import urllib.request
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

origin = {"body": '标题：第一版日报\n'.encode()}

def digest(body):
    return hashlib.sha256(body).hexdigest()

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/daily":
            self.send_error(404)
            return
        body = origin["body"]
        etag = '"' + digest(body) + '"'
        unchanged = self.headers.get("If-None-Match") == etag
        self.send_response(304 if unchanged else 200)
        self.send_header("ETag", etag)
        self.send_header("Cache-Control", "no-cache")
        if not unchanged:
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if not unchanged:
            self.wfile.write(body)

    def log_message(self, *args):
        pass

def main():
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    url = f"http://127.0.0.1:{server.server_port}/daily"
    cache_body = None
    cache_etag = None
    rows = []
    try:
        for step, label in enumerate(["首次获取", "内容未变，条件请求", "源站更新，条件请求"], 1):
            if step == 3:
                origin["body"] = '标题：第二版日报，新增核验结果\n'.encode()
            sent_etag = cache_etag
            headers = {"If-None-Match": cache_etag} if cache_etag else {}
            request = urllib.request.Request(url, headers=headers)
            try:
                response = opener.open(request, timeout=3)
            except urllib.error.HTTPError as error:
                if error.code != 304:
                    raise
                response = error
            with response:
                status = response.code
                received = response.read()
                response_etag = response.headers["ETag"]
            if status == 200:
                assert response_etag == '"' + digest(received) + '"'
                cache_body, cache_etag = received, response_etag
            elif status == 304:
                assert cache_body is not None and received == b""
                assert response_etag == cache_etag
            assert digest(cache_body) == digest(origin["body"])
            rows.append({"step": step, "label": label, "status": status,
                         "requestETag": sent_etag, "responseETag": response_etag,
                         "responseBytes": len(received), "usedBytes": len(cache_body),
                         "sha256": digest(cache_body), "text": cache_body.decode()})
        assert [row["status"] for row in rows] == [200, 304, 200]
        assert rows[0]["sha256"] == rows[1]["sha256"] != rows[2]["sha256"]
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=3)
    output = {"runAt": datetime.now(timezone.utc).isoformat(), "python": sys.version,
              "platform": platform.platform(), "scope": "127.0.0.1 only; synthetic fixture",
              "rows": rows, "passed": True}
    path = Path(__file__).with_name("etag-results.json.txt")
    path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(output, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
