#!/usr/bin/env python3
"""Receipt Sheet Builder server:
 - serves the static app
 - POST /export  {model JSON}  -> generated PDF (cover, sheets, cut lines)
"""
import io
import json
import re
from http.server import HTTPServer, SimpleHTTPRequestHandler

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, landscape, A4
from reportlab.lib.colors import HexColor, black

APP_DIR = __file__.rsplit('/', 1)[0]
PAGE_W, PAGE_H = landscape(letter)  # adjusted per request in generate()
SAVED_MODEL = {}

DEFAULTS = {
    'coverEnabled': True,
    'coverTemplate': 'full',
    'coverTitle': 'OFFICIAL RECEIPT BOOK',
    'coverLines': ['New Israel Community', 'Brewerville City'],
    'coverShowRange': True,
    'coverRangeLabel': 'Receipt Nos.',
    'coverFields': ['Academic Year:', 'Issued to:', 'Registrar:'],
    'schoolName': 'Suahco4',
    'address': ['New Israel Community', 'Brewerville City', 'Phone: 0778662590'],
    'fields': ['Name:', 'Grade:', 'Date:', 'Amount in words:'],
    'numberMode': 'copy',
    'carbon': {'enabled': True, 'color': '#d9e6ff'},
    'numberStart': 1,
    'numberDigits': 4,
    'numberColor': '#ff0000',
    'sheets': 10,
    'slipsPerSheet': 3,
    'columns': ['No', 'Description', 'Amount', 'Receipt No'],
    'rows': ['Registration', '1st Semester', '2nd Semester', 'Uniform',
             'P.E. Uniform', 'Graduation', 'WAEC', 'Gala day',
             'Computer', 'Field trip', 'Total', 'Balance'],
    'signedLabel': 'Signed:',
    'roleLabel': 'Registrar',
    'cut': {'enabled': True, 'style': 'dashed', 'color': '#9aa0a6', 'width': 1,
            'vertical': True, 'outer': False, 'horizontal': True, 'hPos': 7.6},
    'fontFamily': '"Times New Roman", Times, serif',
    'inkColor': '#000000',
    'paper': 'letter',
}

ORD = re.compile(r'(\d+)(st|nd|rd|th)\b', re.I)


def merged(saved):
    m = json.loads(json.dumps(DEFAULTS))
    if isinstance(saved, dict):
        for k, v in saved.items():
            if k in DEFAULTS and isinstance(v, type(DEFAULTS[k])):
                m[k] = v
        if isinstance(m.get('cut'), dict):
            for k, v in DEFAULTS['cut'].items():
                m['cut'].setdefault(k, v)
        if isinstance(m.get('carbon'), dict):
            for k, v in DEFAULTS['carbon'].items():
                m['carbon'].setdefault(k, v)
    return m


def pad(m, n):
    return str(n).zfill(m['numberDigits'])


def sheet_numbers(m, i):
    if m['numberMode'] == 'copy':
        base = m['numberStart'] + (i // 2) * m['slipsPerSheet']
        return [base + s for s in range(m['slipsPerSheet'])]
    return [m['numberStart'] + i] * m['slipsPerSheet']


def draw_ordinal_text(c, x, y, text, size):
    """Draw text, rendering 1st/2nd/3rd ordinals with a raised small suffix."""
    pos = x
    last = 0
    for mo in ORD.finditer(text):
        pre = text[last:mo.start(2)]
        c.drawString(pos, y, pre)
        pos += c.stringWidth(pre, 'Times-Roman', size)
        c.drawString(pos, y + size * 0.28, mo.group(2))
        pos += c.stringWidth(mo.group(2), 'Times-Roman', size * 0.7)
        last = mo.end(2)
    rest = text[last:]
    c.drawString(pos, y, rest)


def set_dash(c, m):
    st = m['cut']['style']
    if st == 'dotted':
        c.setDash(1.5, 3)
    elif st == 'solid':
        c.setDash()
    elif st == 'dashdot':
        c.setDash([6, 3, 1.5, 3])
    else:
        c.setDash(6, 4)


def draw_cut_lines(c, m):
    cut = m['cut']
    if not cut['enabled']:
        return
    c.saveState()
    c.setStrokeColor(HexColor(cut['color']))
    c.setLineWidth(cut['width'])
    n = m['slipsPerSheet']
    if cut['vertical']:
        for i in range(1, n):
            x = PAGE_W * i / n
            set_dash(c, m)
            c.line(x, 0, x, PAGE_H)
    if cut['outer']:
        set_dash(c, m)
        c.line(0.5, 0, 0.5, PAGE_H)
        c.line(PAGE_W - 0.5, 0, PAGE_W - 0.5, PAGE_H)
    if cut['horizontal']:
        y = PAGE_H - min(cut['hPos'] * 72, PAGE_H - 4)
        set_dash(c, m)
        c.line(0, y, PAGE_W, y)
    c.restoreState()


def draw_cover_slip(c, m, w, last):
    """Cover as one receipt piece (like the 001 receipt)."""
    ink = HexColor(m['inkColor'])
    c.setStrokeColor(ink)
    c.setFillColor(ink)
    c.setLineWidth(2)
    c.rect(4, 4, w - 8, PAGE_H - 8)
    c.setLineWidth(0.7)
    c.rect(8, 8, w - 16, PAGE_H - 16)

    y = PAGE_H - 60
    c.setFont('Times-Bold', 13.5)
    c.drawCentredString(w / 2, y, m['schoolName'])
    y -= 13
    c.setFont('Times-Roman', 9.5)
    for line in m['coverLines']:
        c.drawCentredString(w / 2, y, line)
        y -= 12
    y -= 6
    c.setFont('Times-Bold', 13.5)
    c.setFillColor(HexColor(m['numberColor']))
    c.drawRightString(w - 20, y, pad(m, m['numberStart']))
    c.setFillColor(ink)
    y -= 34
    c.setFont('Times-Bold', 16)
    c.drawCentredString(w / 2, y, m['coverTitle'])
    y -= 24
    if m['coverShowRange']:
        c.setFont('Times-Bold', 11)
        c.setFillColor(HexColor(m['numberColor']))
        c.drawCentredString(w / 2, y,
                            '%s %s to %s' % (m['coverRangeLabel'], pad(m, m['numberStart']), pad(m, last)))
        c.setFillColor(ink)
        y -= 30
    c.setFont('Times-Roman', 10.5)
    for f in m['coverFields']:
        c.drawString(24, y, f)
        lw = c.stringWidth(f, 'Times-Roman', 10.5)
        c.setLineWidth(0.8)
        c.line(24 + lw + 4, y - 2, w - 24, y - 2)
        y -= 24


def draw_slip(c, m, x0, w, number):
    ink = HexColor(m['inkColor'])
    c.setFillColor(ink)
    c.setStrokeColor(ink)
    y = PAGE_H - 40

    c.setFont('Times-Bold', 13.5)
    c.drawCentredString(x0 + w / 2, y, m['schoolName'])
    y -= 14
    c.setFont('Times-Roman', 10.5)
    for line in m['address']:
        c.drawCentredString(x0 + w / 2, y, line)
        y -= 13
    y -= 4
    c.setFont('Times-Bold', 13.5)
    c.setFillColor(HexColor(m['numberColor']))
    c.drawRightString(x0 + w - 13, y, number)
    c.setFillColor(ink)
    y -= 16

    c.setFont('Times-Roman', 10.5)
    for f in m['fields']:
        c.drawString(x0 + 8, y, f)
        lw = c.stringWidth(f, 'Times-Roman', 10.5)
        c.setLineWidth(0.8)
        c.line(x0 + 8 + lw + 3, y - 2, x0 + w - 8, y - 2)
        y -= 15.5

    c.setLineWidth(2.2)
    c.line(x0 + 4, y - 4, x0 + w - 4, y - 4)
    y -= 12

    # table
    tx, tw = x0 + 4.5, w - 9
    cols = [0.12, 0.395, 0.24, 0.245]
    xs = [tx]
    for p in cols:
        xs.append(xs[-1] + tw * p)
    head_h, row_h = 21, 16.6
    c.setLineWidth(0.8)
    # grid
    c.line(tx, y, xs[-1], y)
    y_head = y - head_h
    c.line(tx, y_head, xs[-1], y_head)
    for _ in m['rows']:
        y_head -= row_h
        c.line(tx, y_head, xs[-1], y_head)
    for xv in xs:
        c.line(xv, y, xv, y_head)
    # header text
    c.setFont('Times-Roman', 12)
    hy = y - 14
    for i, title in enumerate(m['columns'][:4]):
        words = title.split()
        if len(words) > 1 and c.stringWidth(title, 'Times-Roman', 12) > (xs[i + 1] - xs[i] - 6):
            c.drawCentredString((xs[i] + xs[i + 1]) / 2, hy + 4, words[0])
            c.drawCentredString((xs[i] + xs[i + 1]) / 2, hy - 9, ' '.join(words[1:]))
        else:
            c.drawCentredString((xs[i] + xs[i + 1]) / 2, hy, title)
    # rows
    ry = y - head_h
    for idx, row in enumerate(m['rows']):
        ry -= row_h
        c.setFont('Times-Roman', 12)
        c.drawString(xs[0] + 5, ry + 5.5, str(idx + 1))
        draw_ordinal_text(c, xs[1] + 5, ry + 5.5, row, 12)
    y = y_head

    y -= 20
    c.setFont('Times-Roman', 12)
    c.drawString(x0 + 8, y, m['signedLabel'])
    lw = c.stringWidth(m['signedLabel'], 'Times-Roman', 12)
    c.setLineWidth(0.8)
    c.line(x0 + 8 + lw + 2, y - 8, x0 + 8 + lw + 2 + 155, y - 8)
    c.drawCentredString(x0 + w / 2, y - 22, m['roleLabel'])


def draw_cover(c, m, last):
    ink = HexColor(m['inkColor'])
    c.setStrokeColor(ink)
    c.setFillColor(ink)
    bw, bh = PAGE_W * 0.82, PAGE_H * 0.86
    bx, by = (PAGE_W - bw) / 2, (PAGE_H - bh) / 2
    c.setLineWidth(2.5)
    c.rect(bx, by, bw, bh)
    c.setLineWidth(0.8)
    c.rect(bx + 5, by + 5, bw - 10, bh - 10)

    y = by + bh - 70
    c.setFont('Times-Bold', 20)
    c.drawCentredString(PAGE_W / 2, y, m['schoolName'])
    y -= 18
    c.setFont('Times-Roman', 12)
    for line in m['coverLines']:
        c.drawCentredString(PAGE_W / 2, y, line)
        y -= 15
    y -= 55
    c.setFont('Times-Bold', 27)
    c.drawCentredString(PAGE_W / 2, y, m['coverTitle'])
    y -= 40
    if m['coverShowRange']:
        c.setFont('Times-Bold', 14)
        c.setFillColor(HexColor(m['numberColor']))
        c.drawCentredString(PAGE_W / 2, y,
                            '%s %s to %s' % (m['coverRangeLabel'], pad(m, m['numberStart']), pad(m, last)))
        c.setFillColor(ink)
        y -= 45
    c.setFont('Times-Roman', 12.5)
    fx = PAGE_W / 2 - PAGE_W * 0.35
    for f in m['coverFields']:
        c.drawString(fx, y, f)
        lw = c.stringWidth(f, 'Times-Roman', 12.5)
        c.setLineWidth(0.8)
        c.line(fx + lw + 4, y - 2, PAGE_W / 2 + PAGE_W * 0.35, y - 2)
        y -= 30


def generate(model):
    global PAGE_W, PAGE_H
    m = merged(model)
    PAGE_W, PAGE_H = landscape(A4) if m.get('paper') == 'a4' else landscape(letter)
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(PAGE_W, PAGE_H), pageCompression=0)
    c.setTitle('Receipt Book')

    last = m['numberStart']
    per_sheet = []
    for i in range(m['sheets']):
        nums = sheet_numbers(m, i)
        last = max(last, nums[-1])
        per_sheet.append(nums)

    if m['coverEnabled']:
        if m['coverTemplate'] == 'slip':
            w = PAGE_W / m['slipsPerSheet']
            c.setPageSize((w, PAGE_H))
            draw_cover_slip(c, m, w, last)
            c.showPage()
            c.setPageSize((PAGE_W, PAGE_H))
        else:
            draw_cover(c, m, last)
            c.showPage()

    for idx, nums in enumerate(per_sheet):
        n = m['slipsPerSheet']
        w = PAGE_W / n
        if m['numberMode'] == 'copy' and idx % 2 == 1 and m['carbon']['enabled']:
            c.setFillColor(HexColor(m['carbon']['color']))
            c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
            c.setFillColor(black)
        for s, num in enumerate(nums):
            draw_slip(c, m, s * w, w, pad(m, num))
        draw_cut_lines(c, m)
        c.showPage()

    c.save()
    return buf.getvalue()


def send_pdf(handler, model, attachment=False):
    pdf = generate(model)
    handler.send_response(200)
    handler.send_header('Content-Type', 'application/pdf')
    if attachment:
        handler.send_header('Content-Disposition', 'attachment; filename="receipt-book.pdf"')
    handler.send_header('Content-Length', str(len(pdf)))
    handler.end_headers()
    handler.wfile.write(pdf)


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=APP_DIR, **kw)

    def do_GET(self):
        if self.path.split('?')[0] == '/export.pdf':
            send_pdf(self, SAVED_MODEL, attachment=True)
        else:
            super().do_GET()

    def do_POST(self):
        path = self.path.rstrip('/')
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length).decode('utf-8') if length else '{}'
        try:
            model = json.loads(body or '{}')
        except Exception:
            model = {}
        if path == '/export':
            send_pdf(self, model, attachment=True)
        elif path == '/save':
            if isinstance(model, dict):
                SAVED_MODEL.clear()
                SAVED_MODEL.update(model)
                try:
                    with open(APP_DIR + '/model.json', 'w') as f:
                        json.dump(model, f)
                except Exception:
                    pass
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"ok":true}')
        else:
            self.send_error(404)

    def log_message(self, *a):
        pass


if __name__ == '__main__':
    try:
        with open(APP_DIR + '/model.json') as f:
            SAVED_MODEL.update(json.load(f))
    except Exception:
        pass
    server = HTTPServer(('0.0.0.0', 8000), Handler)
    print('serving on :8000', flush=True)
    server.serve_forever()
