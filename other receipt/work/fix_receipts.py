"""Fix jkpp.pdf receipts:
- triplicate numbering per sheet: sheet i (0-based) -> all 3 slips numbered f"{67+i:04d}"
- page 1 slip 3: remove stray 'w' glyph and the sliced 'Amount' header, re-insert clean 'Amount'
- drop trailing blank page 11
Everything else preserved as-is.
"""
import pymupdf

SRC = 'uploads/jkpp.pdf'
OUT = 'jkpp_fixed.pdf'
F3 = 'work/fonts/f27.ttf'   # Times New Roman Bold  (red numbers)
F4 = 'work/fonts/f35.ttf'   # Times New Roman Regular (table headers)

d = pymupdf.open(SRC)
f3 = pymupdf.Font(fontfile=F3)

for pg in range(10):
    p = d[pg]
    target = f'{67 + pg:04d}'
    num_spans, amount3, stray_w = [], None, None
    for b in p.get_text('dict')['blocks']:
        for l in b.get('lines', []):
            for s in l['spans']:
                if s['color'] == 16711680 and s['text'].strip():
                    num_spans.append(s)
                if pg == 0:
                    x0, y0 = s['bbox'][0], s['bbox'][1]
                    if s['text'] == 'w' and 630 < x0 < 650 and 230 < y0 < 240:
                        stray_w = s
                    if s['text'].startswith('Amount ') and x0 > 600:
                        amount3 = s
    num_spans.sort(key=lambda s: s['bbox'][0])
    assert len(num_spans) == 3, (pg, len(num_spans))

    # blank out the old red numbers (never touch line art)
    for s in num_spans:
        r = pymupdf.Rect(s['bbox']) + (-0.5, -1.0, 1.0, 1.0)
        p.add_redact_annot(r)
    if pg == 0:
        assert stray_w and amount3
        # remove the stray 'w' and the sliced original 'Amount' entirely
        r = pymupdf.Rect(stray_w['bbox']) + (-1, -1, 1, 1)
        p.add_redact_annot(r)
        r = pymupdf.Rect(amount3['bbox']) + (-1, -1, 1, 1)
        p.add_redact_annot(r)
    p.apply_redactions(graphics=pymupdf.PDF_REDACT_LINE_ART_NONE)

    if pg == 0:
        # single clean redraw of the header word
        p.insert_text(amount3['origin'], 'Amount ', fontfile=F4, fontsize=13.2, color=(0, 0, 0))

    # new triplicate numbers, right-aligned to the original right edge
    for s in num_spans:
        w = f3.text_length(target, 13.2)
        p.insert_text((s['bbox'][2] - w, s['origin'][1]), target,
                      fontfile=F3, fontsize=13.2, color=(1, 0, 0))
    print(f'page {pg+1}: slips -> {target} x3')

d.delete_page(10)  # trailing blank page
d.save(OUT, garbage=3, deflate=True)
print('saved', OUT, 'pages:', d.page_count)
