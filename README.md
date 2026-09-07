# Suahco4 — Receipt Platform

Design, preview and print receipts for **Suahco4, Brewerville, Liberia** — and
everything else Suahco4 issues or receives. The whole platform lives in **one
area** (this folder) and every receipt — all four book templates *and* the
40-receipt library — opens in **one editor**.

## Run the platform

```bash
python3 tools/platform_server.py      # then open http://localhost:8000
```

No dependencies: the editor runs fully in the browser (live preview + print /
save-as-PDF). Static hosting works the same way — put `index.html`, `assets/`
and `data/` on any web server and open `index.html`.

## The one editor

Everything opens in the **Receipt Editor** embedded in `index.html`:

| Open | What happens |
| --- | --- |
| `index.html?builder=1` | The editor with the default (simple) template |
| `index.html?template=simple\|itemized\|fees\|wide` | The editor on that template |
| `index.html?receipt=<id>` (e.g. `?receipt=school-0002`) | One of the 40 library receipts, filled and editable |
| `index.html` | The platform home page — templates grid + the 40-receipt library |

Inside the editor: pick a receipt from the **Receipt library** panel (all 40,
grouped by kind) or start from a blank template, edit header, fields, table
rows/values, numbering, copies, paper, cut lines and the optional book cover,
then **Export PDF / Print**. Your own receipts are saved per browser under
**My receipts**. There are no other editors any more — the old stand-alone
*Receipt Sheet Builder* (`receipts-app/`) and the scattered duplicate under
`other receipt/` were removed and its features (book cover, copy labels, cut
lines, stub, watermark) folded into this single editor.

## The 40-receipt library

`data/receipts.js` (mirrored as `data/receipts.json`) holds 40 ready receipts
of all kinds — school fees, tuition instalments, sales & market goods, catering,
pharmacy, hardware, auto, printing, tailoring, wholesale, church offerings,
weddings and funerals, community dues, rent and deposits, salary advances, loan
instalments, transport, water and fuel — spread across all four templates.

Edit `SPECS` in `tools/make_receipts_data.py` and re-run to change them:

```bash
python3 tools/make_receipts_data.py
```

## One area — the folder layout

```
index.html            platform home + the single receipt editor (the whole app)
receipt_book.html     old-link redirect -> the editor in index.html
data/                 the 40-receipt library (receipts.js + receipts.json)
assets/               logo, base64 logo source, template previews (previews/),
                      sheet preview images (sheets/)
docs/                 finished books (PDF + editable DOCX), all-in-one bundles,
                      samples/ (legacy builder exports), scans/ (uploaded jkpp
                      scans, the corrected PDF, source photo + fix script)
tools/                python utilities (all optional, see below)
```

## tools/

| Script | Purpose | Needs |
| --- | --- | --- |
| `platform_server.py` | Serve the platform on :8000 | nothing |
| `make_receipts_data.py` | Regenerate the 40-receipt library | nothing |
| `build_receipts.py` | Rebuild the four `docs/receipt_book*` books | reportlab, python-docx |
| `make_all_receipts_one.py` | Rebuild `docs/receipts_all_in_one.pdf/.docx` | reportlab, pypdf |
| `make_logo.py` | Re-render `assets/logo.png` + `logo_b64.txt` | Pillow |
| `receipt_book_app.py` | *Legacy* generator source kept for reference (the generator now lives in `index.html` — edit it there) | — |
| `make_samples.py` + `receipt_book_pdf.py` | *Legacy* sheet-model PDF engine that regenerates the `docs/samples/` books + `assets/sheets/` previews | reportlab, pymupdf |

## Ready-made documents

- `docs/receipt_book*.pdf|docx` — the four receipt-book templates (print-ready PDF + editable Word).
- `docs/receipts_all_in_one.pdf|docx` — every book in one file (the four templates + the scanned books + source photo).
- `docs/samples/` — sample books from the former sheet builder (default & slip-cover).
- `docs/scans/` — the uploaded `jkpp.pdf` scan, its corrected version `jkpp_fixed.pdf`, the source photo, the `fix_receipts.py` script that produced it, and its fonts.
