# P6 veri indirme durumu — cloud kaydı ve sözleşme v1.3

Cloud kaynağı: `P6_ibrahim.patch`, referans `8d5894c`, 14 Kasım 2026, sözleşme v1.2. Mevcut yerel sözleşme v1.3'tür; DL_FIRE ve ülke-yıl girdilerini dışlama kuralları değişmemiştir.

Bu belgedeki indirme, boyut, SHA-256, ZIP ve Python kontrol sonuçları önceki cloud oturumunun raporudur. CSV ve ZIP dosyaları patch'in içinde değildir; bu Windows çalışma alanında aynı kontroller yeniden çalıştırılmadı. Aşağıdaki “çalışma alanı” ifadeleri cloud oturumunu anlatır. Yerel durum [test_notes.md](test_notes.md) içinde ayrı tutulur.

**Önceki v1.1 ülke-yıl teslimi güncel pipeline girdisi değildir.**
`docs/CONTRACT.md` v1.2 §3 ve §5, ülke-yıl dosyalarını kapsam dışında bırakır.
Önceki 144 CSV ve ZIP korunmuştur; bu not bunları tarihsel indirme arşivi olarak
kaydeder. Kaynak `data_download_manifest.csv` de aynı tarihsel arşivi tanımlar.

## Geçerli girdi

- Kaynak: FIRMS DL_FIRE; `fire_archive_*` ve `fire_nrt_*` CSV çıktıları.
- Dört veri akışı: MODIS, VIIRS S-NPP, NOAA-20, NOAA-21.
- `data/raw/argentina/`: Arjantin ülke seçimi.
- `data/raw/aachen_eifel/`: bbox `5.96, 50.44, 6.44, 50.83`.
- Dönem: Kasım 2000–günümüz; her uydu için mevcut dönem.
- NOAA-21 başlangıcı: 2023-03-01; S-NPP bitişi: 2026-11-02.
- DL_FIRE VIIRS başlıkları da `brightness/bright_t31` olabilir;
  enstrüman sütun adından değil uydu kodundan belirlenir.

Takımın Drive arşivi bu biçimdedir; bu çalışma alanına henüz aktarılmadı.
Süleyman, kanonik `data/hotspots.parquet` üzerinden Nisan 2011 ve Ağustos 2026
pitch sayılarını doğruladı. Ekibin ilettiği gerçek sonuçlar `pitch_facts.md`
içindedir; burada yerel parquet kontrolü yapıldığı iddia edilmez.
Mevcut ülke-yıl CSV dosyalarının yolu aynı `data/raw/` ağacı altında olsa da
bunlar v1.2 girdisi olarak tüketilmemelidir. DL_FIRE arşivi yerleştirilmeden
önce eski ülke-yıl dosyaları ayrı bir çalışma arşivine alınmalıdır.

## Tarihsel ülke-yıl indirmesi (v1.1)

| Ülke | Ürün | CSV | Ham satır | İlk tespit | Son tespit |
|---|---|---:|---:|---|---|
| argentina | modis | 26 | 1,712,416 | 2000-11-01 | 2025-12-31 |
| argentina | viirs-jpss1 | 8 | 1,728,797 | 2018-04-01 | 2025-12-31 |
| argentina | viirs-snpp | 14 | 2,889,092 | 2012-01-20 | 2025-12-31 |
| belgium | modis | 26 | 13,140 | 2000-11-02 | 2025-12-30 |
| belgium | viirs-jpss1 | 8 | 35,357 | 2018-04-02 | 2025-12-31 |
| belgium | viirs-snpp | 14 | 62,163 | 2012-01-22 | 2025-12-31 |
| germany | modis | 26 | 55,526 | 2000-11-02 | 2025-12-30 |
| germany | viirs-jpss1 | 8 | 147,471 | 2018-04-01 | 2025-12-31 |
| germany | viirs-snpp | 14 | 249,977 | 2012-01-20 | 2025-12-31 |

144 CSV, 6.893.939 ham satır, 554.614.725 bayt. Her ülke için 48 CSV.
MODIS 2000–2025, S-NPP 2012–2025, NOAA-20 2018–2025.
2026 ve NOAA-21 içermez. Satır sayıları benzersiz tespit veya yangın olayı sayısı değildir.

Kaynak: https://firms.modaps.eosdis.nasa.gov/data/country/yearly_summary_files.txt

Boyutlar NASA listesiyle eşleşti; SHA-256 değerleri yerel olarak üretildi.
CSV kontrolü yeni Python 3.12 ortamında yeniden çalıştırıldı; alan sayısı bozuk
satır veya kontrol edilen temel alanlarda boş değer yok.

## İlk indirilen CSV — yalnız tarihsel başlık örneği

`head -3 data/raw/belgium/modis_2011_Belgium.csv`:

```csv
latitude,longitude,brightness,scan,track,acq_date,acq_time,satellite,instrument,confidence,version,bright_t31,frp,daynight,type
51.1708,3.8039,308,1,1,2011-01-01,2131,Terra,MODIS,73,6.2,274.8,13.6,N,0
51.1698,3.8165,313.9,1,1,2011-01-04,1051,Terra,MODIS,52,6.2,272.7,17.9,D,2
```

Ülke-yıl VIIRS CSV başlığı `bright_ti4/bright_ti5` kullanır. Bu fark, DL_FIRE
başlıkları için varsayım yapılamayacağını gösterir. MODIS ham `version`
değerleri `6.2`, `6.03`, `61.03`; VIIRS `2`. Veriler değiştirilmedi.

Eski Belçika CSV içinde, enlem 50.45–50.60 ve boylam 5.95–6.25 kutusunda,
25–26 Nisan 2011 için 17 ham MODIS tespit satırı bulundu. Bu ön kontrol,
güncel DL_FIRE pipeline kontrolü veya bilimsel doğrulama değildir.

## Tarihsel aktarım paketi

`data/raw/firms_country_archives_2000_2025.zip`: 145.340.525 bayt.
ZIP bütünlük kontrolü geçti. SHA-256: `data_transfer_package.json`.
Paket v1.1 arşividir; güncel v1.3 girdi klasörlerine açılmamalıdır. ZIP içindeki eski
yerleştirme yönergelerinin yerine bu not geçerlidir.
Drive/USB aktarımı yapılmadı; hiçbir raw CSV veya ZIP git içine eklenmedi.

## Cloud oturumunun kapanış durumu / aktarılacak bilgi

- Ortam kuruldu: Python 3.12.14, sabit paket sürümleri.
- Smoke test: 7 geçti, 6 atlandı, 0 hata; query kontrolleri sentetik veride.
- Ortam raporu: `environment_check.md`.
- P1'in kanonik parquet üzerinden doğruladığı Ağustos 2026 sayıları pitch'e işlendi:
  105 MODIS, 1.794 VIIRS. Harmonize sayı `[TBD — Bahtiyar]`.
- Yerel DL_FIRE/parquet aktarımı ve tam kapsam kontrolleri halen bekleniyor.
- `2026 Judging Criteria.docx` çalışma alanında bulunamadı; taşıma yapılmadı.
- Kod ve sözleşme değiştirilmedi; P6 değişiklikleri `docs/pitch/` altındadır.
