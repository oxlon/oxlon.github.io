# Makro modulun məlumatları — FR3, FR4, FR5 (v2.2)

Mənbə (yalnız oxunur): `/Users/econ0757/My Drive/OxLon/18august/model/data/` (Nazirliyin §15.5.1 makro modulu).
Fayllar dəyişdirilmədən, `fr345_` prefiksi ilə köçürülüb (FR1 agentinin fayllarından ayırmaq üçün). Köçürmə: 2026-10-05.

| fayl (bu qovluqda) | mənbə faylı | MD5 | istifadə |
|---|---|---|---|
| `fr345_public_sources_panel.csv` | `data/public_sources_panel.csv` | `fd4967d5847759202c3b905ef4f44f08` | FR3: DSK 4.5–4.8 fəaliyyət × mülkiyyət üzrə əmək haqları və DSK 2.12 muzdlu işçilər (2005–2024) → sektor və büdcə/qeyri-büdcə əmək haqları (Hissə 20A) |
| `fr345_public_sources_provenance.csv` | `data/public_sources_provenance.csv` | `c8efd3a693a172e28d1b36fc070fce98` | yuxarıdakı panelin mənbə cədvəlləri, sətir/sütun yerləri |
| `fr345_moe_spec_panel.csv` | `data/moe_spec_panel.csv` | `3eccc1db06d5d1a1ed98f33b747ebe67` | FR4: dövlət istehlakı `GC` (MOE SNA, 1995–2024) — E8-ə struktur alternativlər (Hissə 16.2); `W_*`, `L_*` yoxlama üçün |
| `fr345_moe_spec_provenance.csv` | `data/moe_spec_provenance.csv` | `792f783a97a3db000e6179930cff8beb` | Nazirliyin iş kitablarında sətir yerləri |
| `fr345_ministry_equations_catalog.csv` | `data/ministry_equations_catalog.csv` | `b851ee3a9f84fc72d7b5b4e0fcb0bb56` | FR5: Nazirliyin öz pullu xidmətlər tənliyi (`MOE SOCIAL.xlsx`, eq8: Δln SERVICES_PAID = −0,0055 + 1,07042 Δln TRADE + 0,377245 Δln WAGE) — E1 ilə müqayisə (Hissə 18.2) |

Yoxlamalar: DSK 4.5–4.8 dövlət / qeyri-dövlət orta əmək haqları FR3-ün `w_state` / `w_priv` sıraları ilə 2005–2024-də dəqiq
eynidir; 2.12 fəaliyyətlərinin cəmi dərc olunmuş yekuna bərabərdir; FR4-ün öz faylı `data/dsk/002_12-13en.xls` (`Dynamics_2.12`)
eyni məlumatı verir (2023 və 2024 vərəqləri ilə dəqiq üst-üstə düşür).
