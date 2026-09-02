#!/usr/bin/env python3
"""
Combine every receipt document in the project into ONE file:

  receipts_all_in_one.pdf   — every receipt book / scanned book / export kept
                              exactly as designed, with a cover index, part
                              divider pages and PDF bookmarks.
  receipts_all_in_one.docx  — the four editable Word receipt books combined
                              into one .docx (each book keeps its own page
                              setup as a separate Word section).

Run:  python3 make_all_receipts_one.py
"""
import copy
import io
import os

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

ROOT = os.path.dirname(os.path.abspath(__file__))
ACCENT = HexColor('#B8121B')
INK = HexColor('#1f2937')
MUTED = HexColor('#6b7280')

OUT_PDF = os.path.join(ROOT, 'receipts_all_in_one.pdf')
OUT_DOCX = os.path.join(ROOT, 'receipts_all_in_one.docx')

# ---------------------------------------------------------------- PDF parts
# kind: "pdf" -> insert the file's pages untouched
#       "image" -> one page with the photo fitted + caption
#       "none"  -> spacer book (kept for bookmarks/consistency)
PARTS = [
    dict(kind='pdf', file='receipt_book.pdf', title='Simple Receipt Book',
         src='receipt_book.pdf + receipt_book.docx',
         desc='Blank-line receipt, 2 slips per A4 page - Original + Carbon Copy.',
         nums='Receipt No. GPSS-061 - GPSS-110 (50 receipts x 2 copies)'),
    dict(kind='pdf', file='receipt_book_itemized.pdf', title='Sales Receipt Book (Itemized)',
         src='receipt_book_itemized.pdf + receipt_book_itemized.docx',
         desc='Itemized table (Qty / Rate / Amount) with sub-total, discount, total.',
         nums='Receipt No. GPSS-061 - GPSS-110 (50 receipts x 2 copies)'),
    dict(kind='pdf', file='receipt_book_fees.pdf', title='School Fees Payment Slip Book',
         src='receipt_book_fees.pdf + receipt_book_fees.docx',
         desc='Fee breakdown: particulars / amount due / amount paid / balance.',
         nums='Receipt No. GPSS-061 - GPSS-110 (50 receipts x 2 copies)'),
    dict(kind='pdf', file='receipt_book_wide.pdf', title='Payment Receipt Book (Horizontal)',
         src='receipt_book_wide.pdf + receipt_book_wide.docx',
         desc='Horizontal A4-landscape receipt, 2 slips per page.',
         nums='Receipt No. GPSS-061 - GPSS-110 (50 receipts x 2 copies)'),
    dict(kind='pdf', file='uploads/jkpp.pdf', title='Uploaded Receipt Book - Original Scan/PDF',
         src='uploads/jkpp.pdf',
         desc='The scanned book exactly as it was uploaded (letter size).',
         nums='Receipts 0067 - 0081 as received (includes the trailing blank page)'),
    dict(kind='pdf', file='jkpp_fixed.pdf', title='Uploaded Receipt Book - Corrected',
         src='jkpp_fixed.pdf',
         desc='Same book with clean triplicate numbering, one receipt per page x 3 slips.',
         nums='Receipts 0067 - 0076, 10 pages'),
    dict(kind='pdf', file='receipts-app/work/export_default.pdf', title='Web App Export - Default Book',
         src='receipts-app/work/export_default.pdf',
         desc='Receipt Sheet Builder export with a full-page cover.',
         nums='Receipt Nos. 0001 - 0015 (originals + carbon copies)'),
    dict(kind='pdf', file='receipts-app/work/export_slipcover.pdf', title='Web App Export - Slip-Cover Book',
         src='receipts-app/work/export_slipcover.pdf',
         desc='Receipt Sheet Builder export with a receipt-piece cover.',
         nums='Receipt Nos. 0001 - 0015 (originals + carbon copies)'),
    dict(kind='image', file='uploads/IMG_20260901_115539_678.jpg', title='Appendix - Source Photo',
         src='uploads/IMG_20260901_115539_678.jpg',
         desc='Photo of the printed receipt that the books are based on.',
         nums='Photographed 2026-09-01'),
]

DOCX_FILES = [
    ('receipt_book.docx', 'Part 1 - Simple Receipt Book'),
    ('receipt_book_itemized.docx', 'Part 2 - Sales Receipt Book (Itemized)'),
    ('receipt_book_fees.docx', 'Part 3 - School Fees Payment Slip Book'),
    ('receipt_book_wide.docx', 'Part 4 - Payment Receipt Book (Horizontal)'),
]


def _mm(pt):
    return pt * mm if pt else pt


def make_cover_pdf(pdf_w, pdf_h, toc, total_pages):
    """One A4-portrait index/cover page.  `toc` = [(part_no, title, start_page)]."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(pdf_w, pdf_h))
    c.setTitle('All Receipts - One File')
    W, H = pdf_w, pdf_h
    # top band
    c.setFillColor(ACCENT)
    c.rect(0, H - 6 * mm, W, 6 * mm, stroke=0, fill=1)
    y = H - 24 * mm
    c.setFont('Helvetica-Bold', 10)
    c.setFillColor(ACCENT)
    c.drawCentredString(W / 2, y, 'COMBINED FILE  -  EVERY RECEIPT DOCUMENT IN ONE PDF')
    y -= 12 * mm
    c.setFont('Helvetica-Bold', 24)
    c.setFillColor(INK)
    c.drawCentredString(W / 2, y, 'ALL RECEIPTS - ONE FILE')
    y -= 9 * mm
    c.setFont('Helvetica', 10.5)
    c.setFillColor(MUTED)
    c.drawCentredString(W / 2, y, 'Greater Praise School System - each receipt book kept exactly as designed')
    y -= 18 * mm

    c.setFont('Helvetica-Bold', 13)
    c.setFillColor(INK)
    c.drawString(24 * mm, y, 'Contents')
    y -= 10 * mm

    # contents rows with dotted leaders
    c.setFont('Helvetica', 9.5)
    for part_no, title, start in toc:
        row_h = 9.5 * mm if len(title) < 42 else 14 * mm
        right = W - 24 * mm
        left = 24 * mm
        label = 'Part %d - %s' % (part_no, title)
        c.setFillColor(INK)
        c.drawString(left, y, label[:80])
        label_w = c.stringWidth(label[:80], 'Helvetica', 9.5)
        pageno = str(start + 1)   # cover itself is page 1
        pageno_w = c.stringWidth(pageno, 'Helvetica-Bold', 9.5)
        # dotted leader
        c.setFillColor(MUTED)
        dot_x = left + label_w + 4
        while dot_x < right - pageno_w - 6:
            c.drawString(dot_x, y, '.')
            dot_x += 6
        c.setFont('Helvetica-Bold', 9.5)
        c.setFillColor(INK)
        c.drawRightString(right, y, pageno)
        c.setFont('Helvetica', 9.5)
        y -= row_h
    y -= 4 * mm
    c.setFillColor(MUTED)
    c.setFont('Helvetica-Oblique', 8)
    c.drawString(24 * mm, y, 'Receipt pages are printed exactly as in their original files; dividers and this index are added for navigation.')
    y -= 5 * mm
    c.drawString(24 * mm, y, 'Total: %d pages (incl. this index)  -  generated %s' % (total_pages + 1, '2026-09-02'))
    # bottom band
    c.setFillColor(ACCENT)
    c.rect(0, 0, W, 3 * mm, stroke=0, fill=1)
    c.showPage()
    c.save()
    return buf.getvalue()
    c.save()
    return buf.getvalue()


def make_divider_pdf(pdf_w, pdf_h, part_no, cfg):
    """One divider page sized like the section that follows it."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(pdf_w, pdf_h))
    W, H = pdf_w, pdf_h
    # frame
    c.setStrokeColor(ACCENT)
    c.setLineWidth(1.4)
    c.rect(12 * mm, 12 * mm, W - 24 * mm, H - 24 * mm)
    c.setLineWidth(0.5)
    c.rect(14 * mm, 14 * mm, W - 28 * mm, H - 28 * mm)

    y = H - 30 * mm
    c.setFont('Helvetica-Bold', 11)
    c.setFillColor(ACCENT)
    c.drawCentredString(W / 2, y, 'PART %d' % part_no)
    y -= 13 * mm
    c.setFont('Helvetica-Bold', 19)
    c.setFillColor(INK)
    # wrap long titles
    words = cfg['title'].split()
    lines, cur = [], ''
    for w in words:
        test = (cur + ' ' + w).strip()
        if c.stringWidth(test, 'Helvetica-Bold', 19) < W - 40 * mm:
            cur = test
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    for ln in lines:
        c.drawCentredString(W / 2, y, ln)
        y -= 9.5 * mm

    y -= 8 * mm
    c.setFont('Helvetica', 11.5)
    c.setFillColor(INK)
    box = [cfg['desc'][i:i + 88] for i in range(0, len(cfg['desc']), 88)]
    for ln in box:
        c.drawCentredString(W / 2, y, ln)
        y -= 6 * mm
    y -= 6 * mm
    c.setFont('Helvetica', 10.5)
    c.setFillColor(MUTED)
    c.drawCentredString(W / 2, y, cfg['nums'])
    y -= 8 * mm
    c.setFont('Helvetica-Oblique', 8.5)
    c.drawCentredString(W / 2, y, 'kept exactly as in:  %s' % cfg['src'])
    c.showPage()
    c.save()
    return buf.getvalue()


def make_photo_pdf(pdf_w, pdf_h, path):
    """One page containing the source photo, fitted + caption."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(pdf_w, pdf_h))
    img = ImageReader(path)
    iw, ih = img.getSize()
    max_w, max_h = pdf_w - 36 * mm, pdf_h - 52 * mm
    scale = min(max_w / iw, max_h / ih)
    dw, dh = iw * scale, ih * scale
    c.drawImage(img, (pdf_w - dw) / 2, (pdf_h - dh) / 2 + 10 * mm,
                width=dw, height=dh, preserveAspectRatio=True, mask='auto')
    c.setFont('Helvetica-Oblique', 8.5)
    c.setFillColor(MUTED)
    c.drawCentredString(pdf_w / 2, 8 * mm,
                        'Source photo: uploads/IMG_20260901_115539_678.jpg  (printed receipt, photographed 2026-09-01)')
    c.showPage()
    c.save()
    return buf.getvalue()


def build_pdf():
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import NameObject

    writer = PdfWriter()

    blocks = []          # (type, cfg_or_path)
    for i, cfg in enumerate(PARTS, start=1):
        blocks.append(('divider', (i, cfg)))
        blocks.append((cfg['kind'], cfg))

    # page-size of each block (divider follows the part that comes after it)
    def part_page_size(cfg):
        if cfg['kind'] == 'pdf':
            r = PdfReader(os.path.join(ROOT, cfg['file']))
            p = r.pages[0].mediabox
            return float(p.width), float(p.height), r
        return float(A4[0]), float(A4[1]), None

    # pre-read sources
    sources = {}
    for cfg in PARTS:
        if cfg['kind'] == 'pdf':
            sources[cfg['file']] = part_page_size(cfg)

    # assemble toc info while building
    page_counter = 0
    toc = []
    part_num = 0

    for kind, cfg in blocks:
        if kind == 'divider':
            part_num, cfg2 = cfg
            w, h, _ = sources.get(cfg2['file'], (A4[0], A4[1], None)) if cfg2['kind'] == 'pdf' else (A4[0], A4[1], None)
            data = make_divider_pdf(w, h, part_num, cfg2)
            reader = PdfReader(io.BytesIO(data))
            writer.add_page(reader.pages[0])
            toc.append((part_num, cfg2['title'], page_counter + 1))
            page_counter += 1
        elif kind == 'pdf':
            r = sources[cfg['file']][2]
            for p in r.pages:
                writer.add_page(p)
                page_counter += 1
        elif kind == 'image':
            w, h = A4[0], A4[1]
            data = make_photo_pdf(w, h, os.path.join(ROOT, cfg['file']))
            reader = PdfReader(io.BytesIO(data))
            writer.add_page(reader.pages[0])
            page_counter += 1

    total_pages = page_counter
    # cover goes first (needs total + section starts)
    cover_data = make_cover_pdf(A4[0], A4[1], toc, total_pages)
    cover_reader = PdfReader(io.BytesIO(cover_data))
    cover = cover_reader.pages[0]

    # re-assemble final writer with cover prepended
    final = PdfWriter()
    final.add_page(cover)
    # copy the pages we already added (they live in `writer`)
    for p in writer.pages:
        final.add_page(p)

    # bookmarks for each part (page numbers are 1-based in PDF viewers)
    try:
        offset = 1  # cover is page 1
        for part_no, title, start in toc:
            final.add_outline_item('Part %d - %s' % (part_no, title), start + offset - 1)
    except Exception as e:
        print('  (bookmarks skipped:', e, ')')

    try:
        final.add_metadata({
            '/Title': 'All Receipts - One File (Greater Praise School System)',
            '/Author': 'Greater Praise School System',
            '/Subject': 'Combined receipt book: every receipt document in one PDF',
            '/Creator': 'make_all_receipts_one.py',
        })
    except Exception:
        pass

    with open(OUT_PDF, 'wb') as fh:
        final.write(fh)
    return total_pages, toc


# ----------------------------------------------------------------- DOCX
def docx_section_pg(pg):
    import re
    from docx.oxml.ns import qn
    sz = pg.find(qn('w:pgSz'))
    if sz is None:
        return None
    w = sz.get(qn('w:w'))
    h = sz.get(qn('w:h'))
    return (w, h)


def build_docx():
    from docx import Document
    from docx.opc.constants import RELATIONSHIP_TYPE as RT
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement

    R_NS = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'

    doc = Document()
    body = doc.element.body
    # drop the template's starter paragraph, keep its final sectPr to replace later
    final_sect = body.find(qn('w:sectPr'))
    for child in list(body):
        if child is not final_sect:
            body.remove(child)

    last = len(DOCX_FILES) - 1
    for idx, (fname, heading) in enumerate(DOCX_FILES):
        src = Document(os.path.join(ROOT, fname))
        src_body = src.element.body

        # --- remap image relationships (each book embeds the same logo) ---
        rid_map = {}
        for rid, rel in src.part.rels.items():
            if rel.reltype == RT.IMAGE:
                blob = rel.target_part.blob
                new_rid = doc.part.get_or_add_image(io.BytesIO(blob))
                if isinstance(new_rid, tuple):      # python-docx returns (rId, image)
                    new_rid = new_rid[0]
                rid_map[rid] = new_rid

        src_sect = None
        for child in list(src_body):
            if child.tag == qn('w:sectPr'):
                src_sect = child
                continue
            node = copy.deepcopy(child)
            # swap any relationship-id references to images in this subtree
            for el in node.iter():
                for attr, val in list(el.attrib.items()):
                    if val in rid_map:
                        el.set(attr, rid_map[val])
            body.insert(list(body).index(final_sect), node)

        if idx < last:
            # close this section: paragraph holding a copy of the source's page setup
            p = OxmlElement('w:p')
            pPr = OxmlElement('w:pPr')
            if src_sect is not None:
                pPr.append(copy.deepcopy(src_sect))
            p.append(pPr)
            body.insert(list(body).index(final_sect), p)
        else:
            # last book: its page setup becomes the document's final section
            if src_sect is not None:
                body.replace(final_sect, copy.deepcopy(src_sect))
                final_sect = body.find(qn('w:sectPr'))

    core = doc.core_properties
    core.title = 'All Receipts - One File (Greater Praise School System)'
    core.author = 'Greater Praise School System'
    core.comments = 'Simple, itemized, school-fees and horizontal receipt books combined; each book keeps its own page setup as a Word section.'
    doc.save(OUT_DOCX)
    return OUT_DOCX


if __name__ == '__main__':
    missing = [os.path.join(ROOT, p['file']) for p in PARTS if not os.path.exists(os.path.join(ROOT, p['file']))]
    if missing:
        print('Missing source files:\n -', '\n - '.join(missing))
        raise SystemExit(1)
    print('Building combined PDF ...')
    total, toc = build_pdf()
    print(' -> %s  (%d pages incl. cover + dividers)' % (OUT_PDF, total + 1))
    for i, (part_no, title, start) in enumerate(toc):
        nxt = toc[i + 1][2] if i + 1 < len(toc) else total
        print('    Part %d %-46s pages %d-%d' % (part_no, title[:46], start + 1, nxt + 1 if i + 1 < len(toc) else total + 1))
    print('Building combined DOCX ...')
    out = build_docx()
    print(' ->', out)
