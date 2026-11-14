# Doğrulama özeti

Girdi: `data/hotspots_harm.parquet`  
monthly_grid.parquet yıllık n_modis/n_viirs ile tutarlı ✓  
k_factors.csv: 49 satır. P2 teyidi: k sadece Arjantin 2012–2021 VIIRS'ten, Terra-only ağırlığı 2003–2011'den → test yılları (2022–2024) k'ya girmedi.

## Test (hücre-ay, harmonize vs ham VIIRS)

test = 2022–2024; test_2022 = NOAA-21 öncesi; test_2023-2024 = NOAA-21 aktif (eğitimde olmayan uydu); transfer_2012-2026 = Aachen/Eifel'in tüm VIIRS yılları (bölge eğitime hiç girmedi).

| bölge | dönem | ölçek | yöntem | R² | bias (tespit/hücre-ay) | bias % | n |
|---|---|---|---|---|---|---|---|
| aachen_eifel | test | 0.25deg | harm | 0.49 | -0.01 | -1.6 | 14 |
| aachen_eifel | test | 0.25deg | raw_viirs | -112.83 | 4.21 | +842.9 | 14 |
| aachen_eifel | test | 1deg | harm | 0.57 | -0.01 | -1.6 | 12 |
| aachen_eifel | test | 1deg | raw_viirs | -119.27 | 4.92 | +842.9 | 12 |
| aachen_eifel | test_2022 | 0.25deg | harm | -0.40 | -0.50 | -66.0 | 4 |
| aachen_eifel | test_2022 | 0.25deg | raw_viirs | -1.55 | 0.75 | +100.0 | 4 |
| aachen_eifel | test_2022 | 1deg | harm | -0.85 | -0.66 | -66.0 | 3 |
| aachen_eifel | test_2022 | 1deg | raw_viirs | -4.50 | 1.00 | +100.0 | 3 |
| aachen_eifel | test_2023-2024 | 0.25deg | harm | 0.76 | 0.19 | +46.8 | 10 |
| aachen_eifel | test_2023-2024 | 0.25deg | raw_viirs | -154.00 | 5.60 | +1400.0 | 10 |
| aachen_eifel | test_2023-2024 | 1deg | harm | 0.88 | 0.21 | +46.8 | 9 |
| aachen_eifel | test_2023-2024 | 1deg | raw_viirs | -157.35 | 6.22 | +1400.0 | 9 |
| aachen_eifel | transfer_2012-2026 | 0.25deg | harm | 0.63 | 0.86 | +35.0 | 68 |
| aachen_eifel | transfer_2012-2026 | 0.25deg | raw_viirs | -258.09 | 30.90 | +1250.6 | 68 |
| aachen_eifel | transfer_2012-2026 | 1deg | harm | 0.79 | 1.09 | +35.0 | 54 |
| aachen_eifel | transfer_2012-2026 | 1deg | raw_viirs | -209.94 | 38.91 | +1250.6 | 54 |
| argentina | test | 0.25deg | harm | 0.64 | 0.23 | +6.7 | 51250 |
| argentina | test | 0.25deg | raw_viirs | -87.01 | 26.88 | +785.9 | 51250 |
| argentina | test | 1deg | harm | 0.79 | 1.37 | +6.7 | 8616 |
| argentina | test | 1deg | raw_viirs | -74.82 | 159.88 | +785.9 | 8616 |
| argentina | test_2022 | 0.25deg | harm | 0.51 | 0.81 | +18.4 | 17633 |
| argentina | test_2022 | 0.25deg | raw_viirs | -85.37 | 31.07 | +706.7 | 17633 |
| argentina | test_2022 | 1deg | harm | 0.71 | 5.02 | +18.4 | 2834 |
| argentina | test_2022 | 1deg | raw_viirs | -71.96 | 193.31 | +706.7 | 2834 |
| argentina | test_2023-2024 | 0.25deg | harm | 0.85 | -0.07 | -2.5 | 33617 |
| argentina | test_2023-2024 | 0.25deg | raw_viirs | -90.31 | 24.68 | +848.7 | 33617 |
| argentina | test_2023-2024 | 1deg | harm | 0.93 | -0.42 | -2.5 | 5782 |
| argentina | test_2023-2024 | 1deg | raw_viirs | -80.45 | 143.49 | +848.7 | 5782 |

## Test yılları tek tek (Σ harmonize VIIRS / Σ MODIS; 1.00 = mükemmel)

| bölge | yıl | Σ MODIS | Σ harm | oran |
|---|---|---|---|---|
| aachen_eifel | 2022 | 3 | 1.0 | 0.34 |
| aachen_eifel | 2023 | 4 | 5.4 | 1.35 |
| aachen_eifel | 2024 | 0 | 0.5 | — |
| argentina | 2022 | 77522 | 91757.8 | 1.18 |
| argentina | 2023 | 47911 | 48672.8 | 1.02 |
| argentina | 2024 | 49843 | 46627.3 | 0.94 |

### Arjantin 2022 aylık (S-NPP Tem–Ağu, Aqua Mar–Nis kesintileri)

| ay | Σ MODIS | Σ harm | oran | Terra | Aqua | SNPP | NOAA20 |
|---|---|---|---|---|---|---|---|
| Ocak | 14485 | 17352.1 | 1.20 | 5907 | 8578 | 62411 | 59091 |
| Şubat | 10260 | 11974.3 | 1.17 | 4482 | 5778 | 43248 | 40303 |
| Mart | 1778 | 1750.7 | 0.98 | 896 | 882 | 6817 | 6708 |
| Nisan | 831 | 1070.8 | 1.29 | 421 | 410 | 4370 | 4310 |
| Mayıs | 1280 | 1256.9 | 0.98 | 397 | 883 | 4923 | 5073 |
| Haziran | 1918 | 2143.5 | 1.12 | 336 | 1582 | 6881 | 7382 |
| Temmuz | 4076 | 3930.7 | 0.96 | 959 | 3117 | 9556 | 13295 |
| Ağustos | 11050 | 12034.6 | 1.09 | 3044 | 8006 | 34624 | 39462 |
| Eylül | 13121 | 13476.2 | 1.03 | 4345 | 8776 | 46795 | 45763 |
| Ekim | 6478 | 8441.3 | 1.30 | 2006 | 4472 | 28635 | 29269 |
| Kasım | 7981 | 12666.9 | 1.59 | 3118 | 4863 | 44476 | 42067 |
| Aralık | 4264 | 5659.7 | 1.33 | 1982 | 2282 | 20178 | 19717 |

## 2022 sapması — ham veriden tanı (Arjantin)

oran = MODIS / (aktif VIIRS uydusu başına VIIRS). Harmonizasyondan bağımsız. Eğitim yılları aralığı 0.280–0.326 (medyan 0.299).

| yıl | MODIS | VIIRS/uydu | oran | oran / eğitim medyanı | Aqua/Terra |
|---|---|---|---|---|---|
| 2012 | 61885 | 189774 | 0.326 | 1.09 | 1.73 |
| 2013 | 66553 | 237549 | 0.280 | 0.94 | 1.67 |
| 2014 | 36817 | 126344 | 0.291 | 0.97 | 1.48 |
| 2015 | 45140 | 151064 | 0.299 | 1.00 | 1.75 |
| 2016 | 55414 | 181412 | 0.305 | 1.02 | 1.84 |
| 2017 | 60301 | 201660 | 0.299 | 1.00 | 1.64 |
| 2018 | 55410 | 183612 | 0.302 | 1.01 | 1.73 |
| 2019 | 50388 | 161172 | 0.313 | 1.05 | 1.75 |
| 2020 | 124103 | 441532 | 0.281 | 0.94 | 1.87 |
| 2021 | 56876 | 198512 | 0.287 | 0.96 | 1.74 |
| 2022 (test) | 77522 | 312677 | 0.248 | 0.83 | 1.78 |
| 2023 (test) | 47911 | 167013 | 0.287 | 0.96 | 1.60 |
| 2024 (test) | 49843 | 155388 | 0.321 | 1.07 | 2.06 |

2022 aylık oran / aynı ayın eğitim medyanı (< 1 → MODIS beklenenden az): Oca 0.76, Şub 0.87, Mar 1.06, Nis 0.77, May 0.93, Haz 0.92, Tem 1.18, Ağu 0.91, Eyl 0.92, Eki 0.79, Kas 0.64, Ara 0.76

## Hohes Venn (kutu lon 5.95–6.25, lat 50.45–50.60)

'Görünüyor' = değer > 0 ve aynı ayın diğer yıllar ortalamasının ≥ 3 katı.

| seri | ay | sonuç | görünüyor |
|---|---|---|---|
| raw | 2011-04 | 17 tespit — 26 yılın en yüksek Nisan ayı; aynı ayın diğer yıllardaki ortalamasının (≈2.6) 6 katı, diğer yılların en fazlası 12 | evet |
| raw | 2026-08 | 1899 tespit — 26 yılın en yüksek Ağustos ayı; aynı ayın diğer yıllardaki ortalamasının (≈0.1) 23.738 katı, diğer yılların en fazlası 2 | evet |
| modis | 2011-04 | 17 MODIS tespiti — 26 yılın en yüksek Nisan ayı; aynı ayın diğer yıllardaki ortalamasının (≈0.6) 27 katı, diğer yılların en fazlası 3 | evet |
| modis | 2026-08 | 105 MODIS tespiti — 26 yılın en yüksek Ağustos ayı; aynı ayın diğer yıllardaki ortalamasının (≈0.1) 1.312 katı, diğer yılların en fazlası 2 | evet |
| harm | 2011-04 | 17 MODIS-eşdeğeri tespit — 26 yılın en yüksek Nisan ayı; aynı ayın diğer yıllardaki ortalamasının (≈0.6) 29 katı, diğer yılların en fazlası 3 | evet |
| harm | 2026-08 | 169 MODIS-eşdeğeri tespit — 26 yılın en yüksek Ağustos ayı; aynı ayın diğer yıllardaki ortalamasının (≈0.1) 2.115 katı, diğer yılların en fazlası 2 | evet |

## Sunum için 3 cümle (P6)

1. Arjantin'de (eğitim bölgesi), eğitimde kullanılmayan 2022–2024 yıllarında harmonize VIIRS tahmini MODIS tespit sayısını 1° hücre-ay ölçeğinde R²=0.79 ile, toplamda +6.7% sapmayla tahmin ediyor.
   Eğitimde hiç olmayan NOAA-21'in de aktif olduğu 2023–2024'te: R²=0.93, toplam sapma -2.5% (2022, NOAA-21 öncesi: R²=0.71, +18.4%).
2. Aynı katsayılar Aachen/Eifel'e (transfer, 2012–2026) taşındığında R²=0.79, toplam sapma +35.0% (n=54 hücre-ay); bu R² büyük ölçüde tek olaydan (Ağustos 2026): o ay hariç R²=0.37, sapma -4.3%.
3. Hohes Venn'de bilinen yangın olaylarıyla örtüşen tespit artışı Nisan 2011 ve Ağustos 2026'da harmonize takvimde görünüyor: Nisan 2011 → 17 MODIS-eşdeğeri tespit — 26 yılın en yüksek Nisan ayı; aynı ayın diğer yıllardaki ortalamasının (≈0.6) 29 katı, diğer yılların en fazlası 3; Ağustos 2026 → 169 MODIS-eşdeğeri tespit — 26 yılın en yüksek Ağustos ayı; aynı ayın diğer yıllardaki ortalamasının (≈0.1) 2.115 katı, diğer yılların en fazlası 2.

## Sınırlamalar ve gelecek çalışma

- **2022 (test) fazla tahmin:** Arjantin'de Σharm/ΣMODIS = 1.18. Fazlalık yangın sezonunda (Oca 1.20, Şub 1.17, Nis 1.29, Eki 1.30, Kas 1.59, Ara 1.33); kesinti ayları dahil diğer aylar 1'e yakın (Mar 0.98, May 0.98, Haz 1.12, Tem 0.96, Ağu 1.09, Eyl 1.03). Ham veride de 2022'de MODIS/VIIRS oranı eğitim aralığının dışında (yukarıdaki tanı tablosu) → S-NPP/Aqua kesintisi ya da kalıcı yörünge kayması ile açıklanmıyor (2023–2024 normale dönüyor).
- **Aachen/Eifel Ağustos 2026 (bölge aktarımı, tek olay, n küçük):** harm/MODIS = 1.61 (169 / 105). Fallback'ten değil (P2: 40–50 bandının k'sıyla bile +%50); olayın örtük k'sı 0.176, eğitimdeki tüm k'lar ≥ 0.20.
- **Transfer R² tek olaydan etkileniyor:** Aachen/Eifel 1° R²=0.79 (n=54, bias +35.0%); 2026-08 hariç R²=0.37, bias -4.3% (n=52). Yani olağan dönemde toplam seviye tutuyor, hücre-ay deseni zayıf; büyük olayda fazla tahmin.
- **Yorum (hipotez, doğrulanmadı):** k yangın büyüklüğüne bağlı — tek büyük yangın cephesinde VIIRS (375 m) MODIS'e (1 km) göre orantısız çok piksel sayıyor; k sadece enlem bandı × mevsim × uyduya göre katmanlı olduğu için bunu yakalayamıyor.
- **Gelecek çalışma:** k'yı yangın büyüklüğüne (aynı gün komşu tespit kümesinin alanı / toplam FRP) göre koşullamak; transfer için Avrupa'dan ikinci bir eğitim bölgesi.
- **Örneklem:** Aachen/Eifel'de 2022–2024'te toplam 7 MODIS tespiti → bölge test metriği istatistiksel olarak anlamsız; bu yüzden transfer_2012-2026 raporlandı (metrics.json'da değil, P4 onayı bekliyor).
