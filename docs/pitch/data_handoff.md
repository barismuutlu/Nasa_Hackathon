# P6 veri teslim durumu — güncel DL_FIRE ve tarihsel arşiv

Cloud kaynağı: `P6_ibrahim.patch`, referans `8d5894c`, 14 Kasım 2026, sözleşme v1.2. Mevcut yerel sözleşme v1.3'tür; DL_FIRE ve ülke-yıl girdilerini dışlama kuralları değişmemiştir.

Tarihsel indirme, boyut, SHA-256, ZIP ve Python kontrol sonuçları önceki cloud oturumunun raporudur. CSV ve ZIP dosyaları patch'in içinde değildir; bu Windows çalışma alanında aynı kontroller yeniden çalıştırılmadı. Güncel P1/P4/P5 teslimi aşağıda ayrı kaydedilmiştir. P6 yerel durumu [test_notes.md](test_notes.md) içindedir.

**Önceki v1.1 ülke-yıl teslimi güncel pipeline girdisi değildir.**
`docs/CONTRACT.md` v1.2 §3 ve §5, ülke-yıl dosyalarını kapsam dışında bırakır.
Önceki 144 CSV ve ZIP korunmuştur; bu not bunları tarihsel indirme arşivi olarak
kaydeder. Kaynak `data_download_manifest.csv` de aynı tarihsel arşivi tanımlar.

## Güncel teslim — P1 tarafında tamamlandı

Kaynak: Süleyman'ın `26fa38d` referanslı mesajı. P1 makinesinde `data/raw/` altında yalnız şu DL_FIRE ZIP girdilerinin bulunduğu ve ülke-yıl CSV'si olmadığı bildirildi:

| Alan | P1'de bildirilen girdi |
|---|---|
| argentina | `data/raw/argentina/Argentina-20261114T101801Z-1-001.zip` |
| aachen_eifel | `data/raw/aachen_eifel/Aachen-Eifel-20261114T101746Z-1-001.zip` |

Dört kaynak, archive + NRT; Aachen/Eifel indirme kutusu `(5.96, 50.44, 6.44, 50.83)`. Çıktı `data/hotspots.parquet`: 7.082.663 satır, 2000-11-01 → 2026-11-13. Barış'ın Drive'dan alıp kontrol ettiği, Yusuf'un gerçek veriyle uygulama testini yaptığı bildirildi. **P1 teslimi tamamdır; bu durum P6 makinesinde tam verinin bulunduğu veya yeniden test edildiği anlamına gelmez.**

P1 tam harmonize çıktısında Hohes Venn Nisan 2011=17,0 ve Ağustos 2026=169,2 MODIS-eşdeğeri; Nisan kartı 2001–2026'daki 26 Nisan içinde 1., diğer 25 Nisan ortalaması ≈0,59 ve oran ≈29×. Ayrıntılar [pitch_facts.md](pitch_facts.md) içinde; aktif tespitlerin Ağustos tarihleri 14–17 olarak teyit edildi.

## Tarihsel arşivi ingest girdisinden ayrı tut

Tarihsel ülke-yıl ZIP'i ve açılmış CSV'leri **`data/raw/` dışında**, örneğin `data/archive/` altında tut; git'e ekleme. Bu belge kapsamında hiçbir ham dosya taşınmadı veya silinmedi. Eski manifest ve paket kaydındaki `data/raw/...` yolları cloud'da bildirilen tarihsel konumlardır; güncel yerleştirme talimatı değildir.

- `data/raw/` kökündeki ZIP (ör. `firms_country_archives_2000_2025.zip`) ingest'in bölge-klasörü kontrolünde açık hataya yol açar.
- `data/raw/belgium/` gibi bir alt klasöre açılmış ülke-yıl CSV'leri ise taranır; uyarı basılması bunları otomatik dışlamaz. “Uygulama zaten reddeder” varsayımıyla burada tutulmamalıdır.
- Geçerli DL_FIRE ZIP'leri yukarıdaki `argentina` ve `aachen_eifel` bölge klasörlerinde kalır. Bu davranış `pipeline/ingest.py` kaynak kodundan okundu; ingest bu makinede çalıştırılmadı.

## Geçerli girdi

- Kaynak: FIRMS DL_FIRE; `fire_archive_*` ve `fire_nrt_*` CSV çıktıları.
- Dört veri akışı: MODIS, VIIRS S-NPP, NOAA-20, NOAA-21.
- `data/raw/argentina/`: Arjantin ülke seçimi.
- `data/raw/aachen_eifel/`: bbox `5.96, 50.44, 6.44, 50.83`.
- Dönem: Kasım 2000–günümüz; her uydu için mevcut dönem.
- NOAA-21 başlangıcı: 2023-03-01; S-NPP bitişi: 2026-11-02.
- DL_FIRE VIIRS başlıkları da `brightness/bright_t31` olabilir;
  enstrüman sütun adından değil uydu kodundan belirlenir.

Takımın Drive arşivi bu biçimdedir ve P1/P4 teslimi yukarıdaki bildirime göre tamamlanmıştır. P6'nın bu Windows çalışma alanında tam parquet aktarımı ve runtime tekrarı henüz yapılmadı. Süleyman'ın kanonik parquet üzerinden teyit ettiği sayılar kaynak atfıyla kullanılır; burada yerel parquet kontrolü yapıldığı iddia edilmez.

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

Cloud'da bildirilen eski konum `data/raw/firms_country_archives_2000_2025.zip`: 145.340.525 bayt. Güncel saklama önerisi `data/archive/firms_country_archives_2000_2025.zip`; ZIP ve içindeki ülke-yıl CSV'leri `data/raw/` altında tutulmaz.
ZIP bütünlük kontrolü geçti. SHA-256: `data_transfer_package.json`.
Paket v1.1 arşividir; güncel v1.3 girdi klasörlerine açılmamalıdır. ZIP içindeki eski
yerleştirme yönergelerinin yerine bu not geçerlidir.
Bu tarihsel paket için cloud raporunda Drive/USB aktarımı yapılmadığı yazılıydı; bu ifade güncel DL_FIRE tesliminin eksik olduğu anlamına gelmez. Hiçbir raw CSV veya ZIP bu belge değişikliğiyle git'e eklenmedi.

## Cloud oturumunun kapanış durumu / aktarılacak bilgi

- Ortam kuruldu: Python 3.12.14, sabit paket sürümleri.
- Smoke test: 7 geçti, 6 atlandı, 0 hata; query kontrolleri sentetik veride.
- Ortam raporu: `environment_check.md`.
- Cloud kapanışında harmonize sayı bekleniyordu. Sonraki P1 tesliminde Nisan 17,0; Ağustos 169,2 MODIS-eşdeğeri olarak bildirildi; ham Ağustos 105 MODIS + 1.794 VIIRS.
- Cloud kapanışında bekleyen DL_FIRE/parquet teslimi P1/P4 tarafında sonradan tamamlandı; P6 yerel aktarım ve runtime kontrolü ayrı, halen bekliyor.
- `2026 Judging Criteria.docx` çalışma alanında bulunamadı; taşıma yapılmadı.
- Kod ve sözleşme değiştirilmedi; P6 değişiklikleri `docs/pitch/` altındadır.
