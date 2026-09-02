#!/usr/bin/env python3
"""
Run the whole Receipt Platform from a single command:

    python3 platform_server.py          # then open  http://localhost:8000

Serves:
    /                           ->  index.html            (platform home page)
    /receipts-app/              ->  Receipt Sheet Builder (static app)
    POST  /receipts-app/save    ->  remembers the builder's current model
    POST  /receipts-app/export  ->  generates receipt-book.pdf for the posted model
    GET   /receipts-app/export.pdf -> (re)downloads the PDF of the remembered model

The builder itself also works on plain static hosting (serve index.html plus the
receipts-app folder) - only the Export-PDF buttons need this small server;
without it they fall back to the browser Print dialog, which is already
print-ready.  Requires:  pip install reportlab
"""
import io
import json
import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, 'receipts-app'))
import server as builder          # reportlab-based receipt-sheet generator

SAVED = {}


def send_pdf(handler, model, attachment=True):
    pdf = builder.generate(model)
    handler.send_response(200)
    handler.send_header('Content-Type', 'application/pdf')
    handler.send_header('Content-Length', str(len(pdf)))
    if attachment:
        handler.send_header('Content-Disposition', 'attachment; filename="receipt-book.pdf"')
    handler.end_headers()
    handler.wfile.write(pdf)


def send_json(handler, obj, status=200):
    body = json.dumps(obj).encode('utf-8')
    handler.send_response(status)
    handler.send_header('Content-Type', 'application/json')
    handler.send_header('Content-Length', str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def do_GET(self):
        path = self.path.split('?')[0]
        if path == '/receipts-app/export.pdf':
            model = SAVED if SAVED else builder.DEFAULTS
            send_pdf(self, model, attachment=True)
        else:
            super().do_GET()

    def do_POST(self):
        path = self.path.rstrip('/')
        length = int(self.headers.get('Content-Length') or 0)
        raw = self.rfile.read(length).decode('utf-8') if length else '{}'
        try:
            model = json.loads(raw or '{}')
        except Exception:
            model = {}
        if path == '/receipts-app/save':
            if isinstance(model, dict):
                SAVED.clear()
                SAVED.update(model)
            send_json(self, {'ok': True})
        elif path == '/receipts-app/export':
            send_pdf(self, model)
        else:
            self.send_error(404)

    def log_message(self, *a):
        pass


if __name__ == '__main__':
    try:
        with open(os.path.join(ROOT, 'receipts-app', 'model.json')) as f:
            SAVED.update(json.load(f))
    except Exception:
        pass
    server = HTTPServer(('0.0.0.0', 8000), Handler)
    print('Receipt Platform serving on http://0.0.0.0:8000  (home: / , builder: /receipts-app/)', flush=True)
    server.serve_forever()
