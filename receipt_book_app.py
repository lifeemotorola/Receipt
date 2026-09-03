"""Builds receipt_book.html — a self-contained receipt-book generator.

NOTE: the generator now lives inside index.html (open it with index.html?builder=1 or
index.html?template=simple|itemized|fees|wide), and receipt_book.html is a redirect to it.
Re-running this script would overwrite that redirect — update index.html instead."""
import base64, json, io
from PIL import Image

LOGO = open('logo_b64.txt').read().strip()

HTML = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Receipt Book Generator</title>
<style>
  :root{
    --ink:#111; --muted:#6b7280; --line:#d8dbe0; --bg:#eef1f5;
    --accent:#b8121b;
  }
  *{box-sizing:border-box}
  body{margin:0;font-family:"Segoe UI",system-ui,-apple-system,Arial,sans-serif;background:var(--bg);color:var(--ink)}
  header.app{background:#1f2937;color:#fff;padding:14px 20px;display:flex;align-items:center;gap:14px;flex-wrap:wrap}
  header.app h1{font-size:17px;margin:0;font-weight:650;letter-spacing:.2px}
  header.app .sp{flex:1}
  .btn{border:0;border-radius:7px;padding:9px 15px;font-size:13px;font-weight:600;cursor:pointer;background:#374151;color:#fff}
  .btn:hover{background:#4b5563}
  .btn.pri{background:#b8121b}.btn.pri:hover{background:#940f16}
  .btn.gr{background:#0f766e}.btn.gr:hover{background:#0b5c56}
  .btn.sm{padding:5px 10px;font-size:12px;border-radius:6px}
  .wrap{display:flex;align-items:flex-start;gap:18px;padding:18px;max-width:1500px;margin:0 auto}
  .panel{width:395px;flex:none;background:#fff;border-radius:12px;box-shadow:0 1px 3px rgba(0,0,0,.12);
         max-height:calc(100vh - 100px);overflow:auto;position:sticky;top:14px}
  .panel h2{font-size:12px;text-transform:uppercase;letter-spacing:.9px;color:var(--muted);
            margin:0;padding:13px 16px 9px;border-bottom:1px solid #eef0f3;background:#fafbfc;position:sticky;top:0;z-index:2}
  details{border-bottom:1px solid #eef0f3}
  summary{padding:11px 16px;font-size:13px;font-weight:650;cursor:pointer;user-select:none;background:#fff}
  summary:hover{background:#f7f8fa}
  .body{padding:6px 16px 16px}
  label.f{display:block;margin:9px 0 3px;font-size:11.5px;font-weight:600;color:#374151}
  input[type=text],input[type=number],input[type=color],select,textarea{
    width:100%;padding:7px 9px;border:1px solid var(--line);border-radius:6px;font-size:13px;font-family:inherit;background:#fff}
  textarea{resize:vertical;min-height:52px}
  input[type=color]{padding:2px;height:34px}
  .row{display:flex;gap:8px}.row>*{flex:1}
  .chk{display:flex;align-items:center;gap:7px;margin:7px 0;font-size:12.5px;font-weight:500}
  .chk input{width:15px;height:15px;margin:0;flex:none}
  .hint{font-size:11px;color:var(--muted);margin:5px 0 0;line-height:1.45}
  .fieldrow{display:flex;gap:6px;align-items:center;margin:6px 0;padding:6px;background:#f7f8fa;border-radius:7px}
  .fieldrow input[type=text]{flex:1;padding:5px 7px;font-size:12px}
  .fieldrow select{width:95px;padding:5px;font-size:11.5px}
  .grip{cursor:grab;color:#9ca3af;font-size:14px;padding:0 2px}
  .x{background:#fee2e2;color:#b91c1c;border:0;border-radius:5px;width:24px;height:24px;cursor:pointer;font-size:14px;line-height:1;flex:none}
  .stage{flex:1;min-width:0}
  .stagebar{display:flex;align-items:center;gap:10px;margin-bottom:12px;font-size:12.5px;color:#4b5563;flex-wrap:wrap}
  .zoomwrap{overflow:auto;padding-bottom:20px}
  /* ---------- PAGE / RECEIPT ---------- */
  .sheet{background:#fff;box-shadow:0 2px 10px rgba(0,0,0,.15);margin:0 auto 20px;
         display:flex;flex-direction:column;overflow:hidden;transform-origin:top center}
  .rcpt{position:relative;overflow:hidden;background:var(--paper,#fff);color:#111;
        display:flex;flex-direction:column;padding:var(--pad,5mm) var(--padx,6mm)}
  .rcpt.dash{border-bottom:2px dashed #999}
  .rcpt.solid{border-bottom:1px solid #333}
  .rc-in{border:1.2px solid #222;flex:1;display:flex;flex-direction:column;padding:3.2mm 4mm;position:relative}
  .rc-in.noborder{border:none;padding:1mm 0}
  .hdr{display:flex;align-items:flex-start;gap:3mm}
  .logo{flex:none;object-fit:contain}
  .hdrtxt{flex:1;text-align:center;min-width:0}
  .biz{font-weight:800;letter-spacing:.6px;line-height:1.05;margin:0}
  .addr{margin:.7mm 0 0;line-height:1.3}
  .rtitle{font-weight:800;letter-spacing:2px;margin:1.2mm 0 0}
  .meta{display:flex;justify-content:space-between;align-items:baseline;gap:4mm;margin-top:.6mm}
  .rno{font-weight:800;color:var(--accent)}
  .copytag{font-weight:800;letter-spacing:1.2px;text-transform:uppercase;opacity:.85}
  .fields{margin-top:1.6mm;flex:1;display:flex;flex-direction:column;gap:0}
  .fr{display:flex;align-items:flex-end;gap:2mm;padding:.35mm 0}
  .fr .lb{font-weight:700;white-space:nowrap;flex:none}
  .fr .ln{flex:1;border-bottom:.8px solid #333;min-height:1.05em}
  .fr .ln.val{font-weight:600;padding-left:1mm}
  .fr.half{width:100%}
  .pair{display:flex;gap:5mm}
  .pair>.fr{flex:1}
  .opts{display:flex;align-items:center;gap:3.2mm;flex-wrap:wrap;flex:1}
  .opt{display:flex;align-items:center;gap:1.1mm;white-space:nowrap}
  .box{display:inline-block;border:1px solid #333;flex:none}
  .foot{display:flex;justify-content:space-between;align-items:flex-end;gap:4mm;margin-top:auto;padding-top:2.2mm}
  .sig{text-align:center;min-width:38mm}
  .sigline{border-bottom:.8px solid #333;height:5.5mm}
  .sigcap{margin-top:.6mm;white-space:nowrap}
  .note{color:#555;font-style:italic;flex:1}
  .wm{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;pointer-events:none;
      font-weight:900;letter-spacing:6px;transform:rotate(-22deg);white-space:nowrap}
  .stub{flex:none;border-right:1.5px dashed #888;padding-right:3mm;margin-right:3mm;display:flex;flex-direction:column}
  .rc-flex{display:flex;flex:1}
  .rc-main{flex:1;display:flex;flex-direction:column;min-width:0}
  @media print{
    body{background:#fff}
    header.app,.panel,.stagebar{display:none !important}
    .wrap{padding:0;display:block;max-width:none}
    .zoomwrap{overflow:visible;padding:0}
    .sheet{box-shadow:none;margin:0;transform:none !important;page-break-after:always;break-after:page}
    .sheet:last-child{page-break-after:auto;break-after:auto}
    .rcpt{-webkit-print-color-adjust:exact;print-color-adjust:exact}
  }
</style>
</head>
<body>
<header class="app">
  <h1><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-3px;margin-right:6px" aria-hidden="true"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/><line x1="8" y1="13" x2="16" y2="13"/><line x1="8" y1="17" x2="13" y2="17"/></svg>Receipt Book Generator</h1>
  <span class="sp"></span>
  <button class="btn sm" id="btnSave">Save settings</button>
  <button class="btn sm" id="btnLoad">Load</button>
  <button class="btn sm" id="btnReset">Reset</button>
  <button class="btn gr" id="btnPdf">Export PDF / Print</button>
</header>

<div class="wrap">
  <div class="panel" id="panel">
    <h2>Customize everything</h2>

    <details open><summary><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-3px;margin-right:6px" aria-hidden="true"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg> Template</summary><div class="body">
      <label class="f">Receipt template</label>
      <select id="template">
        <option value="simple">1 &mdash; Blank lines (your original book)</option>
        <option value="itemized">2 &mdash; Itemized table with totals</option>
        <option value="fees">3 &mdash; School fees payment slip</option>
        <option value="wide">4 &mdash; Horizontal / landscape slip</option>
      </select>
      <p class="hint">Switching loads that template&rsquo;s fields, table and title. Your business header,
      numbering and copy settings are kept. Everything stays editable afterwards.</p>
      <button class="btn sm" id="btnReload">Reload this template&rsquo;s defaults</button>
    </div></details>

    <details open><summary><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-3px;margin-right:6px" aria-hidden="true"><path d="M3 21h18"/><path d="M5 21V5a1 1 0 0 1 1-1h8a1 1 0 0 1 1 1v16"/><path d="M15 9h4a1 1 0 0 1 1 1v11"/><line x1="8" y1="7" x2="8" y2="7"/><line x1="11" y1="7" x2="11" y2="7"/><line x1="8" y1="11" x2="8" y2="11"/><line x1="11" y1="11" x2="11" y2="11"/></svg> Business header</summary><div class="body">
      <label class="f">Business / school name</label>
      <input type="text" id="biz">
      <label class="f">Address line</label>
      <input type="text" id="addr">
      <label class="f">Contact line (phone / email)</label>
      <input type="text" id="contact">
      <label class="f">Extra line (optional)</label>
      <input type="text" id="extra">
      <label class="f">Document title</label>
      <input type="text" id="title">
      <label class="f">Header arrangement</label>
      <select id="headerStyle">
        <option value="stacked">Stacked &mdash; centred block (portrait look)</option>
        <option value="inline">Inline &mdash; name left, title + number right (horizontal look)</option>
      </select>
      <div class="row">
        <div><label class="f">Logo</label><input type="file" id="logoFile" accept="image/*" style="font-size:11px"></div>
        <div><label class="f">Logo width (mm)</label><input type="number" id="logoW" min="0" max="60" step="1"></div>
      </div>
      <div class="chk"><input type="checkbox" id="showLogo"><label for="showLogo">Show logo</label></div>
      <button class="btn sm" id="btnNoLogo" style="margin-top:4px">Remove logo image</button>
    </div></details>

    <details open><summary><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-3px;margin-right:6px" aria-hidden="true"><line x1="4" y1="9" x2="20" y2="9"/><line x1="4" y1="15" x2="20" y2="15"/><line x1="10" y1="3" x2="8" y2="21"/><line x1="16" y1="3" x2="14" y2="21"/></svg> Numbering</summary><div class="body">
      <div class="row">
        <div><label class="f">Prefix</label><input type="text" id="prefix"></div>
        <div><label class="f">Suffix</label><input type="text" id="suffix"></div>
      </div>
      <div class="row">
        <div><label class="f">Start number</label><input type="number" id="start" min="0"></div>
        <div><label class="f">Digits (pad)</label><input type="number" id="pad" min="1" max="10"></div>
      </div>
      <div class="row">
        <div><label class="f">How many receipts</label><input type="number" id="count" min="1" max="500"></div>
        <div><label class="f">Increment by</label><input type="number" id="step" min="1"></div>
      </div>
      <label class="f">Number label</label>
      <input type="text" id="noLabel">
      <div class="chk"><input type="checkbox" id="showSeq"><label for="showSeq">Show plain sequence tag (e.g. [Receipt #61])</label></div>
      <label class="f">Sequence tag template <span style="font-weight:400;color:#6b7280">— {n} = number</span></label>
      <input type="text" id="seqTpl">
      <p class="hint">Numbering runs across the book; the carbon copy always repeats its original's number.</p>
    </div></details>

    <details open><summary><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-3px;margin-right:6px" aria-hidden="true"><path d="M9 5H5a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-4"/><rect x="9" y="3" width="6" height="4" rx="1"/><line x1="9" y1="12" x2="15" y2="12"/><line x1="9" y1="16" x2="15" y2="16"/></svg> Fields on the receipt</summary><div class="body">
      <div id="fieldList"></div>
      <div class="row" style="margin-top:8px">
        <button class="btn sm" id="addLine">+ Line field</button>
        <button class="btn sm" id="addOpts">+ Checkbox row</button>
      </div>
      <p class="hint"><b>Line</b> = label + writing line. <b>Checkboxes</b> = label + tick boxes (comma-separated options).
      <b>Pair</b> puts a field side-by-side with the next one. <b>Ruled</b> adds extra blank writing lines.</p>
    </div></details>

    <details open id="secTable" style="display:none"><summary><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-3px;margin-right:6px" aria-hidden="true"><rect x="3" y="4" width="18" height="16" rx="2"/><line x1="3" y1="10" x2="21" y2="10"/><line x1="9" y1="10" x2="9" y2="20"/></svg> The table</summary><div class="body">
      <label class="f">Columns &mdash; one per line: <code>Heading | width | l/c/r</code></label>
      <textarea id="tblCols" style="min-height:90px"></textarea>
      <label class="f">Row labels &mdash; one per line (leave empty for numbered blank rows)</label>
      <textarea id="tblLabels" style="min-height:80px"></textarea>
      <div class="row">
        <div><label class="f">Blank rows (if no labels)</label><input type="number" id="tblRows" min="1" max="20"></div>
        <div><label class="f">Row height (mm)</label><input type="number" id="tblRowH" min="4" max="14" step="0.5"></div>
      </div>
      <label class="f">Totals rows &mdash; one per line</label>
      <textarea id="tblTotals" style="min-height:60px"></textarea>
      <div class="row">
        <div><label class="f">Heading shade</label><input type="color" id="headFill"></div>
        <div><label class="f">Totals shade</label><input type="color" id="totalFill"></div>
      </div>
      <div class="chk"><input type="checkbox" id="totalsRight"><label for="totalsRight">Totals only under the last columns</label></div>
    </div></details>

    <details id="secBelow" style="display:none"><summary><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-3px;margin-right:6px" aria-hidden="true"><line x1="12" y1="3" x2="12" y2="21"/><polyline points="6 15 12 21 18 15"/></svg> Fields below the table</summary><div class="body">
      <div id="fieldList2"></div>
      <div class="row" style="margin-top:8px">
        <button class="btn sm" id="addLine2">+ Line field</button>
        <button class="btn sm" id="addOpts2">+ Checkbox row</button>
      </div>
    </div></details>

    <details><summary><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-3px;margin-right:6px" aria-hidden="true"><path d="M12 20h9"/><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4z"/></svg> Footer</summary><div class="body">
      <label class="f">Signature caption(s) &mdash; comma-separated for two or three lines</label>
      <input type="text" id="sigCap">
      <label class="f">Footer note (left of signature)</label>
      <textarea id="footNote"></textarea>
      <div class="chk"><input type="checkbox" id="showSig"><label for="showSig">Show signature line</label></div>
    </div></details>

    <details open><summary><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-3px;margin-right:6px" aria-hidden="true"><rect x="9" y="9" width="12" height="12" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg> Copies &amp; paper</summary><div class="body">
      <label class="f">Copies per receipt number</label>
      <select id="copies">
        <option value="1">1 — original only</option>
        <option value="2">2 — original + carbon copy</option>
        <option value="3">3 — original + 2 copies</option>
      </select>
      <label class="f">Copy labels (comma-separated)</label>
      <input type="text" id="copyLabels">
      <label class="f">Copy paper tints (comma-separated colours)</label>
      <input type="text" id="copyTints">
      <div class="chk"><input type="checkbox" id="showCopyTag"><label for="showCopyTag">Print the copy label on each receipt</label></div>
      <div class="chk"><input type="checkbox" id="wm"><label for="wm">Watermark copies with their label</label></div>
      <div class="row">
        <div><label class="f">Watermark size (pt)</label><input type="number" id="wmSize" min="10" max="120"></div>
        <div><label class="f">Watermark opacity %</label><input type="number" id="wmOp" min="1" max="60"></div>
      </div>
      <label class="f">Copy order</label>
      <select id="copyOrder">
        <option value="page">Page of originals, then the same page as copies (stack &amp; cut together)</option>
        <option value="together">Keep a number's copies back-to-back</option>
        <option value="separate">All originals first, then all copies</option>
      </select>
    </div></details>

    <details open><summary><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-3px;margin-right:6px" aria-hidden="true"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/></svg> Page layout</summary><div class="body">
      <label class="f">Page size</label>
      <select id="page">
        <option value="210x297">A4 portrait — 210 x 297 mm</option>
        <option value="297x210">A4 landscape — 297 x 210 mm</option>
        <option value="216x279">US Letter portrait — 8.5 x 11 in</option>
        <option value="279x216">US Letter landscape</option>
        <option value="148x210">A5 portrait</option>
        <option value="210x148">A5 landscape</option>
        <option value="custom">Custom…</option>
      </select>
      <div class="row" id="customPage" style="display:none">
        <div><label class="f">Width mm</label><input type="number" id="pw"></div>
        <div><label class="f">Height mm</label><input type="number" id="ph"></div>
      </div>
      <label class="f">Receipts per page</label>
      <select id="perPage">
        <option value="1">1</option><option value="2">2</option>
        <option value="3">3</option><option value="4">4</option>
      </select>
      <div class="row">
        <div><label class="f">Page margin (mm)</label><input type="number" id="margin" min="0" max="30" step="1"></div>
        <div><label class="f">Inner padding (mm)</label><input type="number" id="ipad" min="0" max="20" step="1"></div>
      </div>
      <label class="f">Cut guide between receipts</label>
      <select id="cut">
        <option value="dash">Dashed tear line</option>
        <option value="solid">Solid line</option>
        <option value="none">None</option>
      </select>
      <div class="chk"><input type="checkbox" id="cutAll"><label for="cutAll">Cut line under every receipt (incl. the bottom one)</label></div>
      <div class="chk"><input type="checkbox" id="border"><label for="border">Box border around each receipt</label></div>
      <div class="chk"><input type="checkbox" id="stub"><label for="stub">Add tear-off stub on the left</label></div>
      <div class="row">
        <div><label class="f">Stub width (mm)</label><input type="number" id="stubW" min="10" max="70"></div>
        <div><label class="f">Stub fields (comma)</label><input type="text" id="stubF"></div>
      </div>
    </div></details>

    <details><summary><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-3px;margin-right:6px" aria-hidden="true"><circle cx="12" cy="12" r="9"/><circle cx="8.5" cy="9.5" r="1"/><circle cx="12" cy="7.5" r="1"/><circle cx="15.5" cy="9.5" r="1"/></svg> Type &amp; colour</summary><div class="body">
      <label class="f">Font family</label>
      <select id="font">
        <option value="Arial,Helvetica,sans-serif">Arial / Helvetica</option>
        <option value="'Times New Roman',Times,serif">Times New Roman</option>
        <option value="Georgia,serif">Georgia</option>
        <option value="'Courier New',monospace">Courier New</option>
        <option value="Verdana,Geneva,sans-serif">Verdana</option>
        <option value="'Trebuchet MS',sans-serif">Trebuchet MS</option>
      </select>
      <div class="row">
        <div><label class="f">Base text (pt)</label><input type="number" id="fs" min="5" max="16" step="0.5"></div>
        <div><label class="f">Business name (pt)</label><input type="number" id="fsBiz" min="8" max="34" step="0.5"></div>
      </div>
      <div class="row">
        <div><label class="f">Address (pt)</label><input type="number" id="fsAddr" min="4" max="14" step="0.5"></div>
        <div><label class="f">Title (pt)</label><input type="number" id="fsTitle" min="6" max="22" step="0.5"></div>
      </div>
      <div class="row">
        <div><label class="f">Number colour</label><input type="color" id="cAccent"></div>
        <div><label class="f">Text colour</label><input type="color" id="cText"></div>
      </div>
      <div class="row">
        <div><label class="f">Line spacing</label><input type="number" id="gap" min="0" max="8" step="0.2"></div>
        <div><label class="f">Label width (mm, 0=auto)</label><input type="number" id="labW" min="0" max="60"></div>
      </div>
    </div></details>

    <details><summary><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-3px;margin-right:6px" aria-hidden="true"><path d="M12 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M15 3l6 6-9 9-4 1 1-4z"/></svg> Pre-fill values (optional)</summary><div class="body">
      <p class="hint">Type a value to print it on every receipt instead of a blank line. Leave empty for handwriting.</p>
      <div id="prefillList"></div>
    </div></details>
  </div>

  <div class="stage">
    <div class="stagebar">
      <b id="statLine">—</b>
      <span class="sp" style="flex:1"></span>
      <label style="font-size:12px">Zoom</label>
      <input type="range" id="zoom" min="30" max="150" value="70" style="width:150px">
      <span id="zoomv">70%</span>
      <button class="btn sm" id="btnPrev">Preview 1st page only</button>
    </div>
    <div class="zoomwrap" id="out"></div>
  </div>
</div>

<script>
const DEFAULT_LOGO = "__LOGO__";

const DEFAULTS = {
  biz:"Suahco4",
  addr:"COW FARM, NEW ISRAEL COMMUNITY, BREWERVILLE -LIBERIA",
  contact:"Phone: 0778662590 | Email:",
  extra:"",
  title:"RECEIPT",
  logo: DEFAULT_LOGO, showLogo:true, logoW:14,
  prefix:"SUAHCO4-", suffix:"", start:1, pad:3, count:50, step:1,
  noLabel:"Receipt No:", showSeq:true, seqTpl:"[Receipt #{n}]",
  fields:[
    {t:"line", label:"Date:",           pair:true,  ruled:0, val:""},
    {t:"line", label:"Received from:",  pair:false, ruled:0, val:""},
    {t:"line", label:"The sum of:",     pair:false, ruled:1, val:""},
    {t:"line", label:"For:",            pair:false, ruled:1, val:""},
    {t:"line", label:"Amount Paid$:",   pair:true,  ruled:0, val:""},
    {t:"line", label:"Balance:",        pair:false, ruled:0, val:""},
    {t:"opts", label:"Payment Method:", opts:"Cash, Check, Card, Transfer", pair:false, val:""},
    {t:"opts", label:"Currency:",       opts:"USD, LRD",                    pair:false, val:""}
  ],
  sigCap:"Authorized Signature", footNote:"", showSig:true,
  copies:2, copyLabels:"ORIGINAL, CARBON COPY", copyTints:"#ffffff, #d9eef7",
  showCopyTag:true, wm:false, wmSize:44, wmOp:8, copyOrder:"page",
  page:"210x297", pw:210, ph:297, perPage:3, margin:7, ipad:3,
  cut:"dash", cutAll:true, border:true, stub:false, stubW:35, stubF:"No., Date, Amount",
  font:"Arial,Helvetica,sans-serif", fs:7.5, fsBiz:13, fsAddr:5.8, fsTitle:8.5,
  cAccent:"#b8121b", cText:"#111111", gap:1.4, labW:0
};
DEFAULTS.template="simple";
DEFAULTS.headerStyle="stacked";
DEFAULTS.fields2=[];
DEFAULTS.tbl={cols:"", labels:"", rows:6, rowH:6.5, totals:"", headFill:"#e9edf2", totalFill:"#f4f6f8", totalsRight:true};

const TEMPLATES = {
  simple:{
    title:"RECEIPT", perPage:3, fs:7.5, fsBiz:13, fsTitle:8.5, sigCap:"Authorized Signature",
    fields: DEFAULTS.fields, fields2:[],
    tbl:{cols:"",labels:"",rows:6,rowH:6.5,totals:"",headFill:"#e9edf2",totalFill:"#f4f6f8",totalsRight:true}
  },
  itemized:{
    title:"SALES RECEIPT", perPage:2, fs:8, fsBiz:15, fsTitle:9.5, sigCap:"Authorized Signature",
    fields:[
      {t:"line",label:"Date:",pair:true,ruled:0,val:""},
      {t:"line",label:"Received from:",pair:false,ruled:0,val:""}
    ],
    fields2:[
      {t:"line",label:"Amount in words:",pair:false,ruled:0,val:""},
      {t:"opts",label:"Payment Method:",opts:"Cash, Check, Card, Transfer",pair:false,val:""},
      {t:"opts",label:"Currency:",opts:"USD, LRD",pair:false,val:""}
    ],
    tbl:{cols:"# | 0.6 | c\nDESCRIPTION | 6 | l\nQTY | 1 | c\nRATE | 1.6 | r\nAMOUNT | 1.9 | r",
         labels:"", rows:6, rowH:6.5, totals:"Sub-Total\nDiscount\nTOTAL",
         headFill:"#e9edf2", totalFill:"#f4f6f8", totalsRight:true}
  },
  fees:{
    title:"SCHOOL FEES PAYMENT SLIP", perPage:2, fs:8, fsBiz:15, fsTitle:9.5,
    sigCap:"Parent / Guardian, Bursar / Cashier",
    footNote:"Keep this slip safe \u2014 it is your proof of payment.",
    fields:[
      {t:"line",label:"Student Name:",pair:false,ruled:0,val:""},
      {t:"line",label:"Student ID:",pair:true,ruled:0,val:""},
      {t:"line",label:"Class / Grade:",pair:false,ruled:0,val:""},
      {t:"line",label:"Academic Year:",pair:true,ruled:0,val:""},
      {t:"opts",label:"Term:",opts:"1st Term, 2nd Term, 3rd Term",pair:false,val:""}
    ],
    fields2:[
      {t:"line",label:"Amount in words:",pair:false,ruled:0,val:""},
      {t:"opts",label:"Payment Method:",opts:"Cash, Check, Card, Transfer",pair:false,val:""},
      {t:"opts",label:"Currency:",opts:"USD, LRD",pair:false,val:""},
      {t:"line",label:"Balance Carried Forward:",pair:true,ruled:0,val:""},
      {t:"line",label:"Next Payment Due:",pair:false,ruled:0,val:""}
    ],
    tbl:{cols:"PARTICULARS | 4.6 | l\nAMOUNT DUE | 2 | r\nAMOUNT PAID | 2 | r\nBALANCE | 2 | r",
         labels:"Tuition Fee\nRegistration Fee\nUniform\nBooks / Materials\nExamination Fee\nOther (specify)",
         rows:6, rowH:6.5, totals:"TOTAL",
         headFill:"#e9edf2", totalFill:"#f4f6f8", totalsRight:false}
  }
,
  wide:{
    title:"PAYMENT RECEIPT", perPage:2, fs:8.5, fsBiz:15, fsAddr:6.4, fsTitle:11,
    sigCap:"Authorized Signature", headerStyle:"inline",
    page:"297x210", margin:8, ipad:3,
    fields:[
      {t:"line",label:"Date:",pair:true,ruled:0,val:""},
      {t:"line",label:"Received from:",pair:false,ruled:0,val:""},
      {t:"line",label:"The sum of:",pair:false,ruled:1,val:""},
      {t:"line",label:"Being payment for:",pair:false,ruled:0,val:""},
      {t:"line",label:"Amount Paid$:",pair:true,ruled:0,val:""},
      {t:"line",label:"Balance:",pair:false,ruled:0,val:""},
      {t:"opts",label:"Payment Method:",opts:"Cash, Check, Card, Transfer",pair:true,val:""},
      {t:"opts",label:"Currency:",opts:"USD, LRD",pair:false,val:""}
    ],
    fields2:[],
    tbl:{cols:"",labels:"",rows:6,rowH:6.5,totals:"",headFill:"#e9edf2",totalFill:"#f4f6f8",totalsRight:true}
  }
};

function loadTemplate(name){
  const t = TEMPLATES[name];
  S.template = name;
  S.fields  = JSON.parse(JSON.stringify(t.fields));
  S.fields2 = JSON.parse(JSON.stringify(t.fields2));
  S.tbl     = JSON.parse(JSON.stringify(t.tbl));
  ["title","perPage","fs","fsBiz","fsAddr","fsTitle","sigCap","headerStyle","page","margin","ipad"].forEach(k=>{ if(t[k]!==undefined) S[k]=t[k]; });
  S.footNote = t.footNote || "";
  if(t.headerStyle===undefined) S.headerStyle="stacked";
  if(t.page===undefined){ S.page="210x297"; S.margin=7; S.ipad=3; }
  push();
}

let S = JSON.parse(JSON.stringify(DEFAULTS));
let previewOnly = false;

const $ = id => document.getElementById(id);
const SIMPLE = ["template","headerStyle","biz","addr","contact","extra","title","logoW","prefix","suffix","start","pad","count","step",
  "noLabel","seqTpl","sigCap","footNote","copies","copyLabels","copyTints","wmSize","wmOp","copyOrder",
  "page","pw","ph","perPage","margin","ipad","cut","stubW","stubF","font","fs","fsBiz","fsAddr","fsTitle",
  "cAccent","cText","gap","labW"];
const TBL = {tblCols:"cols",tblLabels:"labels",tblRows:"rows",tblRowH:"rowH",tblTotals:"totals",headFill:"headFill",totalFill:"totalFill",totalsRight:"totalsRight"};
const BOOLS = ["showLogo","showSeq","showSig","showCopyTag","wm","border","stub","cutAll"];
const NUMS = ["logoW","start","pad","count","step","copies","wmSize","wmOp","pw","ph","perPage","margin",
  "ipad","stubW","fs","fsBiz","fsAddr","fsTitle","gap","labW"];

function pull(){
  SIMPLE.forEach(k=>{ const e=$(k); if(!e) return; S[k] = NUMS.includes(k) ? (parseFloat(e.value)||0) : e.value; });
  BOOLS.forEach(k=>{ const e=$(k); if(e) S[k]=e.checked; });
  Object.entries(TBL).forEach(([id,k])=>{ const e=$(id); if(!e) return;
    S.tbl[k] = e.type==="checkbox" ? e.checked : (e.type==="number" ? (parseFloat(e.value)||0) : e.value); });
  $("customPage").style.display = S.page==="custom" ? "flex" : "none";
  syncSections();
}
function syncSections(){
  const t = (S.template==="itemized" || S.template==="fees");
  $("secTable").style.display = t ? "" : "none";
  $("secBelow").style.display = t ? "" : "none";
  document.querySelector("#fieldList").closest("details").querySelector("summary").innerHTML =
    t ? "Fields above the table" : "Fields on the receipt";
}
function push(){
  SIMPLE.forEach(k=>{ const e=$(k); if(e) e.value = S[k]; });
  BOOLS.forEach(k=>{ const e=$(k); if(e) e.checked = !!S[k]; });
  Object.entries(TBL).forEach(([id,k])=>{ const e=$(id); if(!e) return;
    if(e.type==="checkbox") e.checked=!!S.tbl[k]; else e.value=S.tbl[k]; });
  $("customPage").style.display = S.page==="custom" ? "flex" : "none";
  syncSections(); drawFields(); drawFields2(); drawPrefill();
}

/* ---------- field editor ---------- */
function drawFieldsInto(listId, arrName){
  const w=$(listId); w.innerHTML="";
  S[arrName].forEach((f,i)=>{
    const d=document.createElement("div"); d.className="fieldrow"; d.draggable=true; d.dataset.i=i;
    d.innerHTML = `<span class="grip">&#8942;&#8942;</span>
      <input type="text" value="${esc(f.label)}" data-k="label" placeholder="Label">
      ${f.t==="opts" ? `<input type="text" value="${esc(f.opts||"")}" data-k="opts" placeholder="Option, Option">`
        : `<select data-k="ruled" title="extra blank lines"><option value="0">no extra</option><option value="1">+1 line</option><option value="2">+2 lines</option><option value="3">+3 lines</option></select>`}
      <label style="font-size:11px;display:flex;align-items:center;gap:3px" title="place side-by-side with next field">
        <input type="checkbox" data-k="pair" ${f.pair?"checked":""} style="width:13px;height:13px">pair</label>
      <button class="x" data-del="${i}">&times;</button>`;
    if(f.t==="line") d.querySelector('[data-k=ruled]').value = f.ruled||0;
    w.appendChild(d);
  });
  w.querySelectorAll("input,select").forEach(el=>{
    el.addEventListener("input",e=>{
      const i=+e.target.closest(".fieldrow").dataset.i, k=e.target.dataset.k;
      S[arrName][i][k] = k==="pair" ? e.target.checked : (k==="ruled" ? +e.target.value : e.target.value);
      if(k==="label") drawPrefill();
      render();
    });
  });
  w.querySelectorAll("[data-del]").forEach(b=>b.onclick=e=>{
    S[arrName].splice(+e.target.dataset.del,1); drawFieldsInto(listId,arrName); drawPrefill(); render();
  });
  let src=null;
  w.querySelectorAll(".fieldrow").forEach(r=>{
    r.addEventListener("dragstart",e=>{src=+r.dataset.i; r.style.opacity=.4});
    r.addEventListener("dragend",()=>r.style.opacity=1);
    r.addEventListener("dragover",e=>e.preventDefault());
    r.addEventListener("drop",e=>{e.preventDefault();
      const t=+r.dataset.i; if(src===null||src===t) return;
      const [m]=S[arrName].splice(src,1); S[arrName].splice(t,0,m); drawFieldsInto(listId,arrName); drawPrefill(); render();});
  });
}
function drawFields(){  drawFieldsInto("fieldList","fields"); }
function drawFields2(){ if($("fieldList2")) drawFieldsInto("fieldList2","fields2"); }

function drawPrefill(){
  const w=$("prefillList"); w.innerHTML="";
  ["fields","fields2"].forEach(arr=>{
    (S[arr]||[]).forEach((f,i)=>{
      const d=document.createElement("div");
      d.innerHTML=`<label class="f">${esc(f.label||"(field "+(i+1)+")")}</label>
        <input type="text" data-pa="${arr}" data-pi="${i}" value="${esc(f.val||"")}" placeholder="leave blank to handwrite">`;
      w.appendChild(d);
    });
  });
  w.querySelectorAll("[data-pi]").forEach(el=>el.addEventListener("input",e=>{
    S[e.target.dataset.pa][+e.target.dataset.pi].val=e.target.value; render();}));
}
const esc = s => String(s??"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));

/* ---------- rendering ---------- */
function pageDims(){
  if(S.page==="custom") return [S.pw||210, S.ph||297];
  const [w,h]=S.page.split("x").map(Number); return [w,h];
}
function num(i){
  const n = S.start + i*S.step;
  return S.prefix + String(n).padStart(S.pad,"0") + S.suffix;
}
function fieldHTML(f){
  const labStyle = S.labW>0 ? `style="width:${S.labW}mm"` : "";
  if(f.t==="opts"){
    const bs = (S.fs*1.25).toFixed(2)+"pt";
    const opts=(f.opts||"").split(",").map(o=>o.trim()).filter(Boolean)
      .map(o=>`<span class="opt"><span class="box" style="width:${bs};height:${bs}"></span>${esc(o)}</span>`).join("");
    return `<div class="fr" style="padding:${S.gap*0.35}mm 0"><span class="lb" ${labStyle}>${esc(f.label)}</span><span class="opts">${opts}</span></div>`;
  }
  let h=`<div class="fr" style="padding:${S.gap*0.35}mm 0"><span class="lb" ${labStyle}>${esc(f.label)}</span><span class="ln${f.val?" val":""}">${esc(f.val||"")}</span></div>`;
  for(let k=0;k<(f.ruled||0);k++)
    h+=`<div class="fr" style="padding:${S.gap*0.35}mm 0"><span class="ln"></span></div>`;
  return h;
}
function fieldsBlock(list){
  const F = list || S.fields;
  let out="", i=0;
  while(i<F.length){
    const f=F[i];
    if(f.pair && F[i+1] && !(f.ruled>0)){
      out += `<div class="pair">${fieldHTML(f)}${fieldHTML(F[i+1])}</div>`; i+=2;
    } else { out += fieldHTML(f); i++; }
  }
  return out;
}

/* ---------- the items / fee table ---------- */
function tableHTML(){
  const T=S.tbl;
  const cols=(T.cols||"").split("\n").map(l=>l.trim()).filter(Boolean).map(l=>{
    const p=l.split("|").map(x=>x.trim());
    return {h:p[0]||"", w:parseFloat(p[1])||1, a:(p[2]||"l").toLowerCase()};
  });
  if(!cols.length) return "";
  const labels=(T.labels||"").split("\n").map(x=>x.trim()).filter(Boolean);
  const totals=(T.totals||"").split("\n").map(x=>x.trim()).filter(Boolean);
  const tw=cols.reduce((a,c)=>a+c.w,0);
  const AL={l:"left",c:"center",r:"right"};
  const nBody = labels.length || Math.max(1,T.rows|0);
  const rh = (T.rowH||6.5)+"mm";

  let h=`<table style="width:100%;border-collapse:collapse;table-layout:fixed;
      font-size:${S.fs}pt;border:.9px solid #333;margin:1.5mm 0">
    <colgroup>${cols.map(c=>`<col style="width:${(c.w/tw*100).toFixed(3)}%">`).join("")}</colgroup><tr>`;
  cols.forEach(c=>{h+=`<th style="background:${T.headFill};border:.5px solid #333;padding:.9mm 1.4mm;
      text-align:${AL[c.a]};font-size:${(S.fs*.95).toFixed(2)}pt;font-weight:700">${esc(c.h)}</th>`;});
  h+="</tr>";
  for(let r=0;r<nBody;r++){
    h+="<tr>";
    cols.forEach((c,j)=>{
      const txt = j===0 ? (labels.length ? esc(labels[r]) : String(r+1)) : "";
      const al  = j===0 ? (labels.length ? "left" : "center") : AL[c.a];
      h+=`<td style="border:.5px solid #333;height:${rh};padding:.6mm 1.4mm;text-align:${al}">${txt}</td>`;
    });
    h+="</tr>";
  }
  totals.forEach((t,ti)=>{
    const last = ti===totals.length-1;
    const span = T.totalsRight ? Math.max(1,cols.length-2) : cols.length-1;
    const skip = T.totalsRight ? cols.length-2-span : 0;
    h+="<tr>";
    if(T.totalsRight && cols.length>2)
      h+=`<td colspan="${cols.length-2}" style="border:none"></td>`;
    h+=`<td colspan="${T.totalsRight?1:cols.length-1}" style="background:${T.totalFill};
        border:.5px solid #333;height:${rh};padding:.6mm 1.4mm;text-align:right;
        font-weight:${last?700:400};${last?"border-top:1px solid #333":""}">${esc(t)}</td>`;
    h+=`<td style="background:${T.totalFill};border:.5px solid #333;height:${rh};
        ${last?"border-top:1px solid #333":""}"></td>`;
    h+="</tr>";
  });
  return h+"</table>";
}
function receiptHTML(idx, copyIdx, tints, labels){
  const tint = tints[copyIdx] || "#fff";
  const label = labels[copyIdx] || "";
  const n = num(idx);
  const seqN = S.start + idx*S.step;
  const logo = (S.showLogo && S.logo)
      ? `<img class="logo" src="${S.logo}" style="width:${S.logoW}mm">` : "";
  const wmHTML = S.wm && label
      ? `<div class="wm" style="font-size:${S.wmSize}pt;color:${S.cText};opacity:${S.wmOp/100}">${esc(label)}</div>` : "";
  let stubHTML="";
  if(S.stub){
    const rows=(S.stubF||"").split(",").map(x=>x.trim()).filter(Boolean)
      .map(x=>`<div class="fr" style="padding:${S.gap*0.4}mm 0"><span class="lb">${esc(x)}</span><span class="ln"></span></div>`).join("");
    stubHTML=`<div class="stub" style="width:${S.stubW}mm">
        <div class="rno" style="font-size:${(S.fs*1.05).toFixed(2)}pt;margin-bottom:1.5mm">${esc(n)}</div>
        ${rows}</div>`;
  }
  return `<div class="rcpt ${S.cut}" style="--paper:${tint};color:${S.cText};padding:${S.ipad}mm ${S.ipad}mm">
    ${wmHTML}
    <div class="rc-in ${S.border?"":"noborder"}">
      <div class="rc-flex">
        ${stubHTML}
        <div class="rc-main">
          ${S.headerStyle==="inline" ? `
          <div class="hdr" style="align-items:flex-start">
            ${logo}
            <div style="flex:1;text-align:left;min-width:0">
              <p class="biz" style="font-size:${S.fsBiz}pt;text-align:left">${esc(S.biz)}</p>
              ${S.addr?`<p class="addr" style="font-size:${S.fsAddr}pt;text-align:left">${esc(S.addr)}</p>`:""}
              ${S.contact?`<p class="addr" style="font-size:${S.fsAddr}pt;text-align:left">${esc(S.contact)}</p>`:""}
              ${S.extra?`<p class="addr" style="font-size:${S.fsAddr}pt;text-align:left">${esc(S.extra)}</p>`:""}
            </div>
            <div style="text-align:right;flex:none">
              <p class="rtitle" style="font-size:${S.fsTitle}pt;margin:0">${esc(S.title)}</p>
              <p class="rno" style="font-size:${(S.fs*1.1).toFixed(2)}pt;color:${S.cAccent};margin:.8mm 0 0">${esc(S.noLabel)} ${esc(n)}</p>
              ${S.showCopyTag && label ? `<p class="copytag" style="font-size:${(S.fs*0.92).toFixed(2)}pt;margin:.5mm 0 0">${esc(label)}</p>`:""}
            </div>
          </div>
          <div style="border-bottom:.9px solid #333;margin:.8mm 0 0"></div>
          ` : `
          <div class="hdr">
            ${logo}
            <div class="hdrtxt">
              <p class="biz" style="font-size:${S.fsBiz}pt">${esc(S.biz)}</p>
              ${S.addr?`<p class="addr" style="font-size:${S.fsAddr}pt">${esc(S.addr)}</p>`:""}
              ${S.contact?`<p class="addr" style="font-size:${S.fsAddr}pt">${esc(S.contact)}</p>`:""}
              ${S.extra?`<p class="addr" style="font-size:${S.fsAddr}pt">${esc(S.extra)}</p>`:""}
              <p class="rtitle" style="font-size:${S.fsTitle}pt">${esc(S.title)}</p>
            </div>
            ${S.showLogo && S.logo ? `<span style="width:${S.logoW}mm;flex:none"></span>` : ""}
          </div>
          <div class="meta">
            <span class="rno" style="font-size:${(S.fs*1.1).toFixed(2)}pt;color:${S.cAccent}">${esc(S.noLabel)} ${esc(n)}</span>
            ${S.showCopyTag && label ? `<span class="copytag" style="font-size:${(S.fs*0.92).toFixed(2)}pt">${esc(label)}</span>`:""}
          </div>`}
          <div class="fields">${
            S.template==="simple"
              ? fieldsBlock(S.fields)
              : fieldsBlock(S.fields) + tableHTML() + fieldsBlock(S.fields2)
          }</div>
          <div class="foot">
            <span class="note" style="font-size:${(S.fs*0.85).toFixed(2)}pt">
              ${esc(S.footNote)}${S.showSeq?`<span style="display:block">${esc((S.seqTpl||"").replace("{n}",seqN))}</span>`:""}
            </span>
            ${S.showSig ? (S.sigCap||"").split(",").map(c=>c.trim()).filter(Boolean).map(c=>
              `<span class="sig"><span class="sigline" style="display:block"></span>
               <span class="sigcap" style="font-size:${(S.fs*0.85).toFixed(2)}pt;display:block">${esc(c)}</span></span>`).join("") : ""}
          </div>
        </div>
      </div>
    </div>
  </div>`;
}
function render(){
  const [W,H]=pageDims();
  const labels=(S.copyLabels||"").split(",").map(x=>x.trim());
  const tints=(S.copyTints||"").split(",").map(x=>x.trim());
  const copies=Math.max(1,Math.min(3,S.copies|0));
  // build ordered list of [receiptIndex, copyIndex]
  const per=Math.max(1,S.perPage|0);
  let seq=[];
  if(S.copyOrder==="separate"){
    for(let c=0;c<copies;c++) for(let i=0;i<S.count;i++) seq.push([i,c]);
  } else if(S.copyOrder==="together"){
    for(let i=0;i<S.count;i++) for(let c=0;c<copies;c++) seq.push([i,c]);
  } else {
    for(let b=0;b<S.count;b+=per){
      const grp=[]; for(let i=b;i<Math.min(b+per,S.count);i++) grp.push(i);
      for(let c=0;c<copies;c++){
        grp.forEach(i=>seq.push([i,c]));
        for(let k=grp.length;k<per;k++) seq.push([null,c]);
      }
    }
  }
  const inner=H - 2*S.margin;
  let html="", pages=0;
  for(let p=0;p<seq.length;p+=per){
    pages++;
    if(previewOnly && pages>1) break;
    let cells="";
    for(let k=0;k<per;k++){
      const item=seq[p+k];
      cells += (item && item[0]!==null) ? receiptHTML(item[0],item[1],tints,labels)
                    : `<div class="rcpt ${S.cut}" style="background:#fff"></div>`;
    }
    html += `<div class="sheet" style="width:${W}mm;height:${H}mm;padding:${S.margin}mm;
       font-family:${S.font};font-size:${S.fs}pt">
       <div style="flex:1;display:flex;flex-direction:column">${cells.replace(/class="rcpt /g,`class="rcpt `)}</div></div>`;
  }
  $("out").innerHTML=html;
  document.querySelectorAll(".sheet .rcpt").forEach(r=>{ r.style.flex="1"; r.style.minHeight="0"; });
  // remove cut line on last receipt of each page
  document.querySelectorAll(".sheet").forEach(s=>{
    const rs=s.querySelectorAll(".rcpt");
    if(rs.length && !S.cutAll) rs[rs.length-1].classList.remove("dash","solid");
  });
  applyZoom();
  const totalPages=Math.ceil(seq.length/per);
  $("statLine").textContent=`${S.count} receipt number${S.count>1?"s":""} x ${copies} cop${copies>1?"ies":"y"} = ${seq.length} slips - ${totalPages} page${totalPages>1?"s":""} (${W}x${H}mm, ${per}/page)`
    + (previewOnly ? "  -  showing page 1 only" : "");
}
function applyZoom(){
  const z=+$("zoom").value/100; $("zoomv").textContent=Math.round(z*100)+"%";
  const [W,H]=pageDims();
  document.querySelectorAll(".sheet").forEach(s=>{
    s.style.transform=`scale(${z})`;
    s.style.marginBottom=(20 - H*(1-z)*3.78)+"px";
  });
  $("out").style.textAlign="center";
}

/* ---------- wiring ---------- */
function bindAll(){
  SIMPLE.concat(BOOLS).forEach(k=>{ const e=$(k); if(e) e.addEventListener("input",()=>{pull();render();}); });
  $("zoom").addEventListener("input",applyZoom);
  Object.keys(TBL).forEach(id=>{ const e=$(id); if(e) e.addEventListener("input",()=>{pull();render();}); });
  $("template").addEventListener("change",e=>{ loadTemplate(e.target.value); render(); });
  $("btnReload").onclick=()=>{ loadTemplate(S.template); render(); };
  $("addLine2").onclick=()=>{S.fields2.push({t:"line",label:"New field:",pair:false,ruled:0,val:""});drawFields2();drawPrefill();render();};
  $("addOpts2").onclick=()=>{S.fields2.push({t:"opts",label:"Choose:",opts:"Option A, Option B",pair:false,val:""});drawFields2();drawPrefill();render();};
  $("addLine").onclick=()=>{S.fields.push({t:"line",label:"New field:",pair:false,ruled:0,val:""});drawFields();drawPrefill();render();};
  $("addOpts").onclick=()=>{S.fields.push({t:"opts",label:"Choose:",opts:"Option A, Option B",pair:false,val:""});drawFields();drawPrefill();render();};
  $("logoFile").onchange=e=>{const f=e.target.files[0]; if(!f)return;
    const r=new FileReader(); r.onload=()=>{S.logo=r.result;S.showLogo=true;$("showLogo").checked=true;render();}; r.readAsDataURL(f);};
  $("btnNoLogo").onclick=()=>{S.logo="";render();};
  $("btnPdf").onclick=()=>{previewOnly=false;render();setTimeout(()=>window.print(),120);};
  $("btnPrev").onclick=()=>{previewOnly=!previewOnly;$("btnPrev").textContent=previewOnly?"Show all pages":"Preview 1st page only";render();};
  $("btnSave").onclick=()=>{pull();localStorage.setItem("rbook",JSON.stringify(S));$("btnSave").textContent="Saved!";setTimeout(()=>$("btnSave").textContent="Save settings",1200);};
  $("btnLoad").onclick=()=>{const d=localStorage.getItem("rbook"); if(d){S=JSON.parse(d);push();render();}};
  $("btnReset").onclick=()=>{if(confirm("Reset everything to the original design?")){S=JSON.parse(JSON.stringify(DEFAULTS));push();render();}};
}
push(); bindAll(); render();
</script>
</body>
</html>
'''

HTML = HTML.replace("__LOGO__", LOGO)
open('receipt_book.html', 'w').write(HTML)
print("written", len(HTML))
