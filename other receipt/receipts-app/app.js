/* Receipt Sheet Builder — every part of the receipt is customizable.
   Model -> editor sidebar + live sheet preview; saved in localStorage. */
(function () {
  'use strict';

  var STORAGE_KEY = 'gps-receipt-builder-v2';

  var DEFAULTS = {
    coverEnabled: true,
    coverTemplate: 'full',     /* 'full' page or 'slip' (receipt piece) */
    coverTitle: 'OFFICIAL RECEIPT BOOK',
    coverLines: ['New Israel Community', 'Brewerville City'],
    coverShowRange: true,
    coverRangeLabel: 'Receipt Nos.',
    coverFields: ['Academic Year:', 'Issued to:', 'Registrar:'],
    schoolName: 'GREATER PRAISE SCHOOL SYSTEM',
    address: ['New Israel Community', 'Brewerville City'],
    fields: ['Name:', 'Grade:', 'Date:', 'Amount in words:'],
    numberMode: 'copy',          /* 'copy' = original + carbon copy sheet pairs; 'triplicate' */
    carbon: { enabled: true, color: '#d9e6ff' },
    numberStart: 1,
    numberDigits: 4,
    numberColor: '#ff0000',
    sheets: 10,
    slipsPerSheet: 3,
    columns: ['No', 'Description', 'Amount', 'Receipt No'],
    rows: ['Registration', '1st Semester', '2nd Semester', 'Uniform',
           'P.E. Uniform', 'Graduation', 'WAEC', 'Gala day',
           'Computer', 'Field trip', 'Total', 'Balance'],
    signedLabel: 'Signed:',
    roleLabel: 'Registrar',
    cut: {
      enabled: true,
      style: 'dashed',      /* dashed | dotted | solid | dashdot */
      color: '#9aa0a6',
      width: 1,
      vertical: true,       /* cuts between slips, exactly at the boundaries */
      outer: false,         /* trim edges of the sheet */
      horizontal: true,     /* adjustable cut line under the receipts */
      hPos: 7.6             /* inches from the top of the sheet */
    },
    fontFamily: '"Times New Roman", Times, serif',
    inkColor: '#000000',
    paper: 'letter'              /* 'letter' | 'a4' */
  };

  var model = load();

  /* ---------- elements ---------- */
  var $ = function (id) { return document.getElementById(id); };
  var sheetsEl = $('sheets');
  var sheetTpl = $('sheetTpl');
  var itemTpl = $('itemTpl');

  /* ---------- helpers ---------- */
  function clone(obj) { return JSON.parse(JSON.stringify(obj)); }

  function load() {
    var m = clone(DEFAULTS);
    try {
      var raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        var saved = JSON.parse(raw);
        Object.keys(DEFAULTS).forEach(function (k) {
          if (saved[k] !== undefined && typeof saved[k] === typeof DEFAULTS[k]) m[k] = saved[k];
        });
        /* merge missing sub-keys of nested objects (e.g. older saves without cut options) */
        Object.keys(DEFAULTS).forEach(function (k) {
          if (typeof DEFAULTS[k] === 'object' && DEFAULTS[k] !== null && !Array.isArray(DEFAULTS[k]) && m[k]) {
            Object.keys(DEFAULTS[k]).forEach(function (sk) {
              if (m[k][sk] === undefined) m[k][sk] = DEFAULTS[k][sk];
            });
          }
        });
      }
    } catch (e) { /* private mode etc. */ }
    return m;
  }

  function save() {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(model)); } catch (e) { /* ignore */ }
  }

  function clampInt(v, min, max, fb) {
    var n = parseInt(v, 10);
    if (isNaN(n)) n = fb;
    return Math.min(max, Math.max(min, n));
  }

  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  /* "1st" -> 1<sup>st</sup> so customized rows keep the ordinal style */
  function fmt(s) {
    return esc(s).replace(/(\d+)(st|nd|rd|th)\b/gi, '$1<sup>$2</sup>');
  }

  function padNum(n) {
    return String(n).padStart(model.numberDigits, '0');
  }

  /* page dimensions per paper size */
  function pageDims() {
    return model.paper === 'a4'
      ? { w: '297mm', h: '210mm', slip: function (n) { return (297 / n) + 'mm'; } }
      : { w: '11in', h: '8.5in', slip: function (n) { return (11 / n) + 'in'; } };
  }

  function applyPageRule() {
    var st = document.getElementById('dynpage');
    if (!st) {
      st = document.createElement('style');
      st.id = 'dynpage';
      document.head.appendChild(st);
    }
    st.textContent = '@page { size: ' + (model.paper === 'a4' ? 'A4' : 'letter') + ' landscape; margin: 0; }';
  }

  /* numbers for the slips of sheet i */
  function sheetNumbers(i) {
    var out = [];
    for (var s = 0; s < model.slipsPerSheet; s++) {
      if (model.numberMode === 'copy') {
        /* originals on even sheets, carbon copies on odd sheets:
           sheet 0: 1,2,3  sheet 1: 1,2,3  sheet 2: 4,5,6 ... */
        out.push(model.numberStart + Math.floor(i / 2) * model.slipsPerSheet + s);
      } else {
        out.push(model.numberStart + i);
      }
    }
    return out;
  }

  /* ---------- cover page ---------- */
  function buildCover(lastNumber) {
    var slipMode = model.coverTemplate === 'slip';
    var dims = pageDims();
    var sheet = sheetTpl.content.firstElementChild.cloneNode(true);
    sheet.classList.add('cover-sheet');
    sheet.style.width = dims.w;
    sheet.style.height = dims.h;
    if (slipMode) {
      sheet.classList.add('slip-cover');
      sheet.style.width = dims.slip(model.slipsPerSheet);
    }
    sheet.style.fontFamily = model.fontFamily;
    sheet.style.setProperty('--ink', model.inkColor);
    sheet.style.setProperty('--num-color', model.numberColor);

    var box = document.createElement('div');
    box.className = 'cover';

    var school = document.createElement('h1');
    school.className = 'cov-school';
    school.textContent = model.schoolName;
    var lines = document.createElement('p');
    lines.className = 'addr';
    lines.innerHTML = model.coverLines.map(esc).join('<br>');
    box.append(school, lines);

    if (slipMode) {
      var no = document.createElement('div');
      no.className = 'rcpt-no';
      no.textContent = padNum(model.numberStart);
      box.appendChild(no);
    }

    var title = document.createElement('div');
    title.className = 'cov-title';
    title.textContent = model.coverTitle;
    box.appendChild(title);

    if (model.coverShowRange) {
      var range = document.createElement('div');
      range.className = 'cov-range';
      range.textContent = model.coverRangeLabel + ' ' +
        padNum(model.numberStart) + ' to ' + padNum(lastNumber);
      box.appendChild(range);
    }

    var fields = document.createElement('div');
    fields.className = 'cov-fields';
    model.coverFields.forEach(function (f) {
      var row = document.createElement('div');
      row.className = 'field';
      var lbl = document.createElement('span');
      lbl.className = 'lbl';
      lbl.textContent = f;
      var fill = document.createElement('span');
      fill.className = 'fill';
      row.append(lbl, fill);
      fields.appendChild(row);
    });
    box.appendChild(fields);

    sheet.appendChild(box);
    return sheet;
  }

  /* ---------- receipt slip ---------- */
  function buildSlip(number) {
    var slip = document.createElement('div');
    slip.className = 'slip';

    var head = document.createElement('div');
    head.className = 'head';
    var h1 = document.createElement('h1');
    h1.textContent = model.schoolName;
    var addr = document.createElement('p');
    addr.className = 'addr';
    addr.innerHTML = model.address.map(esc).join('<br>');
    var no = document.createElement('div');
    no.className = 'rcpt-no';
    no.textContent = number;
    head.append(h1, addr, no);

    var fields = document.createElement('div');
    fields.className = 'fields';
    model.fields.forEach(function (f) {
      var row = document.createElement('div');
      row.className = 'field';
      var lbl = document.createElement('span');
      lbl.className = 'lbl';
      lbl.textContent = f;
      var fill = document.createElement('span');
      fill.className = 'fill';
      row.append(lbl, fill);
      fields.appendChild(row);
    });

    var rule = document.createElement('div');
    rule.className = 'rule';

    var table = document.createElement('table');
    var thead = document.createElement('thead');
    var htr = document.createElement('tr');
    ['c-no', 'c-desc', 'c-amt', 'c-rcpt'].forEach(function (cls, i) {
      var th = document.createElement('th');
      th.className = cls;
      th.textContent = model.columns[i] || '';
      htr.appendChild(th);
    });
    thead.appendChild(htr);
    var tbody = document.createElement('tbody');
    model.rows.forEach(function (r, i) {
      var tr = document.createElement('tr');
      var tdNo = document.createElement('td');
      tdNo.textContent = i + 1;
      var tdDesc = document.createElement('td');
      tdDesc.innerHTML = fmt(r);
      tr.append(tdNo, tdDesc, document.createElement('td'), document.createElement('td'));
      tbody.appendChild(tr);
    });
    table.append(thead, tbody);

    var signed = document.createElement('div');
    signed.className = 'signed';
    signed.textContent = model.signedLabel;
    var sig = document.createElement('span');
    sig.className = 'sig-line';
    signed.appendChild(sig);
    var registrar = document.createElement('div');
    registrar.className = 'registrar';
    registrar.textContent = model.roleLabel;

    slip.append(head, fields, rule, table, signed, registrar);
    return slip;
  }

  /* ---------- cut lines ---------- */
  function cutBackground(vertical) {
    var c = model.cut.color;
    var dir = vertical ? 'to bottom' : 'to right';
    var stops;
    switch (model.cut.style) {
      case 'solid':  return 'linear-gradient(' + dir + ', ' + c + ' 100%)';
      case 'dotted': stops = [2, 4]; break;
      case 'dashdot': stops = [8, 4, 2, 4]; break;
      default:       stops = [8, 6]; break; /* dashed */
    }
    var parts = [], pos = 0, on = true;
    for (var i = 0; i < stops.length; i++) {
      var col = on ? c : 'transparent';
      parts.push(col + ' ' + pos + 'px ' + (pos + stops[i]) + 'px');
      pos += stops[i];
      on = !on;
    }
    return 'repeating-linear-gradient(' + dir + ', ' + parts.join(', ') + ')';
  }

  function addCutLines(sheet) {
    if (!model.cut.enabled) return;
    var w = model.cut.width;
    function mk(cls, styleExtra) {
      var d = document.createElement('div');
      d.className = 'cut ' + cls;
      Object.keys(styleExtra).forEach(function (k) { d.style[k] = styleExtra[k]; });
      sheet.appendChild(d);
    }
    if (model.cut.vertical) {
      for (var i = 1; i < model.slipsPerSheet; i++) {
        mk('v', {
          left: 'calc(' + (i * 100 / model.slipsPerSheet) + '% - ' + (w / 2) + 'px)',
          width: w + 'px',
          background: cutBackground(true)
        });
      }
    }
    if (model.cut.outer) {
      mk('v', { left: 0, width: w + 'px', background: cutBackground(true) });
      mk('v', { left: 'calc(100% - ' + w + 'px)', width: w + 'px', background: cutBackground(true) });
    }
    if (model.cut.horizontal) {
      mk('h', { top: model.cut.hPos + 'in', height: w + 'px', background: cutBackground(false) });
    }
  }

  function renderSheets() {
    sheetsEl.textContent = '';
    applyPageRule();
    var dims = pageDims();

    var lastNumber = model.numberStart;
    var built = [];
    for (var i = 0; i < model.sheets; i++) {
      var nums = sheetNumbers(i);
      lastNumber = Math.max(lastNumber, nums[nums.length - 1]);
      var sheet = sheetTpl.content.firstElementChild.cloneNode(true);
      sheet.style.width = dims.w;
      sheet.style.height = dims.h;
      sheet.style.fontFamily = model.fontFamily;
      sheet.style.setProperty('--ink', model.inkColor);
      sheet.style.setProperty('--num-color', model.numberColor);
      nums.forEach(function (n) { sheet.appendChild(buildSlip(padNum(n))); });
      if (model.numberMode === 'copy' && i % 2 === 1 && model.carbon.enabled) {
        sheet.style.background = model.carbon.color;   /* carbon copy sheet */
      }
      addCutLines(sheet);
      built.push(sheet);
    }

    if (model.coverEnabled) sheetsEl.appendChild(buildCover(lastNumber));
    built.forEach(function (s) { sheetsEl.appendChild(s); });
  }

  /* ---------- editor ---------- */
  var LIST_MIN = { address: 1, fields: 0, rows: 0, coverLines: 0, coverFields: 0 };
  var LIST_IDS = {
    address: 'addressList', fields: 'fieldList', columns: 'columnList', rows: 'rowList',
    coverLines: 'coverLinesList', coverFields: 'coverFieldsList'
  };
  var ADD_DEFAULT = { rows: 'New item', coverFields: 'New field:', coverLines: 'New line' };

  function renderList(key) {
    var container = $(LIST_IDS[key]);
    container.textContent = '';
    model[key].forEach(function (value, idx) {
      var item = itemTpl.content.firstElementChild.cloneNode(true);
      var input = item.querySelector('input');
      input.value = value;
      input.dataset.list = key;
      input.dataset.idx = idx;
      var del = item.querySelector('.del');
      del.dataset.list = key;
      del.dataset.idx = idx;
      container.appendChild(item);
    });
  }

  function renderLists() { Object.keys(LIST_IDS).forEach(renderList); }

  function syncSimpleInputs() {
    $('coverEnabled').checked = model.coverEnabled;
    $('coverTemplate').value = model.coverTemplate;
    $('coverTitle').value = model.coverTitle;
    $('coverShowRange').checked = model.coverShowRange;
    $('coverRangeLabel').value = model.coverRangeLabel;
    $('schoolName').value = model.schoolName;
    $('numberMode').value = model.numberMode;
    $('numberStart').value = model.numberStart;
    $('numberDigits').value = model.numberDigits;
    $('sheetCount').value = model.sheets;
    $('slipsPerSheet').value = model.slipsPerSheet;
    $('numberColor').value = model.numberColor;
    $('carbonEnabled').checked = model.carbon.enabled;
    $('carbonColor').value = model.carbon.color;
    $('cutEnabled').checked = model.cut.enabled;
    $('cutStyle').value = model.cut.style;
    $('cutColor').value = model.cut.color;
    $('cutWidth').value = model.cut.width;
    $('cutVertical').checked = model.cut.vertical;
    $('cutOuter').checked = model.cut.outer;
    $('cutHorizontal').checked = model.cut.horizontal;
    $('cutPos').value = model.cut.hPos;
    $('cutPosVal').textContent = model.cut.hPos;
    $('signedLabel').value = model.signedLabel;
    $('roleLabel').value = model.roleLabel;
    $('fontFamily').value = model.fontFamily;
    $('inkColor').value = model.inkColor;
    $('paperSize').value = model.paper;
  }

  /* keep a server-side copy so "Open PDF" / GET export.pdf always matches the editor */
  var saveTimer = null;
  function pushSave() {
    if (saveTimer) clearTimeout(saveTimer);
    saveTimer = setTimeout(function () {
      fetch('save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(model)
      }).catch(function () { /* offline preview: localStorage still holds it */ });
    }, 400);
  }

  function changed() { save(); pushSave(); renderSheets(); }

  /* simple scalar controls */
  var SIMPLE = {
    coverTitle: function (v) { model.coverTitle = v; },
    coverTemplate: function (v) { model.coverTemplate = v === 'slip' ? 'slip' : 'full'; },
    coverRangeLabel: function (v) { model.coverRangeLabel = v; },
    schoolName: function (v) { model.schoolName = v; },
    signedLabel: function (v) { model.signedLabel = v; },
    roleLabel: function (v) { model.roleLabel = v; },
    fontFamily: function (v) { model.fontFamily = v; },
    numberColor: function (v) { model.numberColor = v; },
    carbonColor: function (v) { model.carbon.color = v; },
    inkColor: function (v) { model.inkColor = v; },
    numberMode: function (v) { model.numberMode = v === 'triplicate' ? 'triplicate' : 'copy'; },
    paperSize: function (v) { model.paper = v === 'a4' ? 'a4' : 'letter'; },
    cutStyle: function (v) { model.cut.style = ['dashed', 'dotted', 'solid', 'dashdot'].indexOf(v) >= 0 ? v : 'dashed'; },
    cutColor: function (v) { model.cut.color = v; },
    cutWidth: function (v) { model.cut.width = clampInt(v, 1, 4, 1); },
    cutPos: function (v) {
      var n = parseFloat(v);
      if (isNaN(n)) n = 7.6;
      model.cut.hPos = Math.min(8.4, Math.max(0.5, n));
      $('cutPosVal').textContent = model.cut.hPos;
    },
    numberStart: function (v) { model.numberStart = clampInt(v, 0, 999999, 1); },
    numberDigits: function (v) { model.numberDigits = clampInt(v, 1, 8, 4); },
    sheetCount: function (v) { model.sheets = clampInt(v, 1, 200, 10); },
    slipsPerSheet: function (v) { model.slipsPerSheet = clampInt(v, 1, 4, 3); }
  };
  Object.keys(SIMPLE).forEach(function (id) {
    $(id).addEventListener('input', function (e) { SIMPLE[id](e.target.value); changed(); });
  });

  /* boolean controls */
  var BOOLS = {
    coverEnabled: function (v) { model.coverEnabled = v; },
    coverShowRange: function (v) { model.coverShowRange = v; },
    cutEnabled: function (v) { model.cut.enabled = v; },
    cutVertical: function (v) { model.cut.vertical = v; },
    cutOuter: function (v) { model.cut.outer = v; },
    cutHorizontal: function (v) { model.cut.horizontal = v; },
    carbonEnabled: function (v) { model.carbon.enabled = v; }
  };
  Object.keys(BOOLS).forEach(function (id) {
    $(id).addEventListener('input', function (e) { BOOLS[id](e.target.checked); changed(); });
  });

  /* list item edits + deletes (delegated) */
  $('editor').addEventListener('input', function (e) {
    var t = e.target;
    if (t.dataset.list) {
      model[t.dataset.list][+t.dataset.idx] = t.value;
      changed();
    }
  });
  $('editor').addEventListener('click', function (e) {
    var t = e.target;
    if (t.classList.contains('del')) {
      var key = t.dataset.list;
      if (model[key].length > (LIST_MIN[key] || 0)) {
        model[key].splice(+t.dataset.idx, 1);
        renderList(key);
        changed();
      }
    }
    if (t.classList.contains('add')) {
      var k = t.dataset.add;
      model[k].push(ADD_DEFAULT[k] || 'New line');
      renderList(k);
      changed();
    }
  });

  /* toolbar */
  $('printBtn').addEventListener('click', function () { window.print(); });
  $('exportBtn').addEventListener('click', function () {
    fetch('export', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(model)
    })
      .then(function (r) {
        if (!r.ok) throw new Error('server returned ' + r.status);
        return r.blob();
      })
      .then(function (blob) {
        var a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = 'receipt-book.pdf';
        document.body.appendChild(a);
        a.click();
        a.remove();
        setTimeout(function () { URL.revokeObjectURL(a.href); }, 5000);
      })
      .catch(function (e) {
        alert('PDF export failed: ' + e.message + '. Use the "Open PDF" link in the toolbar instead.');
      });
  });
  $('resetBtn').addEventListener('click', function () {
    try { localStorage.removeItem(STORAGE_KEY); } catch (e) { /* ignore */ }
    model = clone(DEFAULTS);
    syncSimpleInputs();
    renderLists();
    changed();
  });
  $('toggleEditor').addEventListener('click', function () {
    var hidden = document.body.classList.toggle('editor-hidden');
    this.textContent = hidden ? 'Show editor' : 'Hide editor';
  });

  /* ---------- go ---------- */
  syncSimpleInputs();
  renderLists();
  renderSheets();
  pushSave();
})();
