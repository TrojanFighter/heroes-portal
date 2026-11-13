#!/usr/bin/env python3
"""Static server for the portal. Clean URLs: /x -> /x.html, /d/ -> /d/index.html."""
import os
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public")
PORT = int(os.environ.get("PORT", "8000"))

class H(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def send_head(self):
        path = self.translate_path(self.path)
        if self.path != "/" and not os.path.exists(path):
            alt = os.path.join(ROOT, self.path.lstrip("/") + ".html")
            if os.path.exists(alt):
                self.path = self.path + ".html"
        return super().send_head()

    def log_message(self, *a):
        pass

if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", PORT), H).serve_forever()
