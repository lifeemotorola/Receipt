#!/usr/bin/env python3
"""Suahco4 — Receipt Platform, one command:

    python3 tools/platform_server.py        # then open  http://localhost:8000

Serves the repository root:
    /                       ->  index.html   (platform home + the single Receipt Editor)
    /index.html?builder=1   ->  the Receipt Editor (all 4 templates)
    /index.html?receipt=<id>->  one of the 40 library receipts, open in the editor
    /data/  /assets/  /docs/->  receipt library data, branding/previews, finished books

Everything the editor does (edit, preview, print / save-as-PDF) runs in the
browser, so plain static hosting of this folder works exactly the same — this
server just makes the platform open with one command.
"""
import functools
import http.server
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def main():
    port = int(os.environ.get("PORT", "8000"))
    handler = functools.partial(Handler, directory=ROOT)
    with http.server.ThreadingHTTPServer(("0.0.0.0", port), handler) as srv:
        print("Suahco4 Receipt Platform on http://0.0.0.0:%d  (root: %s)" % (port, ROOT), flush=True)
        srv.serve_forever()


if __name__ == "__main__":
    main()
