# FR10 və FR12 dəftərlərinin mənbə faylları

`FR10.ipynb` və `FR12.ipynb` dəftərləri bu qovluqdakı hissə fayllarından yığılır (`src/pNN_*.py`; xanalar
`# %%` və `# %% [markdown]` işarələri ilə ayrılır). Dəftəri birbaşa redaktə etmək də mümkündür, lakin böyük
dəyişikliklər üçün mənbə fayllarını redaktə edib dəftəri yenidən yığmaq tövsiyə olunur:

```bash
python3 tools/notebook_src/fr10/build.py --out FR10.ipynb
python3 tools/notebook_src/fr12/build.py --out FR12.ipynb
python3 run_all.py --stage FR10          # FR10 → FR12 → panel → sayt
```

Diqqət: dəftəri birbaşa redaktə etmisinizsə, yenidən yığmazdan əvvəl həmin dəyişiklikləri mənbə fayllarına köçürün —
əks halda yığma onları silir. Yığılmış dəftərin xana mətnləri mənbə ilə eynidir (2026-10-05 tarixində yoxlanılıb).
