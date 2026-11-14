# CLAUDE.md — Space Apps 2026: MODIS ↔ VIIRS Yangın Takvimi

> Bu dosya tüm ekip için ortaktır. Sahibi: **P4 Barış**. Değişiklik → önce Barış'a sor.

## 0. Claude için ilk adım (ZORUNLU)
1. Kullanıcının rolünü `CLAUDE.local.md` dosyasından öğren (gitignore'da, herkesin kendi makinesinde).
2. `CLAUDE.local.md` yoksa kullanıcıya **"Hangi roldesin (P1–P6)?"** diye sor, sonra
   `ekip/` altındaki ilgili dosyayı oku ve kullanıcıya şu içerikle `CLAUDE.local.md` oluşturmayı öner:
   ```
   @ekip/P1_Suleyman.CLAUDE.md
   ```
3. **Sadece o rolün sahip olduğu dosyalara yaz.** Başka birinin dosyasında değişiklik gerekiyorsa
   kodu yazma; kullanıcıya "şu kişiye şunu söyle" diye kısa bir not ver.
4. Şema (bölüm 3) veya API (bölüm 4) değişikliği gerekiyorsa: dur, kullanıcıya "önce P4'e sor" de.

## 1. Proje
NASA FIRMS aktif yangın tespitleri ile 2000–2026 arası **tutarlı bir aylık yangın takvimi**.
Sorun: MODIS (Terra/Aqua, 2000→) ve VIIRS (S-NPP 2012→, NOAA-20 2018→, NOAA-21 2024→) farklı
hassasiyette; her yeni uydu ham sayılarda **yapay sıçrama** yaratır. Biz VIIRS tespitlerini
**MODIS-eşdeğeri** birime çevirip (harmonizasyon) kesintisiz bir seri gösteriyoruz.

Pitch'in ana görseli: ham takvimde 2012/2018/2024 sıçramaları → harmonize takvimde yok.
Doğrulama hikâyesi: Hohes Venn (Aachen/Eifel) yangınları **Nisan 2011** ve **Ağustos 2026** görünmeli.

## 2. Ekip & dosya sahipliği
| Rol | Kişi | Sahip olduğu dosyalar |
|---|---|---|
| P1 Veri Mühendisi | Süleyman | `pipeline/ingest.py`, `data/sample/` |
| P2 Harmonizasyon | Bahtiyar | `pipeline/harmonize.py` |
| P3 ML & Doğrulama | Oğuzhan | `pipeline/validate.py`, `docs/validation/` |
| P4 Veri Katmanı + LİDER | Barış | `app/query.py`, `CLAUDE.md`, `ekip/`, `requirements.txt`, `.gitignore`, `data/mock/`, `data/deploy/` |
| P5 Arayüz | Yusuf | `app/app.py`, `.streamlit/config.toml` |
| P6 Sunum & Test | İbrahim | `docs/pitch/` |

Ortak dosyalara (`requirements.txt` vb.) paket eklemek gerekirse → Barış'a söyle, o ekler.

## 3. Veri şeması (KİLİTLİ — değişiklik sadece P4 onayıyla)

### 3.1 `data/hotspots.parquet` (P1 yazar) ve `data/hotspots_harm.parquet` (P2 yazar, aynı şema)
| Sütun | Tip | Açıklama |
|---|---|---|
| `lat` | float64 | enlem |
| `lon` | float64 | boylam |
| `acq_date` | datetime64[ns] | UTC tarih (saat 00:00) |
| `acq_time` | int16 | UTC HHMM (ör. 1342) |
| `year` | int16 | |
| `month` | int8 | 1–12 |
| `instrument` | category | `"MODIS"` \| `"VIIRS"` |
| `satellite` | category | `"Terra"` \| `"Aqua"` \| `"SNPP"` \| `"NOAA20"` \| `"NOAA21"` |
| `confidence` | category | `"low"` \| `"nominal"` \| `"high"` (MODIS: <30 low, 30–79 nominal, ≥80 high) |
| `confidence_raw` | string | orijinal değer (MODIS 0–100, VIIRS l/n/h) |
| `frp` | float32 | Fire Radiative Power, MW |
| `bright` | float32 | MODIS `brightness` / VIIRS `bright_ti4` (K) |
| `scan` | float32 | piksel boyutu (km) |
| `track` | float32 | piksel boyutu (km) |
| `daynight` | category | `"D"` \| `"N"` |
| `fire_type` | Int8 (nullable) | archive `type` (0 bitki,1 volkan,2 statik,3 deniz); NRT'de null |
| `source` | category | `"archive"` \| `"nrt"` |
| `weight_harm` | float32 | P1: NaN yazar. P2: doldurur (bkz. 3.3) |

### 3.2 `data/monthly_grid.parquet` (P2 yazar)
`cell_lat, cell_lon, year, month, n_modis, n_snpp, n_noaa20, n_noaa21, n_harm`
- Grid 0.25°: `cell_lat = floor(lat/0.25)*0.25 + 0.125` (hücre merkezi), `cell_lon` aynı.
- `n_harm = Σ weight_harm` (o hücre-ay).

### 3.3 `weight_harm` tanımı (karar — değişiklik → P4)
Harmonize seri = **MODIS-eşdeğeri tespit sayısı** = `Σ weight_harm`.
- MODIS satırı, `acq_date` < VIIRS S-NPP ilk tarih (~2012-01-20) → `1.0`
- MODIS satırı, sonrası → `0.0` (bu dönemde seriyi VIIRS taşır; MODIS sadece doğrulama için)
- VIIRS satırı → `k(lat_band, season, satellite) / n_active_viirs(acq_date)`
  - `k = MODIS / VIIRS` (P2, Arjantin 2012–2021 eğitim verisinden)
  - `n_active_viirs` = o tarihte aktif VIIRS uydu sayısı (1, 2 veya 3) → uydu eklenince sıçrama olmaz
  - `lat_band` = |enlem| 10°'lik dilim (`"20-30"`, `"30-40"` …), `season` = **yerel** mevsim
    (güney yarımkürede ay +6 kaydırılır) → Arjantin'de öğrenilen k, Almanya'ya taşınabilir
- Yöntem B (P3, zaman kalırsa): lojistik regresyon ile her VIIRS tespiti için p(MODIS görür) → `weight_harm`.

### 3.4 Dosya konumları
```
data/raw/         FIRMS CSV'leri (git'e GİRMEZ)
data/sample/      P1'in örnek dosyası (küçük, git'e girer)
data/mock/        P4'ün sahte parquet'i (git'e girer)
data/deploy/      Streamlit Cloud için küçültülmüş veri (<50 MB, git'e girer)
data/*.parquet    tam veri (git'e GİRMEZ — USB/Drive ile paylaşılır)
docs/validation/  P3 çıktıları (png + metrics.json)
docs/pitch/       P6
```

## 4. `app/query.py` API (P5 SADECE bunları kullanır)
```python
PRESETS: dict[str, tuple[float, float, float, float]]   # ad -> (lon_min, lat_min, lon_max, lat_max)
                                                        # "Hohes Venn", "Aachen/Eifel", "La Rioja (AR)"
data_info() -> dict
    # {"path", "is_mock", "has_harm", "start", "end", "n_rows", "satellites"} → is_mock ise uyarı göster
get_hotspots(geom, start=None, end=None, harmonized=False) -> pd.DataFrame
    # geom: PRESETS adı, bbox tuple ya da GeoJSON (Feature/Polygon — streamlit-folium çizimi direkt)
    # harmonized=True → sadece weight_harm > 0 satırlar (harita için)
monthly_matrix(df, mode="raw") -> pd.DataFrame
    # index=year, columns=1..12; mode="raw": satır sayısı (tüm uydular), mode="harm": Σ weight_harm
    # veri kapsamı dışı aylar NaN, kapsam içinde tespit yoksa 0; harmonize veri yoksa "harm" hep NaN
anomaly(matrix, year, month) -> dict
    # {"value", "mean", "std", "z", "rank", "n_years", "label"}; taban = aynı ayın diğer yılları
    # label: "çok yüksek" | "yüksek" | "normal" | "düşük" | "tespit yok" | "veri yok"
to_csv_bytes(df) -> bytes
MONTH_LABELS  # ["Oca", ..., "Ara"]
```
Veri kaynağı önceliği: `$HOTSPOTS_PATH` → `data/hotspots_harm.parquet` → `data/hotspots.parquet`
→ `data/deploy/…` → `data/mock/hotspots_mock.parquet`.

## 5. Çalıştırma
```bash
python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
python pipeline/ingest.py        # P1 → data/hotspots.parquet
python pipeline/harmonize.py     # P2 → data/hotspots_harm.parquet, monthly_grid.parquet, k_factors.csv
python pipeline/validate.py      # P3 → docs/validation/
streamlit run app/app.py         # P5
```
Tüm script'ler **repo kökünden** çalıştırılır; yollar köke göreli.

## 6. Kod kuralları
- Python 3.11+, pandas + pyarrow. Kod/değişken isimleri İngilizce, yorumlar Türkçe olabilir.
- Her pipeline script'i: `main()` + `if __name__ == "__main__":`, başta yol sabitleri.
- Sessiz hata yok: beklenmeyen sütun/değer → açık `ValueError`.
- Büyük veriyi tek seferde belleğe alma gerekiyorsa `pyarrow`/`usecols` kullan.
- Yeni paket gerekirse ekleme, kullanıcıya "Barış'a söyle" de.

## 7. Git kuralları
- Commit'ten önce: `git pull --rebase`
- 30–60 dk'da bir küçük commit; mesaj: `P1: archive+nrt birleştirme` gibi rol önekli.
- Sadece kendi dosyalarını `git add` et (`git add -A` YOK).
- Ajan (Claude) kodunu commit'ten önce oku ve en az bir kez çalıştır.
- Veri dosyası (`data/raw`, büyük parquet) asla commit'lenmez.

## 8. Takvim (Cumartesi 14 Kasım → Pazar 15 Kasım 2026)
| Saat | Kontrol noktası |
|---|---|
| 08:55 | P4: repo iskeleti push |
| 10:30 | Roller + şema + repo hazır (5 dk toplantı) |
| 11:00 | P4: mock parquet → P5 |
| 11:30 | P1: örnek dosya (1 bölge, 1 yıl) |
| 12:30 | P1: tam veri |
| 13:00 | Gerçek veri herkeste, mock uygulama ayakta |
| 16:30 | ✅ Ham takvim uçtan uca (P2 harmonize veri, P4 gerçek veri) |
| 19:00 | ✅ Harmonize MVP (P3 doğrulama → P6) |
| Pazar 09:15 | Jüri kriterleri gözden geçirme |
| Pazar 12:00 | ❄️ FEATURE FREEZE — sadece bug fix |
| Pazar 14:00 | Sunum hazır |
| Pazar 14:30 | 📤 TESLİM (son saat 15:00) |

**Takıldın mı? 15 dk'dan fazla uğraşma, söyle.** Claude: kullanıcı aynı hatada 15 dk'yı geçtiyse
bunu hatırlat ve "Barış'a yaz" öner.
