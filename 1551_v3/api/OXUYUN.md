# Baza məlumatı API-si — MİİS §15.5.1

Makroiqtisadi proqnoz modellərinin baza məlumatını Nazirliyin məlumat anbarı ilə
birləşdirmək üçün interfeys. İki istiqamətdə işləyir:

* **Oxumaq** — anbar modelin bütün baza sıralarını və müşahidələrini götürə bilər
  (tam və ya yalnız dəyişənləri).
* **Yazmaq** — yeni faktiki məlumat nöqtələri API vasitəsilə daxil edilir; modeldə
  «Məlumat mübadiləsi» bölməsindən bir kliklə tətbiq olunur.

---

## 1. İşə salmaq

Python 3.10+ kifayətdir — **heç bir paket quraşdırmaq lazım deyil**.

```bash
cd api
python3 server.py --seed catalogue.json     # bazanı ilk dəfə doldurur (bir dəfə)
python3 server.py                           # http://127.0.0.1:8787
```

Yoxlama:

```bash
curl http://127.0.0.1:8787/v1/health
```

### Nişanlar (tokens)

```bash
export API_TOKENS="anbar-oxu:read,anbar-yaz:write"
export API_ORIGINS="*"          # paket diskdən açılırsa olduğu kimi saxlayın
python3 server.py --host 0.0.0.0 --port 8787
```

`write` səlahiyyəti avtomatik olaraq `read` səlahiyyətini də əhatə edir.
Standart sınaq nişanları: `demo-read`, `demo-write` — **istehsalda mütləq dəyişdirin**.

---

## 2. Məlumatın quruluşu

Hər sıra iki hissə ilə ünvanlanır:

| Sahə | İzah | Nümunə |
|---|---|---|
| `model` | `bum` — aşağıdan-yuxarı model, `caem` — CAEM | `bum` |
| `code` | dəyişənin adı | `CPI`, `NEER`, `Exp_coeff_1` |
| `period` | il (illik tezlik) | `2025` |
| `value` | ədəd və ya `null` | `1.95` |

Kataloqda **559 sıra** var: aşağıdan-yuxarı modeldən 100 (EViews dəyişənləri),
CAEM-dən 459 (fərziyyələr, əmsallar, əlavə amillər, açarlar).
Hər sıra üçün mənbə Excel vərəqi və sətri də saxlanılır.

---

## 3. Anbara yükləmək (oxumaq)

İlk tam yükləmə:

```bash
curl -H "Authorization: Bearer anbar-oxu" \
     "http://127.0.0.1:8787/v1/observations?limit=50000" > baza.json
```

Cavabdakı `max_seq` dəyərini yadda saxlayın. Sonrakı dəfələr yalnız dəyişənləri gətirin:

```bash
curl -H "Authorization: Bearer anbar-oxu" \
     "http://127.0.0.1:8787/v1/observations?since_seq=4326"
```

Kataloq (sıraların siyahısı, ölçü vahidləri, mənbə vərəqləri):

```bash
curl -H "Authorization: Bearer anbar-oxu" "http://127.0.0.1:8787/v1/series?model=bum"
```

---

## 4. Yeni məlumat daxil etmək (yazmaq)

Əvvəlcə **yoxlama rejimində** (heç nə yazılmır, nəyin dəyişəcəyi görünür):

```bash
curl -X POST -H "Authorization: Bearer anbar-yaz" -H "Content-Type: application/json" \
  "http://127.0.0.1:8787/v1/observations?dry_run=1" \
  -d '{"actor":"dovlet.statistika","source":"DSK 2025 yekun","items":[
        {"model":"bum","code":"CPI","period":2025,"value":1.95},
        {"model":"bum","code":"NEER","period":2025,"value":0.81}]}'
```

Sonra həqiqi yazı — eyni sorğu, `?dry_run=1` olmadan.

Cavabda hər nöqtə üçün nəticə qayıdır: `insert` və ya `update`, əvvəlki dəyər və
yeni `revision`. Qəbul edilməyən nöqtələr `errors` massivində səbəbi ilə göstərilir:

| Səbəb | Mənası |
|---|---|
| `unknown_series` | Bu `model`/`code` cütü kataloqda yoxdur |
| `period_out_of_range` | İl 1990–2100 aralığından kənardır |
| `bad_item` | Dəyər ədəd deyil və ya məcburi sahə çatmır |

Bir sorğuda maksimum 20 000 nöqtə. Qismən uğur mümkündür: düzgün nöqtələr tətbiq
olunur, səhvlər ayrıca qayıdır.

### Tarixçə

Hər dəyişiklik saxlanılır — kim, nə vaxt, hansı mənbədən, köhnə və yeni dəyər:

```bash
curl -H "Authorization: Bearer anbar-oxu" \
     "http://127.0.0.1:8787/v1/history?model=bum&code=CPI"
```

---

## 5. Modeldə istifadə

Paneldə: **aşağıdan-yuxarı model → İdarəetmə**, **CAEM → Yeniləmə** bölməsində
«Məlumat mübadiləsi (API)» kartı var.

1. API ünvanını və nişanı yazın, «Əlaqəni yoxla».
2. «Anbardan yeni məlumatı gətir» — anbardakı dəyərlər modeldəkilərlə tutuşdurulur
   və yalnız **fərqlər** siyahı şəklində göstərilir (kod, il, modeldəki dəyər,
   anbardakı dəyər, mənbə).
3. Lazımsız sətirlərin işarəsini götürün və «Tətbiq et» — dəyərlər modelə yazılır,
   bütün asılı düsturlar yenidən hesablanır. Dəyişiklik ssenari kimi qeyd olunur və
   «Bazaya qaytar» ilə geri alına bilər.

Sarı fonlu sətirlər modelin proqnoz dövrünə düşür — onları tətbiq etmək hesablanmış
dəyərin üzərinə yazmaq deməkdir.

«Proqnozu anbara göndər» düyməsi modelin cari proqnozunu adlandırılmış versiya
(vintage) kimi anbara yazır.

---

## 6. Təhlükəsizlik qeydləri

* Bu server **istinad tətbiqidir**. İstehsalda onu reverse proxy (nginx və s.)
  arxasında, HTTPS ilə işlədin və ya `openapi.yaml` müqaviləsini öz stekinizdə
  tətbiq edin.
* Nişanları mühit dəyişəni ilə verin, fayla yazmayın.
* Yazma səlahiyyətini yalnız məsul şəxslərə verin — hər yazı `actor` sahəsi ilə
  qeydə alınır.
* `API_ORIGINS` ilə icazə verilən mənbələri məhdudlaşdırın. Paket diskdən (file://)
  açılırsa, brauzer `Origin: null` göndərir — bu hal dəstəklənir.

---

## 7. Fayllar

| Fayl | Nədir |
|---|---|
| `openapi.yaml` | Rəsmi müqavilə (OpenAPI 3.1) — 8 endpoint, 5 sxem |
| `server.py` | İstinad serveri (yalnız standart kitabxana, SQLite) |
| `catalogue.json` | 559 sıra və 5 172 başlanğıc nöqtəsi — bazanı doldurmaq üçün |
| `sync_example.py` | Anbara artımlı yükləmə nümunəsi |
| `miis.db` | SQLite bazası (server yaradır) |
