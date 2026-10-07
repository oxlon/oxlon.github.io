/* xlsx.js — a ZIP writer (DEFLATE via CompressionStream where available, else stored; CRC-32) and a minimal multi-sheet .xlsx writer
   (inline strings, numbers, bold header, frozen top row, column widths). No dependency, works from file://. */
(function () {
  'use strict';
  var U = window.U, enc = new TextEncoder();
  var CRC = (function () { var t = [], c, n, k; for (n = 0; n < 256; n++) { c = n; for (k = 0; k < 8; k++) c = c & 1 ? 0xEDB88320 ^ (c >>> 1) : c >>> 1; t[n] = c >>> 0; } return t; })();
  function crc32(b) { var c = 0xFFFFFFFF; for (var i = 0; i < b.length; i++) c = CRC[(c ^ b[i]) & 255] ^ (c >>> 8); return (c ^ 0xFFFFFFFF) >>> 0; }
  U.xmlEsc = function (s) { return String(s).replace(/[\x00-\x08\x0B\x0C\x0E-\x1F]/g, '').replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); };
  /* raw DEFLATE of one entry with the browser's CompressionStream; null when unavailable (then the entry is stored) */
  function deflate(u8) {
    try {
      if (!window.CompressionStream || !window.Response || u8.length < 256) return Promise.resolve(null);
      var st = new Blob([u8]).stream().pipeThrough(new CompressionStream('deflate-raw'));
      return new Response(st).arrayBuffer().then(function (b) { return new Uint8Array(b); }, function () { return null; });
    } catch (e) { return Promise.resolve(null); }
  }
  /* files: [[name, string | Uint8Array], ...] → Promise<Blob>; entries DEFLATE-compressed where the browser can, else stored */
  U.zip = function (files, type) {
    var ents = files.map(function (f) { var data = typeof f[1] === 'string' ? enc.encode(f[1]) : f[1]; return { name: enc.encode(f[0]), data: data, crc: crc32(data) }; });
    return Promise.all(ents.map(function (e) { return deflate(e.data); })).then(function (zs) {
      var parts = [], cen = [], off = 0;
      ents.forEach(function (e, i) {
        var z = zs[i] && zs[i].length < e.data.length ? zs[i] : null, body = z || e.data, meth = z ? 8 : 0;
        var h = new DataView(new ArrayBuffer(30));
        h.setUint32(0, 0x04034b50, true); h.setUint16(4, 20, true); h.setUint16(6, 0x0800, true); h.setUint16(8, meth, true); h.setUint16(10, 0, true); h.setUint16(12, 33, true); h.setUint32(14, e.crc, true);
        h.setUint32(18, body.length, true); h.setUint32(22, e.data.length, true); h.setUint16(26, e.name.length, true);
        parts.push(new Uint8Array(h.buffer), e.name, body);
        var d = new DataView(new ArrayBuffer(46));
        d.setUint32(0, 0x02014b50, true); d.setUint16(4, 20, true); d.setUint16(6, 20, true); d.setUint16(8, 0x0800, true); d.setUint16(10, meth, true); d.setUint16(14, 33, true); d.setUint32(16, e.crc, true);
        d.setUint32(20, body.length, true); d.setUint32(24, e.data.length, true); d.setUint16(28, e.name.length, true); d.setUint32(42, off, true);
        cen.push(new Uint8Array(d.buffer), e.name);
        off += 30 + e.name.length + body.length;
      });
      var size = cen.reduce(function (a, b) { return a + b.length; }, 0), en = new DataView(new ArrayBuffer(22));
      en.setUint32(0, 0x06054b50, true); en.setUint16(8, ents.length, true); en.setUint16(10, ents.length, true); en.setUint32(12, size, true); en.setUint32(16, off, true);
      return new Blob(parts.concat(cen, [new Uint8Array(en.buffer)]), { type: type || 'application/zip' });
    });
  };
  U.blobB64 = function (blob) {
    return new Promise(function (ok) { var r = new FileReader(); r.onload = function () { ok(String(r.result).split(',')[1]); }; r.readAsDataURL(blob); });
  };
  function col(n) { var s = ''; n++; while (n > 0) { var r = (n - 1) % 26; s = String.fromCharCode(65 + r) + s; n = Math.floor((n - 1) / 26); } return s; }
  function sheet(sh) {
    var rows = sh.rows || [], fz = sh.freeze == null ? 1 : sh.freeze, x = U.xmlEsc;
    var o = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">',
      '<sheetViews><sheetView workbookViewId="0">' + (fz ? '<pane ySplit="' + fz + '" topLeftCell="A' + (fz + 1) + '" activePane="bottomLeft" state="frozen"/>' : '') + '</sheetView></sheetViews>'];
    if (sh.widths && sh.widths.length) { o.push('<cols>'); sh.widths.forEach(function (w, i) { o.push('<col min="' + (i + 1) + '" max="' + (i + 1) + '" width="' + w + '" customWidth="1"/>'); }); o.push('</cols>'); }
    o.push('<sheetData>');
    rows.forEach(function (r, ri) {
      o.push('<row r="' + (ri + 1) + '">');
      (r || []).forEach(function (v, ci) {
        var ref = col(ci) + (ri + 1), st = ri < (sh.hdr == null ? 1 : sh.hdr) ? ' s="1"' : (typeof v === 'number' ? ' s="2"' : '');
        if (typeof v === 'number' && isFinite(v)) o.push('<c r="' + ref + '"' + st + '><v>' + v + '</v></c>');
        else if (v !== null && v !== undefined && v !== '') o.push('<c r="' + ref + '"' + st + ' t="inlineStr"><is><t xml:space="preserve">' + x(v) + '</t></is></c>');
      });
      o.push('</row>');
    });
    o.push('</sheetData></worksheet>');
    return o.join('');
  }
  function sname(n, used) {
    var s = String(n || 'Vərəq').replace(/[\[\]\*\?\/\\:]/g, ' ').slice(0, 31), k = s, i = 2;
    while (used[k]) { k = s.slice(0, 28) + ' ' + i++; } used[k] = 1; return k;
  }
  /* sheets: [{name, rows, widths, freeze, hdr}] (or legacy (name, rows, widths)) → Promise<Blob> */
  U.xlsx = function (sheets, rows, widths) {
    if (typeof sheets === 'string') sheets = [{ name: sheets, rows: rows, widths: widths }];
    var NS = 'http://schemas.openxmlformats.org/', used = {}, names = sheets.map(function (s) { return sname(s.name, used); });
    var files = [
      ['[Content_Types].xml', '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="' + NS + 'package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>' +
        sheets.map(function (s, i) { return '<Override PartName="/xl/worksheets/sheet' + (i + 1) + '.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'; }).join('') +
        '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/></Types>'],
      ['_rels/.rels', '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="' + NS + 'package/2006/relationships"><Relationship Id="rId1" Type="' + NS + 'officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>'],
      ['xl/workbook.xml', '<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="' + NS + 'spreadsheetml/2006/main" xmlns:r="' + NS + 'officeDocument/2006/relationships"><sheets>' +
        names.map(function (n, i) { return '<sheet name="' + U.xmlEsc(n) + '" sheetId="' + (i + 1) + '" r:id="rId' + (i + 1) + '"/>'; }).join('') + '</sheets></workbook>'],
      ['xl/_rels/workbook.xml.rels', '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="' + NS + 'package/2006/relationships">' +
        sheets.map(function (s, i) { return '<Relationship Id="rId' + (i + 1) + '" Type="' + NS + 'officeDocument/2006/relationships/worksheet" Target="worksheets/sheet' + (i + 1) + '.xml"/>'; }).join('') +
        '<Relationship Id="rId' + (sheets.length + 1) + '" Type="' + NS + 'officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>'],
      ['xl/styles.xml', '<?xml version="1.0" encoding="UTF-8"?><styleSheet xmlns="' + NS + 'spreadsheetml/2006/main"><numFmts count="1"><numFmt numFmtId="164" formatCode="#,##0.00"/></numFmts><fonts count="2"><font><sz val="11"/><name val="Calibri"/></font><font><b/><sz val="11"/><name val="Calibri"/></font></fonts><fills count="2"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill></fills><borders count="1"><border/></borders><cellStyleXfs count="1"><xf/></cellStyleXfs><cellXfs count="3"><xf xfId="0"/><xf fontId="1" applyFont="1" xfId="0"/><xf numFmtId="164" applyNumberFormat="1" xfId="0"/></cellXfs><cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles></styleSheet>']
    ];
    sheets.forEach(function (s, i) { files.push(['xl/worksheets/sheet' + (i + 1) + '.xml', sheet(s)]); });
    return U.zip(files, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
  };
})();
