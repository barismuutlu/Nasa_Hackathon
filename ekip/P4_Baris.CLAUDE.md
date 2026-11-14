# P4 — Veri Katmanı + LİDER: Barış

Ortak kurallar, şema ve takvim kök `CLAUDE.md`'de. Bu dosya sadece senin rolün.

## Sahip olduğun dosyalar
- `app/query.py`, `contract.py`, `docs/CONTRACT.md`, `tests/smoke_test.py`
- `CLAUDE.md`, `ekip/*`, `requirements.txt`, `.gitignore`
- `data/mock/`, `data/deploy/`

## Liderlik
- Entegrasyon + hızlı kararlar. Şema/API değişiklik talepleri sana gelir → 5 dk içinde karar ver,
  kararı `docs/CONTRACT.md`'ye (değişiklik günlüğüyle) yaz, push et, gruba duyur.
- Her kontrol noktasında (10:30, 13:00, 16:30, 19:00) 5 dk toplantı: herkes "bitti / engel / sonraki".
- 15 dk'dan fazla takılan varsa yardım et ya da kapsamı küçült.
- Pazar 12:00 feature freeze'i uygula.

## Görev
1. **08:55** — repo iskeleti push: `CLAUDE.md`, `ekip/`, `.gitignore`, `requirements.txt`, klasörler.
   Herkese: `cp`/`echo "@ekip/<dosya>" > CLAUDE.local.md` talimatı.
2. **11:00** — `data/mock/hotspots_mock.parquet`: CONTRACT §1 şemasıyla sentetik veri (`version="MOCK"`)
   (Aachen/Eifel + La Rioja, 2000–2026, tüm uydular, VIIRS eklenince sayılar artsın,
   Nisan 2011 & Ağustos 2026 Venn'de pik). `weight_harm` = basit sahte değer. → Yusuf (P5).
3. **`app/query.py`** — API: CONTRACT §7.4:
   - `PRESETS`: `"Aachen/Eifel": (5.9, 50.2, 7.0, 50.9)`, `"La Rioja (AR)": (-69.7, -31.9, -65.4, -27.6)`,
     `"Hohes Venn": (5.95, 50.45, 6.25, 50.60)`
   - `get_hotspots()` — bbox ya da GeoJSON Polygon (shapely ile içerde mi), tarih filtresi.
     Parquet'i `@st.cache_data` olmadan oku (query.py Streamlit'e bağımlı olmasın); önbellek P5'te.
   - `monthly_matrix()` — yıl × ay pivot; eksik ay 0; o yıl hiç uydu yoksa (2000 Ocak–Ekim) NaN.
   - `anomaly()` — aynı ayın diğer yıllarına göre ortalama, std, z, sıra; label:
     z>2 "çok yüksek", z>1 "yüksek", |z|≤1 "normal", z<−1 "düşük".
   - `to_csv_bytes()` — CSV indirme verisi.
4. **16:30** — gerçek veriyle (`hotspots_harm.parquet`) çalışıyor.
5. **Pazar sabah** — `data/deploy/`: Streamlit Cloud için sadece preset bölgeler, <50 MB → Yusuf.

## Teslimler
| Saat | Ne | Kime |
|---|---|---|
| 08:55 | Repo iskeleti | herkes |
| 11:00 | Mock parquet + query.py ilk sürüm | Yusuf (P5) |
| 16:30 | query.py gerçek veriyle | Yusuf (P5) |
| Pazar 09:00 | `data/deploy/` | Yusuf (P5) |

## Teslim öncesi (Pazar, feature freeze'den önce)
- [ ] `README.md` İngilizceye çevrilecek (şu an Türkçe; jüri İngilizce okuyacak). Yer tutucuları doldur:
      demo linki, sunum linki, R²/sapma (docs/validation/metrics.json).
- [ ] Repo public yapılacak (jüri "projenin tamamını" değerlendiriyor).

## Bitti kontrolü
- [ ] `monthly_matrix(get_hotspots(PRESETS["Hohes Venn"]), "harm")` → 2011-04 ve 2026-08 > 0
- [ ] Mock ve gerçek veri arasında geçişte app.py'de tek satır değişmiyor
- [ ] Bölge çizimi (GeoJSON) ile bbox aynı sonucu veriyor (dikdörtgen çizimde)
