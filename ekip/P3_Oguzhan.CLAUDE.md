# P3 — ML & Doğrulama: Oğuzhan

Ortak kurallar ve takvim kök `CLAUDE.md`'de, şema **`docs/CONTRACT.md`** (güncel sürüm)'de. Bu dosya sadece senin rolün.

## Sahip olduğun dosyalar (Claude SADECE bunlara yazar)
- `pipeline/validate.py`
- `docs/validation/` (grafikler + metrikler)

## Girdi / çıktı
- Girdi: `data/monthly_grid.parquet`, `data/hotspots_harm.parquet`, `data/k_factors.csv` (P2).
  P2 hazır olana kadar mock/sample veriyle iskeleti kur.
- Çıktılar (`docs/validation/`, git'e commit):
  - `metrics.json` — CONTRACT §7.3: `[{"method","region","split","scale","r2","bias","bias_pct","n"}]`
  - `pred_vs_true.png` — tahmin (`n_harm` VIIRS'ten) vs gerçek (`n_modis`) saçılım, log-log, 1:1 çizgisi
  - `annual_raw_vs_harm.png` — Arjantin yıllık ham / harmonize / MODIS
  - `venn_check.png` — Hohes Venn takvim kesiti (Nisan 2011, Ağustos 2026)

## Görev
1. **Bölünme** — Eğitim 2012–2021 (P2 k'yı buradan öğrenir), **Test 2022–2024**.
2. **Tahmin vs gerçek** — test yıllarında hücre × ay bazında:
   tahmin = VIIRS satırlarının `Σ weight_harm`, gerçek = `n_modis`.
   - En az bir tarafı > 0 olan hücre-aylar. Ayrıca 1°'ye toplayarak da hesapla (gürültü az).
3. **Metrikler** — R², bias = ortalama(tahmin − gerçek), bias % = Σ tahmin / Σ gerçek − 1.
   Arjantin (eğitim bölgesi) ve `aachen_eifel` (transfer) **ayrı ayrı** raporla.
4. **Venn kontrolü** — Hohes Venn kutusu (lon 5.95–6.25, lat 50.45–50.60):
   Nisan 2011 (sadece MODIS dönemi) ve Ağustos 2026 (VIIRS) ham + harmonize sayılarda görünüyor mu?
   O ayın anomali z-skoru ne? Sonuç: evet/hayır + sayılar.
5. **Zaman kalırsa: Yöntem B** — lojistik regresyon (scikit-learn): VIIRS tespiti için
   p(aynı gün ±1 km içinde MODIS tespiti var). Özellikler: `frp, brightness, scan, track, daynight,
   satellite, enlem bandı, mevsim`. (`brightness` MODIS ile VIIRS arasında karşılaştırılamaz, dikkat.) Ağırlık = p / n_active_viirs. Aynı metriklerle A vs B tablosu.
   → Barış'a söyle; seçilirse P2 entegre eder.

## Teslimler
| Saat | Ne | Kime |
|---|---|---|
| 17:30 | Metriklerin ilk hali (Yöntem A) | Barış |
| 19:00 | `docs/validation/` tamamı + 3 cümlelik özet ("R²=…, bias=…, Venn görünüyor") | İbrahim (P6) |

## Bitti kontrolü
- [ ] Test yılları hiçbir şekilde k hesabına girmedi (P2 ile teyit)
- [ ] Grafikler sunuma hazır: eksen etiketleri, birimler, büyük font, başlık
- [ ] `python pipeline/validate.py` tek komutla tüm çıktıları yeniden üretiyor

## Claude'a not
- `harmonize.py`'yi değiştirme; k yöntemi hakkında öneri varsa kullanıcıya not olarak ver.
- Grafiklerde matplotlib, renk haritası viridis (uygulamayla tutarlı).
- R² negatif/çok düşük çıkarsa saklama — kullanıcıya açıkça söyle; pitch'te dürüstçe anlatılır.
- Venn sonucunu "tespit artışı" olarak yaz, "yangın tespit edildi" değil (CONTRACT §8).
