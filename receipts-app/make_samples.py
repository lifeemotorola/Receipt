#!/usr/bin/env python3
"""Refresh the builder's sample PDFs and the preview PNGs used on the
platform home page. Run after changing branding in receipts-app/server.py:

    .venv/bin/python receipts-app/make_samples.py
"""
import copy
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, 'work')
sys.path.insert(0, HERE)

import server  # noqa: E402  (reportlab-based receipt generator)
import fitz  # pymupdf  # noqa: E402


def pdf_bytes(model):
    return server.generate(model)


def render_first(pdf, path, zoom=2.0, page=0, max_w=None):
    doc = fitz.open(stream=pdf, filetype='pdf')
    pg = doc[page]
    mat = fitz.Matrix(zoom, zoom)
    pix = pg.get_pixmap(matrix=mat, alpha=False)
    pix.save(path)
    doc.close()
    return path


def main():
    os.makedirs(WORK, exist_ok=True)

    # 1) default full-cover book (letter)
    default = copy.deepcopy(server.DEFAULTS)
    with open(os.path.join(WORK, 'export_default.pdf'), 'wb') as f:
        f.write(pdf_bytes(default))

    # 2) slip-cover book
    slip = copy.deepcopy(server.DEFAULTS)
    slip['coverTemplate'] = 'slip'
    with open(os.path.join(WORK, 'export_slipcover.pdf'), 'wb') as f:
        f.write(pdf_bytes(slip))

    # 3) A4 sheet preview (single A4 sheet, no cover)
    a4 = copy.deepcopy(server.DEFAULTS)
    a4['paper'] = 'a4'
    a4['coverEnabled'] = False
    a4['sheets'] = 1
    render_first(pdf_bytes(a4), os.path.join(WORK, 'a4_sheet.png'), zoom=2.0)

    # 4) carbon-copy sheet preview (letter, page 2 = blue carbon copy)
    carb = copy.deepcopy(server.DEFAULTS)
    carb['coverEnabled'] = False
    carb['sheets'] = 2
    render_first(pdf_bytes(carb), os.path.join(WORK, 'carbon_page.png'),
                 zoom=2.0, page=1)

    # 5) slip-cover preview (narrow receipt-piece cover)
    render_first(pdf_bytes(slip), os.path.join(WORK, 'slipcover.png'),
                 zoom=2.0, page=0)

    # 6) extra sheet previews (kept in sync with the others)
    render_first(pdf_bytes(default), os.path.join(WORK, 'export_p2.png'),
                 zoom=2.0, page=1)
    render_first(pdf_bytes(a4), os.path.join(WORK, 'export_custom.png'),
                 zoom=2.0, page=0)

    print('refreshed sample PDFs + preview PNGs in', WORK)


if __name__ == '__main__':
    main()
