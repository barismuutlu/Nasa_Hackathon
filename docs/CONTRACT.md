# Veri & Arayüz Sözleşmesi v1.1

Sahibi: **P4 Barış**. Kod karşılığı: [`contract.py`](../contract.py) (sabitler + `validate_hotspots()`).
Değişiklik → önce P4. Her değişiklik en alttaki **Değişiklik günlüğü**ne yazılır.

Kaynaklar: FIRMS öznitelik tablosu (earthdata.nasa.gov → FIRMS → Active Fire Data Attributes).
⚠️ Gerçek CSV başlıkları henüz görülmedi → P1 ilk dosyada doğrular, fark varsa P4'e bildirir.

---

## 1. `data/hotspots.parquet` — kanonik şema

Bir satır = bir uydunun bir geçişte tespit ettiği bir **termal anomali pikseli** (hotspot).
Bir satır **doğrulanmış bir orman yangını olayı DEĞİLDİR** (bkz. §8 Terminoloji).

| # | Sütun | dtype | Zorunlu | FIRMS kaynağı | Not |
|---|---|---|---|---|---|
| 1 | `latitude` | float64 | ✅ | `latitude` | piksel merkezi (MODIS 1 km, VIIRS 375 m) |
| 2 | `longitude` | float64 | ✅ | `longitude` | |
| 3 | `acq_date` | datetime64[ns] | ✅ | `acq_date` | **UTC** tarih, saat 00:00 |
| 4 | `acq_time` | int16 | ✅ | `acq_time` | HHMM UTC (0–2359); baştaki sıfır kaybı sorun değil |
| 5 | `datetime_utc` | datetime64[ns, UTC] | ✅ | türetilir | `acq_date + HH:MM` |
| 6 | `year` | int16 | ✅ | türetilir | `acq_date` (UTC) yılı |
| 7 | `month` | int8 | ✅ | türetilir | 1–12 |
| 8 | `instrument` | category | ✅ | `instrument` / sütunlardan | `MODIS` \| `VIIRS` |
| 9 | `satellite` | category | ✅ | `satellite` | `Terra` \| `Aqua` \| `SNPP` \| `NOAA20` \| `NOAA21` (§3) |
| 10 | `confidence` | string | ✅ | `confidence` | **orijinal değer, olduğu gibi**: MODIS `"0"`–`"100"`, VIIRS `"l"`/`"n"`/`"h"` |
| 11 | `confidence_class` | category | ✅ | türetilir | `low` \| `nominal` \| `high` — MODIS: <30 / 30–79 / ≥80 (**proje kuralı**, FIRMS sayısal eşik vermiyor) |
| 12 | `version` | string | ✅ | `version` | ör. `6.1`, `6.1NRT`, `2.0NRT`; sahte veri: `MOCK` |
| 13 | `brightness` | float32 | ⬜ | MODIS `brightness` / VIIRS `bright_ti4` | K. **İki enstrüman arasında karşılaştırılamaz** (farklı kanal/çözünürlük) |
| 14 | `brightness_2` | float32 | ⬜ | MODIS `bright_t31` / VIIRS `bright_ti5` | K (FIRMS web servisi adı: Brightness_2) |
| 15 | `scan` | float32 | ⬜ | `scan` | piksel boyutu, km |
| 16 | `track` | float32 | ⬜ | `track` | piksel boyutu, km |
| 17 | `frp` | float32 | ⬜ | `frp` | MW |
| 18 | `daynight` | category | ⬜ | `daynight` | `D` \| `N` |
| 19 | `type` | Int8 | ⬜ | `type` (sadece archive) | 0 bitki yangını (varsayılan), 1 volkan, 2 statik kaynak, 3 deniz; NRT'de boş |
| 20 | `source` | category | ✅ | dosya adı | `archive` \| `nrt` |
| 21 | `region` | string | ✅ | `data/raw/<region>/` klasör adı | indirme alanı slug'ı (§5) |
| 22 | `weight_harm` | float32 | ⬜ | P2 | **ingest'te NaN**; P2 çıktısında dolu, ≥ 0 (§6) |

- **Zorunlu** = sütun var VE boş değer yok. **⬜** = sütun var ama boş olabilir.
- Sütun sırası tablodaki gibi. Ekstra sütun yok (gerekirse P4'e sor → sözleşmeye eklenir).
- **Açık karar — `sensor` sütunu:** şimdilik yok; `instrument` (sensör ailesi) + `satellite`
  (platform) her veri akışını tekil tanımlıyor. İbrahim'in yeni veri setleri gelince yeniden bakılacak.

## 2. Eksik değerler
- Sayısal → `NaN`; `type` → `<NA>`; metin → `<NA>` (boş string `""` YASAK).
- Zorunlu alanı (`latitude, longitude, acq_date, acq_time, satellite`) okunamayan satır **atılır**
  ve sayısı ingest özetinde yazılır. Başka hiçbir sebeple satır atılmaz.
- Bilinmeyen `satellite` kodu ya da beklenmeyen sütun yapısı → `ValueError` (sessiz atma yok).

## 3. Uydu / enstrüman adları
| FIRMS kodu | `satellite` | `instrument` | Veri başlangıcı (yaklaşık) |
|---|---|---|---|
| `Terra`, `T` | Terra | MODIS | 2000-11 |
| `Aqua`, `A` | Aqua | MODIS | 2002-07 |
| `N` | SNPP | VIIRS | 2012-01 — **2026-11-02'de veri akışı durdu** (FIRMS duyurusu) |
| `N20`, `1` | NOAA20 | VIIRS | 2018-04 |
| `N21`, `2` | NOAA21 | VIIRS | 2024-01 |

Gerçek ilk/son tarihleri P1 veriden çıkarır → `data/satellite_coverage.csv` (§7.1).
Enstrüman tespiti dosya adından değil sütunlardan: `brightness` → MODIS, `bright_ti4` → VIIRS.

## 4. Tekrarlar ve archive/NRT çakışması
**4a. Birebir tekrar** (aynı dosya ya da aynı kaynaktan iki kez indirme):
anahtar `(satellite, datetime_utc, round(latitude,4), round(longitude,4))` → ilki kalır.
- Farklı uydu **veya** farklı zaman = farklı gözlem, ASLA birleştirilmez.
- Aynı geçişte komşu pikseller farklı koordinattadır → ayrı satır kalır (bunlar meşru gözlemlerdir).

**4b. archive ↔ NRT**: NRT ve archive aynı tespiti **biraz farklı konumla** verir
(NRT hızlı işlenir), bu yüzden nokta-nokta eşleştirme güvenilmez → çift sayım riski.
Kural: her `satellite` için `cutoff = archive içindeki en son acq_date`;
o uydunun `acq_date ≤ cutoff` olan **tüm NRT satırları atılır**, sonrası kalır.
P1 her uydu için cutoff'u ve atılan NRT satır sayısını özete yazar.

## 5. Bölge (region) adları
- Kaynak: **FIRMS ülke dosyaları**. Ülkeler çakışmaz → aynı tespit iki bölgede olmaz.
- Slug: ülke adı, küçük harf, ascii, `^[a-z0-9_]+$`. Klasör adı = değer:
  `data/raw/germany/*.csv` → `region="germany"`.
- Gerekli ülkeler (`contract.REGIONS`):
  - `germany` — Aachen/Eifel'in Alman tarafı
  - `belgium` — **Hohes Venn'in büyük kısmı Belçika'da.** Almanya dosyası tek başına Venn
    tespitlerini (Nisan 2011) içermez → Belçika dosyası şart.
  - `argentina` — La Rioja + P2 eğitimi
- `region` uygulamada filtre değildir: uygulama **koordinatla** filtreler (`query.PRESETS`),
  bu yüzden "Aachen/Eifel" kutusu Almanya + Belçika tespitlerini birlikte gösterir.

## 6. `weight_harm`
- **Anlam (sözleşme):** herhangi bir satır kümesi için `Σ weight_harm` = o kümenin
  harmonize (MODIS-eşdeğeri) tespit sayısı **tahmini**. Değerler ≥ 0.
- **Ingest (P1):** `NaN` — "henüz harmonize edilmedi". (1.0 değil: 1.0 olsaydı harmonize mod
  sessizce ham sayıyı gösterirdi.)
- **Harmonize (P2):** hiç NaN yok. **Yöntemi P2 belirler** ve `pipeline/harmonize.py` başında
  yazar. Başlangıç önerisi (Yöntem A): MODIS satırları VIIRS döneminden önce 1, sonra 0;
  VIIRS satırları `k / aktif_VIIRS_uydu_sayısı`, `k = MODIS / VIIRS` (Arjantin 2012–2021).
  Aktif uydu sayısı başlangıç **ve bitiş** tarihlerine göre (SNPP 2026-11-02'de bitti).
- Yöntem A **doğrulanmamış bir hipotezdir**; P3 metriklerinden önce "doğru" diye sunulmaz.

## 7. Pipeline arayüzleri
Tüm script'ler repo kökünden: `python pipeline/<ad>.py`. Hepsi `main()` + `if __name__ == "__main__"`.

### 7.1 `pipeline/ingest.py` (P1)
| | |
|---|---|
| Girdi | `data/raw/<region>/*.csv` — FIRMS ülke dosyaları: archive (`fire_archive_*`, ülke-yıl dosyaları), NRT (`fire_nrt_*`) |
| Çıktı | `data/hotspots.parquet` — §1 şeması, `validate_hotspots(df, "ingest")` geçer |
| Çıktı | `data/satellite_coverage.csv` — `satellite, source, first_date, last_date, n_rows, nrt_cutoff, n_nrt_dropped` |
| stdout | uydu × yıl satır sayısı, atılan satırlar (sebep bazında) |

### 7.2 `pipeline/harmonize.py` (P2)
| | |
|---|---|
| Girdi | `data/hotspots.parquet`, `data/satellite_coverage.csv` |
| Çıktı | `data/hotspots_harm.parquet` — §1 şeması, `validate_hotspots(df, "harm")` geçer |
| Çıktı | `data/monthly_grid.parquet` — aşağıda |
| Çıktı | `data/k_factors.csv` — en az `k, n_modis, n_viirs, fallback` + P2'nin seçtiği tabaka sütunları |

`monthly_grid.parquet`:
| Sütun | dtype | Not |
|---|---|---|
| `cell_lat`, `cell_lon` | float64 | 0.25° hücre merkezi: `floor(x/0.25)*0.25 + 0.125` |
| `year` | int16 | |
| `month` | int8 | |
| `region` | string | |
| `n_terra`, `n_aqua`, `n_snpp`, `n_noaa20`, `n_noaa21` | int32 | ham sayı, uydu başına |
| `n_modis`, `n_viirs` | int32 | toplamlar |
| `n_harm` | float64 | `Σ weight_harm` |
Sadece en az bir tespiti olan hücre-aylar yazılır (eksik = 0).

### 7.3 `pipeline/validate.py` (P3)
| | |
|---|---|
| Girdi | `data/monthly_grid.parquet`, `data/hotspots_harm.parquet`, `data/k_factors.csv` |
| Çıktı | `docs/validation/metrics.json` — `[{"method","region","split","scale","r2","bias","bias_pct","n"}]` |
| Çıktı | `docs/validation/*.png` — `pred_vs_true.png`, `annual_raw_vs_harm.png`, `venn_check.png` |
| Bölünme | eğitim 2012–2021, test 2022–2024 |

### 7.4 `app/query.py` (P4) — P5 sadece bunu kullanır
```python
PRESETS: dict[str, tuple[float, float, float, float]]
    # görüntüleme kutuları: "Hohes Venn", "Aachen/Eifel", "La Rioja (AR)"
MONTH_LABELS: list[str]                   # ["Oca", …, "Ara"]

data_info() -> dict
    # {"path": str, "is_mock": bool, "has_harm": bool, "start": Timestamp, "end": Timestamp,
    #  "n_rows": int, "satellites": list[str], "contract": "1.1"}

get_hotspots(geom, start=None, end=None, harmonized=False) -> pd.DataFrame
    # geom: PRESETS adı | (lon_min, lat_min, lon_max, lat_max) | GeoJSON Feature/Polygon/MultiPolygon
    # start/end: tarih benzeri, dahil, UTC; harmonized=True → sadece weight_harm > 0
    # dönüş: §1 sütunları (aynı dtype'lar), 0 satır olabilir

monthly_matrix(df, mode="raw") -> pd.DataFrame
    # index "year" (int, veri kapsamındaki tüm yıllar), columns "month" 1..12, float64
    # raw: satır sayısı (tüm uydular) | harm: Σ weight_harm
    # kapsam dışı ay → NaN; kapsam içinde tespit yok → 0; harmonize veri yoksa harm → tamamen NaN

anomaly(matrix, year, month) -> dict
    # {"value": float, "mean": float, "std": float, "z": float, "rank": int|None,
    #  "n_years": int, "label": str}
    # taban = aynı takvim ayının diğer yılları; rank 1 = en yüksek
    # label: "çok yüksek" (z>2) | "yüksek" (z>1) | "normal" | "düşük" (z<-1) | "tespit yok" | "veri yok"

to_csv_bytes(df) -> bytes                 # UTF-8; index adı varsa index de yazılır
```
Veri dosyası önceliği: `$HOTSPOTS_PATH` → `data/hotspots_harm.parquet` → `data/hotspots.parquet`
→ `data/deploy/hotspots_deploy.parquet` → `data/mock/hotspots_mock.parquet`.

## 8. Terminoloji (uygulama, slayt, proje sayfası)
| Doğru | Yanlış |
|---|---|
| "aktif yangın tespiti", "termal anomali", "hotspot" | "yangın" (tek satır için) |
| "Hohes Venn'de bilinen yangın olaylarıyla **örtüşen** tespit artışı" | "uygulama yangını tespit etti" |
| "harmonize (MODIS-eşdeğeri) tahmin" | "gerçek yangın sayısı" |
| "k katsayısı: Arjantin'de kalibre edildi, test 2022–2024: R²=…" | "doğrulanmış dönüşüm katsayısı" |

Anomali etiketleri **tespit sayısı** anomalisidir, yangın olayı sınıflandırması değildir.

## 9. Sahte veri
`data/mock/hotspots_mock.parquet`, `data/mock/make_mock.py` ile üretilir. Her satırda
`version = "MOCK"` → CSV dışa aktarımında da sentetik olduğu görünür. `data_info()["is_mock"]`
True ise uygulama "SENTETİK TEST VERİSİ" uyarısı gösterir. Bilimsel değeri yoktur.

## Değişiklik günlüğü
| Sürüm | Değişiklik | Etkilenen |
|---|---|---|
| 1.0 | İlk şema (CLAUDE.md §3) | herkes |
| 1.1 | bölgeler ülke dosyalarına çevrildi (`germany`, `belgium`, `argentina`); `sensor` açık karar olarak işaretlendi; `lat/lon` → `latitude/longitude`; `bright` → `brightness`; `brightness_2` eklendi; `confidence` artık **orijinal değer** (eski `confidence_raw`), sınıf → `confidence_class`; `fire_type` → `type`; yeni: `datetime_utc`, `version`, `region`; archive/NRT kuralı uydu bazlı tarih kesimine çevrildi; `satellite_coverage.csv` eklendi; `weight_harm` yöntemi P2'ye devredildi; `contract.py` doğrulayıcı | P1, P2, P3, P5 |
