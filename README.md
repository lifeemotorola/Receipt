# Suahco4 — Receipt Platform

Design, preview and print the official receipt book — originals and
carbon copies — for **Suahco4, Brewerville, Liberia**.

## Run the whole platform

```bash
pip install reportlab     # once (needed for PDF export)
python3 platform_server.py
```

Then open **http://localhost:8000** — the platform home page (`index.html`)
launches the **Receipt Sheet Builder** (`receipts-app/index.html`).

## Static hosting

No server is required for everyday use. Host (or just open) the repo and use:

| File | Purpose |
| --- | --- |
| `index.html` | Platform home page — start here |
| `receipts-app/index.html` | The Receipt Sheet Builder (covers, original/carbon sheets, numbering) |
| `index.html?template=simple` (or `itemized`, `fees`, `wide`) | Opens that template in the embedded Receipt Book Generator |
| `receipt_book.html` | Redirects to the generator in `index.html` (kept so old links still work) |
| `receipt_book*.pdf` / `receipt_book*.docx` | The four receipt-book templates |
| `receipts-app/work/export_default.pdf` | Sample book produced by the builder (default settings) |
| `receipts-app/work/export_slipcover.pdf` | Sample book with a receipt-piece cover |

The Builder works fully in the browser (preview + Print). The **Export PDF**
buttons additionally need `platform_server.py` running so the server can build
the PDF; otherwise use the Print dialog — the sheets are already print-ready.

## Ready-made documents

- `receipts_all_in_one.pdf` / `receipts_all_in_one.docx` — every receipt book in one file
  (simple, itemized, school-fees and horizontal books + the scanned books + source photo).
  Regenerate with `python3 make_all_receipts_one.py`.
- `receipt_book*.pdf|docx` — the four original receipt books.
- `build_receipts.py` — builds those four books (reportlab + python-docx).
