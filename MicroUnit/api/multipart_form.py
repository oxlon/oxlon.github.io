"""
multipart_form — multipart/form-data təhlilçisi (Python 3.13-də `cgi` modulu yoxdur).

    parts = parse(body_bytes, content_type_header)
    parts["kind"].text        -> "firm_panel"
    parts["file"].filename    -> "FR10_firm_panel.csv"
    parts["file"].data        -> bytes

RFC 7578: hissələr `--boundary` ilə ayrılır; hər hissədə başlıqlar, boş sətir və məzmun. Fayl adı
`filename*=UTF-8''...` (RFC 5987) formatında da qəbul olunur. Yalnız LF ilə bitən sətirlər də başa düşülür.
"""
import re
from urllib.parse import unquote


class MultipartError(ValueError):
    pass


class Part:
    __slots__ = ("name", "filename", "content_type", "headers", "data")

    def __init__(self, name, filename, content_type, headers, data):
        self.name, self.filename, self.content_type, self.headers, self.data = name, filename, content_type, headers, data

    @property
    def text(self):
        return self.data.decode("utf-8", errors="replace")

    def __repr__(self):
        return "Part(%r, filename=%r, %d bytes)" % (self.name, self.filename, len(self.data))


def _params(value):
    """'form-data; name="file"; filename="a b.csv"' -> ('form-data', {'name': 'file', 'filename': 'a b.csv'})."""
    out, main = {}, value.split(";", 1)[0].strip().lower()
    for m in re.finditer(r';\s*([A-Za-z0-9_*.-]+)\s*=\s*("((?:[^"\\]|\\.)*)"|[^;]*)', value):
        k = m.group(1).lower()
        v = m.group(3) if m.group(3) is not None else m.group(2).strip()
        if m.group(3) is not None:
            v = re.sub(r"\\(.)", r"\1", v)
        out[k] = v
    if "filename*" in out:                                   # RFC 5987: UTF-8''%C6%8F...
        v = out["filename*"]
        enc, _, rest = v.partition("''")
        try:
            out["filename"] = unquote(rest or v, encoding=(enc or "utf-8"), errors="replace")
        except LookupError:
            out["filename"] = unquote(rest or v)
    return main, out


def boundary_of(content_type):
    main, p = _params(content_type or "")
    if main != "multipart/form-data":
        raise MultipartError("multipart/form-data gözlənilir")
    b = p.get("boundary")
    if not b or len(b) > 200:
        raise MultipartError("multipart sərhədi (boundary) tapılmadı")
    return b.encode("latin-1")


def parse(body, content_type, max_parts=64):
    """{name: Part}; eyni adlı bir neçə hissə olarsa birincisi saxlanılır (qalanları `name#2` ...)."""
    delim = b"--" + boundary_of(content_type)
    start = body.find(delim)
    if start < 0:
        raise MultipartError("multipart gövdəsində sərhəd tapılmadı")
    parts, pos = {}, start + len(delim)
    while True:
        if body[pos:pos + 2] == b"--":                      # closing delimiter
            break
        # skip the line break after the delimiter
        if body[pos:pos + 2] == b"\r\n":
            pos += 2
        elif body[pos:pos + 1] == b"\n":
            pos += 1
        else:
            raise MultipartError("multipart quruluşu pozulub (sərhəddən sonra sətir sonu yoxdur)")
        hdr_end, sep = body.find(b"\r\n\r\n", pos), 4
        lf_end = body.find(b"\n\n", pos)
        if hdr_end < 0 or (0 <= lf_end < hdr_end):
            hdr_end, sep = lf_end, 2
        if hdr_end < 0:
            raise MultipartError("multipart hissəsinin başlıqları bitmir")
        headers = {}
        for line in re.split(rb"\r?\n", body[pos:hdr_end]):
            if b":" in line:
                k, v = line.split(b":", 1)
                headers[k.decode("latin-1").strip().lower()] = v.decode("utf-8", errors="replace").strip()
        data_start = hdr_end + sep
        # the delimiter only counts at the start of a line (RFC 7578): CRLF--boundary (LF tolerated)
        nxt, lead = body.find(b"\r\n" + delim, data_start), 2
        if nxt < 0:
            nxt, lead = body.find(b"\n" + delim, data_start), 1
        if nxt < 0:
            raise MultipartError("multipart bağlanış sərhədi tapılmadı")
        data_end = nxt
        nxt += lead
        disp, p = _params(headers.get("content-disposition", ""))
        if disp != "form-data" or "name" not in p:
            raise MultipartError("Content-Disposition: form-data; name=... tələb olunur")
        name = p["name"]
        key, n = name, 2
        while key in parts:
            key, n = "%s#%d" % (name, n), n + 1
        parts[key] = Part(name, p.get("filename"), headers.get("content-type"), headers, body[data_start:data_end])
        if len(parts) > max_parts:
            raise MultipartError("multipart hissələrinin sayı çoxdur")
        pos = nxt + len(delim)
    return parts


def build(fields, files):
    """Sınaq və müştəri nümunələri üçün: (body, content_type). files = {name: (filename, bytes, ctype)}."""
    import uuid
    b = "----mikromodel" + uuid.uuid4().hex
    out = []
    for k, v in fields.items():
        out.append(("--%s\r\nContent-Disposition: form-data; name=\"%s\"\r\n\r\n" % (b, k)).encode("utf-8")
                   + str(v).encode("utf-8") + b"\r\n")
    for k, (fn, data, ct) in files.items():
        out.append(("--%s\r\nContent-Disposition: form-data; name=\"%s\"; filename=\"%s\"\r\n"
                    "Content-Type: %s\r\n\r\n" % (b, k, fn.replace('"', "%22"), ct or "application/octet-stream")).encode("utf-8")
                   + data + b"\r\n")
    out.append(("--%s--\r\n" % b).encode("ascii"))
    return b"".join(out), "multipart/form-data; boundary=%s" % b
