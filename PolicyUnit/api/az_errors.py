"""az_errors.py — Python istisnalarının istifadəçiyə göstərilən Azərbaycan dilində izahı.

İstifadə: "Hesablama alınmadı: %s" % az_exc(e); orijinal mətn ayrıca «detail» sahəsində saxlanılır.
(RiskUnit/api/az_errors.py-dən uyğunlaşdırılıb + siyasət modulunun mühərrik xətaları.)
"""
import zipfile

_BY_TEXT = [
    ("file is not a zip file", "fayl zip arxivi deyil (.xlsx faylı zədələnib)"),
    ("no such file", "fayl tapılmadı"),
    ("yuxarı axın faylı tapılmadı", "yuxarı axın faylı tapılmadı (MIIS_MICRO_DIR / MIIS_RISK_DIR yoxlayın)"),
    ("permission denied", "fayla giriş icazəsi yoxdur"),
    ("no columns to parse", "faylda sütun yoxdur (boş fayl)"),
    ("error tokenizing data", "CSV sətirlərində sütun sayı uyğun gəlmir"),
    ("override nəzərə alınmadı", "MikroUnit mühərriki override açarını tanımadı (açar adını yoxlayın)"),
    ("mühərrik xətası", "MikroUnit mühərrikində xəta"),
    ("modullar işləmədi", "MikroUnit zəncirinin bəzi modulları işləmədi"),
    ("naməlum əmsal", "naməlum FR1 əmsalı"),
    ("naməlum ekzogen", "naməlum FR1 ekzogen dəyişəni"),
    ("no module named 'microlib'", "MikroUnit paketi (microlib) tapılmadı — MIIS_MICRO_DIR yoxlayın"),
    ("no module named", "Python modulu tapılmadı (numpy/pandas/scipy olan Python seçin: POLICY_PYTHON)"),
    ("could not broadcast", "şok yolunun uzunluğu illərin sayına uyğun deyil (2026–2030 üçün 5 dəyər)"),
    ("operands could not be broadcast", "şok yolunun uzunluğu illərin sayına uyğun deyil (2026–2030 üçün 5 dəyər)"),
    ("could not convert", "ədəd gözlənilirdi"),
    ("timed out", "vaxt limiti bitdi"),
    ("connection refused", "server bağlantını rədd etdi"),
    ("name or service not known", "server ünvanı tapılmadı (internet bağlantısını yoxlayın)"),
    ("nodename nor servname", "server ünvanı tapılmadı (internet bağlantısını yoxlayın)"),
    ("ssenari yoxlanışı uğursuz", "ssenari yoxlanışı uğursuz oldu (errors siyahısına baxın)"),
    ("naməlum siyasət aləti", "naməlum siyasət aləti (config/instruments.csv)"),
    ("naməlum kpi", "naməlum KPI (config/kpi.csv)"),
    ("ən azı 5", "ən azı 5 fərqli KPI seçilməlidir"),
    ("caem.xlsx", "CAEM iş kitabı tapılmadı və ya dəyişib (data/ministry/CAEM.xlsx)"),
    ("no module named 'policyunit", "PolicyUnit modulu tapılmadı (mühərrik hələ qoşulmayıb)"),
    ("database is locked", "verilənlər bazası məşğuldur — bir azdan təkrarlayın"),
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
        return "yaddaş çatmadı (ssenari sayını azaldın)"
    if isinstance(e, ZeroDivisionError):
        return "sıfıra bölmə (baza dəyəri sıfırdır)"
    low = str(e).lower()
    for key, az in _BY_TEXT:
        if key in low:
            return az
    if isinstance(e, KeyError):
        return "tələb olunan sütun və ya açar tapılmadı: %s" % e
    if isinstance(e, (ValueError, TypeError)):
        return "giriş dəyəri yanlışdır"
    return "gözlənilməz xəta (%s) — texniki təfərrüat «detail» sahəsindədir" % type(e).__name__
