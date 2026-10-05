"""az_errors.py — Python istisnalarının istifadəçiyə göstərilən Azərbaycan dilində izahı.

İstifadə: "Fayl oxunmadı: %s" % az_exc(e); orijinal mətn ayrıca "detail" sahəsində saxlanılır (texniki yoxlama üçün).
"""
import zipfile

_BY_TEXT = [
    ("file is not a zip file", "fayl zip arxivi deyil (.xlsx faylı əslində Excel faylı deyil və ya zədələnib)"),
    ("unsupported format", "fayl formatı dəstəklənmir"),
    ("corrupt", "fayl zədələnib"),
    ("no such file", "fayl tapılmadı"),
    ("permission denied", "fayla giriş icazəsi yoxdur"),
    ("worksheet named", "tələb olunan vərəq tapılmadı"),
    ("no sheet named", "tələb olunan vərəq tapılmadı"),
    ("expected bof record", "fayl köhnə Excel (.xls) formatında deyil"),
    ("excel xlsx file; not supported", "xlrd .xlsx fayllarını oxumur — faylı .xls kimi saxlayın"),
    ("no columns to parse", "faylda sütun yoxdur (boş fayl)"),
    ("error tokenizing data", "CSV sətirlərində sütun sayı uyğun gəlmir"),
    ("timed out", "şəbəkə sorğusunun vaxtı bitdi"),
    ("name or service not known", "server ünvanı tapılmadı (internet bağlantısını yoxlayın)"),
    ("nodename nor servname", "server ünvanı tapılmadı (internet bağlantısını yoxlayın)"),
    ("connection refused", "server bağlantını rədd etdi"),
    ("http error 404", "fayl DSK saytında tapılmadı (404)"),
    ("certificate verify failed", "SSL sertifikatı yoxlanılmadı"),
]


def az_exc(e):
    """Qısa Azərbaycan dilində izah; tanınmayan xətalar üçün ümumi izah + xətanın növü."""
    if isinstance(e, zipfile.BadZipFile):
        return _BY_TEXT[0][1]
    if isinstance(e, UnicodeDecodeError):
        return "mətn kodlaşdırması oxunmadı (faylı UTF-8 kimi saxlayın)"
    if isinstance(e, FileNotFoundError):
        return "fayl tapılmadı"
    if isinstance(e, PermissionError):
        return "fayla giriş icazəsi yoxdur"
    if isinstance(e, MemoryError):
        return "fayl çox böyükdür (yaddaş çatmadı)"
    low = str(e).lower()
    for key, az in _BY_TEXT:
        if key in low:
            return az
    return "gözlənilməz xəta (%s) — texniki təfərrüat «detail» sahəsindədir" % type(e).__name__
