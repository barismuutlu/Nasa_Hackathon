# P2 — Harmonizasyon: Bahtiyar

Ortak kurallar, şema ve takvim kök `CLAUDE.md`'de. Bu dosya sadece senin rolün.

## Sahip olduğun dosyalar (Claude SADECE bunlara yazar)
- `pipeline/harmonize.py`

## Girdi / çıktı
- Girdi: `data/hotspots.parquet` (P1). 12:30'a kadar `data/sample/` + `data/mock/` ile geliştir.
- Çıktılar:
  - `data/hotspots_harm.parquet` — girdiyle aynı şema, `weight_harm` dolu
  - `data/monthly_grid.parquet` — §3.2
  - `data/k_factors.csv` — `lat_band, season, satellite, k, n_modis, n_viirs, fallback`

## Görev (Yöntem A — tanım kök `CLAUDE.md` §3.3)
1. **Grid + ay** — 0.25° hücre (`cell_lat/cell_lon` = hücre merkezi), hücre × ay × uydu sayıları.
2. **Yardımcı sütunlar** (parquet'e YAZMA, sadece hesapta):
   - `lat_band` = |lat| 10°'lik dilim: `"20-30"`, `"30-40"`, `"40-50"`, `"50-60"` …
   - `season` = yerel mevsim: güney yarımkürede ay +6 kaydır, sonra DJF=winter, MAM=spring,
     JJA=summer, SON=autumn.
3. **k katsayıları** — Eğitim: **Arjantin, 2012–2021**. Her `(lat_band, season, satellite)` için
   `k = Σ MODIS / Σ VIIRS_satellite` — sadece hem MODIS hem o VIIRS uydusunun aktif olduğu aylar.
   - Az örnek (n_modis < 30): aynı `season`+`satellite` için tüm bantları birleştir → `fallback=True`.
   - Eğitimde olmayan bant (ör. Almanya 50-60 boşsa): en yakın bant / mevsim ortalaması, `fallback=True`.
4. **weight_harm** —
   - MODIS, tarih < S-NPP ilk tarih → 1.0; sonrası → 0.0
   - VIIRS → `k / n_active_viirs(acq_date)` (aktif uydu tarihleri P1'in özet tablosundan)
5. **Uygula: her yer** (Arjantin dışı da).
6. **Özet yazdır** — Arjantin için yıllık ham toplam vs harmonize toplam; 2012/2018/2024 sıçraması
   harmonizede kayboluyor mu?

## Teslimler
| Saat | Ne | Kime |
|---|---|---|
| 14:30 | `k_factors.csv` ilk sürüm | Oğuzhan (P3), Barış |
| 16:30 | `hotspots_harm.parquet` + `monthly_grid.parquet` | Barış (P4), Oğuzhan (P3) |

## Bitti kontrolü
- [ ] `weight_harm` hiç NaN değil, hepsi ≥ 0
- [ ] Arjantin 2012–2021 `Σ weight_harm` ≈ `Σ MODIS` (fark < %10)
- [ ] k tablosunda her satırın `n_modis`, `n_viirs` değeri var; fallback'ler işaretli
- [ ] Ham yıllık seride 2012/2018/2024 basamakları var, harmonizede yok (grafiği P6'ya at)

## Claude'a not
- `pipeline/validate.py` Oğuzhan'ın; test/metrik kodu oraya yazılmaz, buraya da yazılmaz.
- k'yı test yıllarıyla (2022–2024) **eğitme** — veri sızıntısı.
- `weight_harm` tanımını değiştirmek gerekirse kod yazma; "Barış'a sor" de.
