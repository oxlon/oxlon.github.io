# data/ministry — Nazirliyin CAEM iş kitabının sabitlənmiş nüsxəsi

| Fayl | Mənbə | MD5 | Tarix |
|---|---|---|---|
| `CAEM.xlsx` | `Macro_MinistryUnit/Ministry_CAEM/CAEM.xlsx` (dəyişdirilmədən köçürülüb) | `12c22d22eda046e050643004a8d7eec5` | faylın tarixi 22.09.2026; köçürülmə 06.10.2026 |

`CAEM.xlsb` (MD5 `014263b8d7c16e821cdc0b6f87281f2b`, 23.01.2026) eyni 54 vərəqli iş kitabıdır, lakin
`pyxlsb` quraşdırılmadığı üçün oxunmur. xlsx nüsxəsində makrolar yoxdur (bax: C6 qüsurlar reyestri).

## Nə üçün nüsxə
- Testlər və yenidən hesablama oflayn və təkrarlana bilən olsun (NFR1).
- `riskunit.caem_model.vintage_status()` nüsxənin MD5-ni yuxarı axındakı faylla müqayisə edir; fərq
  varsa yeni vintaj deməkdir (NFR2): faylı yenidən köçürün, `CAEM_MD5`-i yeniləyin və
  `python3 -m riskunit.caem` işə salın.
- Fayl yalnız `openpyxl` ilə `read_only=True, data_only=True` (dəyərlər) və ya `data_only=False`
  (düsturlar, sübut üçün) rejimində açılır. Heç vaxt yazılmır.

## İstifadə olunan vərəqlər və diapazonlar
| Vərəq | Diapazon | Nə üçün |
|---|---|---|
| `Risk-oil price` | A5:B255 (aylıq Brent), L5:M30 (illik), M33:M34, N1:T31 | C1 siqnal, zolaq kəsikləri, 0–5 şkala |
| `Risk-food price` | A5:C267 (aylıq FAO, illik artım), M16:O42, O45:O46, P1:V43, M51:N56 | C1 |
| `Risk-import price` | B5:D25, D28:D29, E1:K26 | C1 |
| `Risk-gdp tp` | B5:D34, D37:D38, E1:K4 | C1 |
| `Balance of risks` | A1:E19 | C2 (Nazirlik balları, çəkilər, oxu qaydası) |
| `AZE Model` | C5:AX52 (A0), C56:AX103 (A1), C107:AX154 (A2), C159:C206 (Ac), C211:AX258 (B1), C262:AX309 (B2) | C4/C5 |
| `8a. Simulation` | A5:P52 (şok matrisi), A62:P109 (impuls cavabları), E108:P109 (borc düsturları) | C4 yoxlama |
| `Parametrization` | G26 (ψ, daxili borc payı = 0,3) | C4 |
| `Oil_and_gas_sector` | D69:AL69 (model Brent) | C1, C6 |
| `1d. Real GDP - Expenditure`, `7. Scenario`, `Fancharts`, `6a. SEI`, `8b. Summary`, `INPUT` | qüsur sübutları | C6 |
