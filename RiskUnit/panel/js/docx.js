/* docx.js — a minimal valid Word (.docx) writer: WordprocessingML zip with headings, paragraphs, tables and
   embedded PNG charts (from Plotly.toImage). blocks: {t:'title'|'h1'|'h2'|'p'|'small', text} · {t:'table', rows, head}
   · {t:'img', png: Uint8Array, w, h} (pixels) · {t:'pb'} page break. */
(function () {
  'use strict';
  var U = window.U, x = function (s) { return U.xmlEsc(s == null ? '' : s); };
  var NS = 'http://schemas.openxmlformats.org/';
  function run(text, o) {
    o = o || {};
    var rp = (o.b ? '<w:b/>' : '') + (o.i ? '<w:i/>' : '') + (o.sz ? '<w:sz w:val="' + o.sz + '"/>' : '') + (o.color ? '<w:color w:val="' + o.color + '"/>' : '');
    return '<w:r>' + (rp ? '<w:rPr>' + rp + '</w:rPr>' : '') + '<w:t xml:space="preserve">' + x(text) + '</w:t></w:r>';
  }
  function para(text, style, o) {
    o = o || {};
    var pp = (style ? '<w:pStyle w:val="' + style + '"/>' : '') + (o.jc ? '<w:jc w:val="' + o.jc + '"/>' : '') + (o.sp ? '<w:spacing w:before="0" w:after="' + o.sp + '"/>' : '');
    return '<w:p>' + (pp ? '<w:pPr>' + pp + '</w:pPr>' : '') + run(text, o) + '</w:p>';
  }
  function table(rows, head) {
    var n = Math.max.apply(null, rows.map(function (r) { return r.length; }).concat([1]));
    var W = 9638, first = Math.min(3400, Math.round(W * (n > 8 ? 0.26 : 0.34))), rest = n > 1 ? Math.floor((W - first) / (n - 1)) : W;
    var widths = [first].concat(Array(Math.max(0, n - 1)).fill(rest));
    var h = '<w:tbl><w:tblPr><w:tblStyle w:val="TableGrid"/><w:tblW w:w="' + W + '" w:type="dxa"/><w:tblLayout w:type="fixed"/></w:tblPr><w:tblGrid>' +
      widths.map(function (w) { return '<w:gridCol w:w="' + w + '"/>'; }).join('') + '</w:tblGrid>';
    rows.forEach(function (r, ri) {
      var hd = ri < (head == null ? 1 : head);
      h += '<w:tr>' + (hd ? '<w:trPr><w:tblHeader/></w:trPr>' : '');
      for (var i = 0; i < n; i++) {
        var v = r[i], num = typeof v === 'number';
        var t = num ? U.nf(v, Math.abs(v) >= 1000 ? 0 : Math.abs(v) >= 10 ? 1 : 2) : (v == null ? '' : String(v));
        h += '<w:tc><w:tcPr><w:tcW w:w="' + widths[i] + '" w:type="dxa"/>' + (hd ? '<w:shd w:val="clear" w:color="auto" w:fill="E1F0F2"/>' : '') + '</w:tcPr>' +
          '<w:p><w:pPr><w:spacing w:before="0" w:after="0"/>' + (num || (i > 0 && hd) ? '<w:jc w:val="right"/>' : '') + '</w:pPr>' + run(t, { b: hd, sz: 17 }) + '</w:p></w:tc>';
      }
      h += '</w:tr>';
    });
    return h + '</w:tbl>' + para('', null, { sp: 120 });
  }
  function image(id, w, h) {
    var maxW = 6.3 * 914400, cx = Math.round(w * 9525), cy = Math.round(h * 9525);
    if (cx > maxW) { cy = Math.round(cy * maxW / cx); cx = maxW; }
    return '<w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="' + cx + '" cy="' + cy + '"/>' +
      '<wp:docPr id="' + id + '" name="Qrafik ' + id + '"/><wp:cNvGraphicFramePr><a:graphicFrameLocks noChangeAspect="1"/></wp:cNvGraphicFramePr>' +
      '<a:graphic><a:graphicData uri="' + NS + 'drawingml/2006/picture"><pic:pic><pic:nvPicPr><pic:cNvPr id="' + id + '" name="image' + id + '.png"/><pic:cNvPicPr/></pic:nvPicPr>' +
      '<pic:blipFill><a:blip r:embed="rIdImg' + id + '"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill><pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="' + cx + '" cy="' + cy + '"/></a:xfrm>' +
      '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>';
  }
  var STYLES = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:styles xmlns:w="' + NS + 'wordprocessingml/2006/main">' +
    '<w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:cs="Calibri" w:eastAsia="Calibri"/><w:sz w:val="21"/><w:lang w:val="az-Latn-AZ"/></w:rPr></w:rPrDefault><w:pPrDefault><w:pPr><w:spacing w:after="100" w:line="264" w:lineRule="auto"/></w:pPr></w:pPrDefault></w:docDefaults>' +
    '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style>' +
    '<w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:basedOn w:val="Normal"/><w:pPr><w:spacing w:after="160"/></w:pPr><w:rPr><w:b/><w:color w:val="0A5560"/><w:sz w:val="40"/></w:rPr></w:style>' +
    '<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:pPr><w:keepNext/><w:spacing w:before="320" w:after="120"/><w:outlineLvl w:val="0"/></w:pPr><w:rPr><w:b/><w:color w:val="0E6F7C"/><w:sz w:val="30"/></w:rPr></w:style>' +
    '<w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:pPr><w:keepNext/><w:spacing w:before="220" w:after="80"/><w:outlineLvl w:val="1"/></w:pPr><w:rPr><w:b/><w:sz w:val="24"/></w:rPr></w:style>' +
    '<w:style w:type="paragraph" w:styleId="Small"><w:name w:val="Small"/><w:basedOn w:val="Normal"/><w:rPr><w:color w:val="738190"/><w:sz w:val="17"/></w:rPr></w:style>' +
    '<w:style w:type="table" w:styleId="TableGrid"><w:name w:val="Table Grid"/><w:tblPr><w:tblBorders><w:top w:val="single" w:sz="4" w:space="0" w:color="C9D2DA"/><w:left w:val="single" w:sz="4" w:space="0" w:color="C9D2DA"/><w:bottom w:val="single" w:sz="4" w:space="0" w:color="C9D2DA"/><w:right w:val="single" w:sz="4" w:space="0" w:color="C9D2DA"/><w:insideH w:val="single" w:sz="4" w:space="0" w:color="C9D2DA"/><w:insideV w:val="single" w:sz="4" w:space="0" w:color="C9D2DA"/></w:tblBorders><w:tblCellMar><w:left w:w="70" w:type="dxa"/><w:right w:w="70" w:type="dxa"/></w:tblCellMar></w:tblPr></w:style></w:styles>';
  U.docx = function (blocks, meta) {
    meta = meta || {};
    var body = [], imgs = [];
    blocks.forEach(function (b) {
      if (b.t === 'title') body.push(para(b.text, 'Title'));
      else if (b.t === 'h1') body.push(para(b.text, 'Heading1'));
      else if (b.t === 'h2') body.push(para(b.text, 'Heading2'));
      else if (b.t === 'small') body.push(para(b.text, 'Small'));
      else if (b.t === 'p') body.push(para(b.text));
      else if (b.t === 'pb') body.push('<w:p><w:r><w:br w:type="page"/></w:r></w:p>');
      else if (b.t === 'table' && b.rows && b.rows.length) body.push(table(b.rows, b.head));
      else if (b.t === 'img' && b.png) { imgs.push(b.png); body.push(image(imgs.length, b.w || 900, b.h || 420)); }
    });
    var doc = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="' + NS + 'wordprocessingml/2006/main" xmlns:r="' + NS + 'officeDocument/2006/relationships" xmlns:wp="' + NS + 'drawingml/2006/wordprocessingDrawing" xmlns:a="' + NS + 'drawingml/2006/main" xmlns:pic="' + NS + 'drawingml/2006/picture"><w:body>' +
      body.join('') + '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1134" w:right="1134" w:bottom="1134" w:left="1134" w:header="708" w:footer="708" w:gutter="0"/></w:sectPr></w:body></w:document>';
    var rels = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="' + NS + 'package/2006/relationships"><Relationship Id="rIdSt" Type="' + NS + 'officeDocument/2006/relationships/styles" Target="styles.xml"/>' +
      imgs.map(function (p, i) { return '<Relationship Id="rIdImg' + (i + 1) + '" Type="' + NS + 'officeDocument/2006/relationships/image" Target="media/image' + (i + 1) + '.png"/>'; }).join('') + '</Relationships>';
    var core = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><cp:coreProperties xmlns:cp="' + NS + 'package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">' +
      '<dc:title>' + x(meta.title || 'Hesabat') + '</dc:title><dc:creator>' + x(meta.author || 'Mikro Model') + '</dc:creator><dc:language>az-Latn-AZ</dc:language></cp:coreProperties>';
    var files = [
      ['[Content_Types].xml', '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="' + NS + 'package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Default Extension="png" ContentType="image/png"/>' +
        '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/><Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/><Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/></Types>'],
      ['_rels/.rels', '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="' + NS + 'package/2006/relationships"><Relationship Id="rId1" Type="' + NS + 'officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/><Relationship Id="rId2" Type="' + NS + 'package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/></Relationships>'],
      ['docProps/core.xml', core], ['word/document.xml', doc], ['word/styles.xml', STYLES], ['word/_rels/document.xml.rels', rels]];
    imgs.forEach(function (p, i) { files.push(['word/media/image' + (i + 1) + '.png', p]); });
    return U.zip(files, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document');
  };
  U.dataUrlBytes = function (url) {
    var b = atob(String(url).split(',')[1] || ''), a = new Uint8Array(b.length);
    for (var i = 0; i < b.length; i++) a[i] = b.charCodeAt(i);
    return a;
  };
})();
