/* Functional check of the Receipt Sheet Builder against the live server */
const { JSDOM } = require('jsdom');

const URL = 'http://127.0.0.1:8000/';
const fail = (msg) => { console.error('FAIL:', msg); process.exit(1); };

JSDOM.fromURL(URL, { runScripts: 'dangerously', resources: 'usable', pretendToBeVisual: true })
  .then((dom) => new Promise((resolve) => {
    dom.window.addEventListener('load', () => resolve(dom));
    setTimeout(() => resolve(dom), 4000);
  }))
  .then((dom) => {
    const win = dom.window;
    const doc = win.document;
    const $ = (id) => doc.getElementById(id);
    const set = (el, value) => { el.value = value; el.dispatchEvent(new win.Event('input', { bubbles: true })); };
    const click = (el) => el.dispatchEvent(new win.Event('click', { bubbles: true }));
    const rSheets = () => [...doc.querySelectorAll('.sheet:not(.cover-sheet)')];
    const slipNums = (sh) => [...sh.querySelectorAll('.rcpt-no')].map((n) => n.textContent);

    /* cover page first */
    const allSheets = [...doc.querySelectorAll('.sheet')];
    if (allSheets.length !== 11) fail(`total sheets (cover + 10): ${allSheets.length}`);
    if (!allSheets[0].classList.contains('cover-sheet')) fail('cover page must be first');
    const cover = allSheets[0];
    if (cover.querySelector('.cov-title').textContent !== 'OFFICIAL RECEIPT BOOK') fail('cover title');
    if (cover.querySelector('.cov-school').textContent !== 'GREATER PRAISE SCHOOL SYSTEM') fail('cover school');
    const range = cover.querySelector('.cov-range').textContent;
    if (range !== 'Receipt Nos. 0001 to 0015') fail(`cover range: "${range}"`);
    if (cover.querySelectorAll('.cov-fields .field').length !== 3) fail('cover fields');

    /* copy-mode numbering: sheet1 = 1,2,3 ; sheet2 = 1,2,3 (carbon copy) ; sheet3 = 4,5,6 */
    let rs = rSheets();
    if (rs.length !== 10) fail(`receipt sheets: ${rs.length}`);
    if (JSON.stringify(slipNums(rs[0])) !== JSON.stringify(['0001', '0002', '0003'])) fail(`sheet1: ${slipNums(rs[0])}`);
    if (JSON.stringify(slipNums(rs[1])) !== JSON.stringify(['0001', '0002', '0003'])) fail(`sheet2 copy: ${slipNums(rs[1])}`);
    if (JSON.stringify(slipNums(rs[2])) !== JSON.stringify(['0004', '0005', '0006'])) fail(`sheet3: ${slipNums(rs[2])}`);

    /* carbon copy sheets highlighted blue */
    const isBlue = (s) => /217, 230, 255|#d9e6ff/i.test(s.style.background);
    if (isBlue(rs[0])) fail('sheet1 must not be carbon');
    if (!isBlue(rs[1])) fail(`sheet2 carbon highlight: "${rs[1].style.background}"`);
    if (isBlue(rs[2])) fail('sheet3 must not be carbon');
    if (!isBlue(rs[3])) fail('sheet4 carbon highlight');
    $('carbonEnabled').checked = false;
    $('carbonEnabled').dispatchEvent(new win.Event('input', { bubbles: true }));
    if (rSheets()[1].style.background !== '') fail('carbon disabled');
    $('carbonEnabled').checked = true;
    $('carbonEnabled').dispatchEvent(new win.Event('input', { bubbles: true }));
    if (!isBlue(rSheets()[1])) fail('carbon re-enabled');

    /* switch to triplicate mode */
    set($('numberMode'), 'triplicate');
    rs = rSheets();
    if (JSON.stringify(slipNums(rs[0])) !== JSON.stringify(['0001', '0001', '0001'])) fail('triplicate sheet1');
    if (JSON.stringify(slipNums(rs[1])) !== JSON.stringify(['0002', '0002', '0002'])) fail('triplicate sheet2');
    set($('numberMode'), 'copy');

    /* cover customizing */
    set($('coverTitle'), 'MY RECEIPT BOOK');
    if (doc.querySelector('.cov-title').textContent !== 'MY RECEIPT BOOK') fail('cover title edit');
    set($('coverRangeLabel'), 'Numbers');
    if (!doc.querySelector('.cov-range').textContent.startsWith('Numbers ')) fail('range label edit');
    const coverFieldInput = doc.querySelector('#coverFieldsList .item input');
    set(coverFieldInput, 'PTA Chairman:');
    if (![...doc.querySelectorAll('.cov-fields .lbl')].some((l) => l.textContent === 'PTA Chairman:')) fail('cover field edit render');
    click(doc.querySelector('[data-add="coverLines"]'));
    if (doc.querySelectorAll('.cover .addr br').length !== 2) fail('cover line add');

    /* cover toggle off/on */
    $('coverEnabled').checked = false;
    $('coverEnabled').dispatchEvent(new win.Event('input', { bubbles: true }));
    if (doc.querySelector('.cover-sheet')) fail('cover should be hidden');
    $('coverEnabled').checked = true;
    $('coverEnabled').dispatchEvent(new win.Event('input', { bubbles: true }));
    if (!doc.querySelector('.cover-sheet')) fail('cover should return');

    /* receipt-piece cover template */
    set($('coverTemplate'), 'slip');
    let cov = doc.querySelector('.cover-sheet');
    if (!cov.classList.contains('slip-cover')) fail('slip cover class');
    if (cov.style.width !== (11 / 3) + 'in') fail(`slip cover width: ${cov.style.width}`);
    if (cov.querySelector('.rcpt-no').textContent !== '0001') fail('slip cover shows first number');
    set($('coverTemplate'), 'full');
    if (doc.querySelector('.cover-sheet').classList.contains('slip-cover')) fail('back to full cover');

    /* receipt customization still works */
    set($('schoolName'), 'MY TEST ACADEMY');
    if (doc.querySelector('.sheet:not(.cover-sheet) h1').textContent !== 'MY TEST ACADEMY') fail('school name edit');
    if (doc.querySelector('.cov-school').textContent !== 'MY TEST ACADEMY') fail('cover follows school name');
    const rowInput = doc.querySelector('#rowList .item input');
    set(rowInput, '3rd Term Exam');
    if (doc.querySelector('.sheet tbody td:nth-child(2)').innerHTML !== '3<sup>rd</sup> Term Exam') fail('row edit/sup');
    click(doc.querySelector('[data-add="rows"]'));
    if (rSheets()[0].querySelector('.slip').querySelectorAll('tbody tr').length !== 13) fail('add row');

    /* cut lines */
    rs = rSheets();
    if (rs[0].querySelectorAll('.cut.v').length !== 2) fail('vertical cut lines between 3 slips');
    if (rs[0].querySelectorAll('.cut.h').length !== 1) fail('horizontal cut line');
    if (doc.querySelector('.cover-sheet .cut')) fail('no cut lines on cover');
    const vLefts = [...rs[0].querySelectorAll('.cut.v')].map((d) => d.style.left);
    if (!/^calc\(33\.3\d*% - 0\.5px\)$/.test(vLefts[0]) || !/^calc\(66\.6\d*% - 0\.5px\)$/.test(vLefts[1])) fail(`vertical cut positions: ${vLefts}`);
    if (rs[0].querySelector('.cut.h').style.top !== '7.6in') fail('default cut position');

    set($('cutStyle'), 'solid');
    if (rs[0].querySelector('.cut').style.background.indexOf('linear-gradient') < 0) fail('solid style');
    set($('cutStyle'), 'dashdot');
    if (rs[0].querySelector('.cut').style.background.indexOf('repeating-linear-gradient') < 0) fail('dashdot style');
    set($('cutPos'), '7.2');
    if (rSheets()[0].querySelector('.cut.h').style.top !== '7.2in') fail('adjustable cut position');
    if ($('cutPosVal').textContent != 7.2) fail('position readout');
    set($('slipsPerSheet'), '4');
    if (rSheets()[0].querySelectorAll('.cut.v').length !== 3) fail('cuts follow slips count');
    set($('slipsPerSheet'), '3');
    $('cutEnabled').checked = false;
    $('cutEnabled').dispatchEvent(new win.Event('input', { bubbles: true }));
    if (rSheets()[0].querySelector('.cut')) fail('cut lines disabled');
    $('cutEnabled').checked = true;
    $('cutEnabled').dispatchEvent(new win.Event('input', { bubbles: true }));

    /* persistence + reset */
    if (!win.localStorage.getItem('gps-receipt-builder-v2')) fail('localStorage save');
    click($('resetBtn'));
    if (doc.querySelector('.cov-title').textContent !== 'OFFICIAL RECEIPT BOOK') fail('reset cover');
    if (JSON.stringify(slipNums(rSheets()[0])) !== JSON.stringify(['0001', '0002', '0003'])) fail('reset numbering');
    if (doc.querySelectorAll('.sheet').length !== 11) fail('reset sheet count');
    if (rSheets()[0].querySelectorAll('.cut.v').length !== 2) fail('reset cut lines');
    if (rSheets()[0].querySelector('.cut.h').style.top !== '7.6in') fail('reset cut position');

    /* paper size */
    set($('paperSize'), 'a4');
    if (doc.querySelector('.sheet').style.width !== '297mm') fail('a4 sheet width');
    if ((doc.getElementById('dynpage').textContent || '').indexOf('A4') < 0) fail('dynpage A4 rule');
    set($('paperSize'), 'letter');
    if (doc.querySelector('.sheet').style.width !== '11in') fail('letter sheet width');

    /* export endpoint + button */
    if (!$('exportBtn')) fail('export button missing');
    if (!$('openPdf')) fail('open pdf link missing');
    return fetch('http://127.0.0.1:8000/export', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: '{}'
    }).then((r) => {
      if (!r.ok) fail('export status ' + r.status);
      if ((r.headers.get('content-type') || '').indexOf('application/pdf') < 0) fail('export content type');
      return r.arrayBuffer();
    }).then((ab) => {
      const head = String.fromCharCode(...new Uint8Array(ab).slice(0, 5));
      if (head !== '%PDF-') fail('export not a PDF');
      if (ab.byteLength < 5000) fail('export too small');

      /* save + GET export.pdf fallback flow */
      return fetch('http://127.0.0.1:8000/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ schoolName: 'SAVE TEST ACADEMY' })
      }).then((r) => {
        if (!r.ok) fail('save status ' + r.status);
        return fetch('http://127.0.0.1:8000/export.pdf');
      }).then((r2) => {
        if (!r2.ok) fail('export.pdf status ' + r2.status);
        return r2.arrayBuffer();
      }).then((ab2) => {
        const txt = Buffer.from(ab2).toString('latin1');
        if (txt.indexOf('%PDF-') !== 0) fail('export.pdf not a PDF');
        if (txt.indexOf('SAVE TEST ACADEMY') < 0) fail('export.pdf must use the saved model');
      });
    });
  })
  .then(() => {
    console.log('ALL CHECKS PASSED: cover templates, numbering, editor, cut lines, carbon, paper sizes, persistence, reset, PDF export + save/GET fallback');
    process.exit(0);
  })
  .catch((e) => { console.error('FAIL:', e.message); process.exit(1); });
