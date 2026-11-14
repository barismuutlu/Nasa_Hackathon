# P5 — Arayüz: Yusuf

Ortak kurallar ve takvim kök `CLAUDE.md`'de, şema/API **`docs/CONTRACT.md` v1.1**'de. Bu dosya sadece senin rolün.

## Sahip olduğun dosyalar (Claude SADECE bunlara yazar)
- `app/app.py`
- `.streamlit/config.toml`

## Veri erişimi
Parquet'i **doğrudan okuma**. Sadece `app/query.py` API'si (CONTRACT §7.4):
```python
from query import PRESETS, MONTH_LABELS, data_info, get_hotspots, monthly_matrix, anomaly, to_csv_bytes
```
`data_info()["is_mock"]` True ise sayfanın üstünde **"SENTETİK TEST VERİSİ"** uyarısı göster.
`data_info()["has_harm"]` False ise harmonize düğmesi "henüz hazır değil" desin.
Ağır çağrıları `@st.cache_data` ile sar. API'de eksik bir şey varsa → Barış'a söyle, query.py'ye yazma.
Sentetik veri `data/mock/` içinde hazır — `git pull` yeter.

## Görev (Streamlit)
1. **Kenar çubuğu** — hazır bölge seçimi (`PRESETS`: Aachen/Eifel, La Rioja, Hohes Venn),
   tarih aralığı, **Ham / Harmonize** düğmesi (`mode="raw"` / `"harm"`), CSV indir butonu.
2. **Harita** — `streamlit-folium` + `folium.plugins.Draw` (dikdörtgen/çokgen). Çizilen GeoJSON →
   `get_hotspots(geom)`. Seçili bölgenin noktaları (çok fazlaysa örnekle, ≤5000).
3. **Takvim ısı haritası** — `plotly` `go.Heatmap`: x = ay (Oca…Ara), y = yıl, renk `viridis`,
   hover: yıl, ay, değer. NaN hücreler gri. Ham ↔ harmonize geçişte renk ölçeği ayrı.
4. **Anomali kartı** — seçili (yıl, ay) için `anomaly()`: `st.metric` değer + z + label.
   Isı haritasında tıklanan hücre seçimi (`plotly_events` yoksa selectbox yeterli).
5. **Açıklama satırı** — "Ham: tüm uyduların tespit sayısı. Harmonize: MODIS-eşdeğeri tahmin."
   Metinlerde "yangın" değil "tespit" (CONTRACT §8); anomali kartı = tespit sayısı anomalisi.
6. **Yayın (Pazar sabah)** — Streamlit Cloud, ana dosya `app/app.py`, veri `data/deploy/`.

## Teslimler
| Saat | Ne | Kime |
|---|---|---|
| 13:00 | Mock veriyle uygulama ayakta (harita + takvim) | herkes |
| 16:30 | Ham takvim gerçek veriyle uçtan uca | Barış |
| 19:00 | MVP: harita + çizim + takvim + anomali + düğme + CSV | İbrahim (test) |
| Pazar 10:00 | Streamlit Cloud linki | İbrahim (P6), Barış |

## Bitti kontrolü
- [ ] Hohes Venn seçince Nisan 2011 ve Ağustos 2026 takvimde belirgin
- [ ] La Rioja'da Ham → Harmonize geçişte 2012/2018/2024 sıçraması kayboluyor
- [ ] Boş bölge çizilince çökmüyor ("Bu bölgede tespit yok" mesajı)
- [ ] Sayfa ilk açılış < 5 sn (cache)

## Claude'a not
- Görsel tutarlılık: viridis, tek font, başlıklar Türkçe + İngilizce kısa (jüri yabancı olabilir).
- Yeni paket gerekiyorsa ekleme; "Barış'a söyle, requirements'a eklesin" de.
- Feature freeze (Pazar 12:00) sonrası sadece bug fix.
