# MODIS ve VIIRS Aktif Yangın Tespitlerinin Harmonizasyonu

**NASA Space Apps Challenge 2026 — "Harmonization of MODIS and VIIRS Hot Spots"**

> **Canlı demo:** https://nasahackathon-6dh2dds5wpz3r6q9mz5zx3.streamlit.app/ · **Sunum:** _[link — yakında]_

NASA'nın 25 yıllık yangın kaydı, sürekli değişen uydularla oluşturuldu. MODIS (Terra 2000, Aqua 2002)
görev ömrünün sonuna yaklaşıyor; VIIRS cihazları (Suomi NPP 2012, NOAA-20 2018, NOAA-21 2023) ise çok
daha hassas. Her yeni uydu devreye girdiğinde **ham tespit sayısı sıçrıyor — yerde hiçbir şey
değişmemiş olsa bile.** Ham sayılardan çizilen bir trend çizgisi 2012'den sonra yangın aktivitesinin
keskin biçimde arttığını gösterir; bunun bir kısmı sadece daha çok ve daha iyi sensörün bakıyor olmasıdır.

Açık bir veri hattı ve etkileşimli bir uygulama geliştirdik: VIIRS tespitlerini **MODIS-eşdeğeri
sayılara** çeviriyoruz. Böylece 2000'den bugüne kadarki kayıt tek, tutarlı bir aylık takvim olarak okunabiliyor.

---

## Uygulama ne gösteriyor

| Görünüm | Amaç |
|---|---|
| **Harita + bölge çizimi** | Hazır bir bölge seç ya da istediğin çokgeni çiz; tek tek tespitleri gör |
| **Aylık takvim (yıl × ay)** | Her ay için yangın tespit aktivitesi, ham ya da harmonize |
| **Ham ve harmonize yıllık grafik** | Ham sayılar her uydu fırlatmasında basamak yapar (2012, 2018, 2023); harmonize seri yapmaz |
| **Anomali kartı** | Bir ayın, diğer tüm yıllardaki aynı takvim ayına göre ne kadar sıra dışı olduğu (sıra, normalin kaç katı) |
| **CSV dışa aktarma** | Seçili tespitleri ya da aylık tabloyu indir |

## Örnek: Hohes Venn (Yüksek Bataklıklar), Belçika/Almanya

| Olay | Veri ne gösteriyor |
|---|---|
| **Nisan 2011** (MODIS dönemi) | 25–26 Nisan'da **17 MODIS tespiti**, 3 uydu geçişi, hepsi bitki yangını olarak sınıflandırılmış. Harmonize seride diğer 25 Nisanın ortalaması ≈0,59 → **normalin ~29 katı, 26 yılın en yüksek Nisanı.** Ham seride aynı ay sadece ~6 kat görünüyor: VIIRS dönemindeki şişkin sayılar "normali" yükseltiyor. **Harmonizasyon olmadan tarihi bir olay olduğundan çok daha sıradan görünür.** |
| **Ağustos 2026** (VIIRS dönemi) | Aynı olay için (14–17 Ağustos) **105 MODIS ve 1.794 VIIRS tespiti** (ham toplam 1.899). Harmonize tahmin: **169 MODIS-eşdeğeri tespit**, 26 yılın en yüksek Ağustosu. |

2011 tespitlerinin tamamı Hohes Venn'in **Belçika** tarafında. Sadece Almanya verisi indirilseydi olay
hiç görünmezdi; bu yüzden çalışma alanlarımızı ülke olarak değil, koordinat kutusu olarak tanımladık.

## Nasıl çalışıyor

```
NASA FIRMS CSV'leri ──► ingest.py ──► hotspots.parquet ──► harmonize.py ──► hotspots_harm.parquet ──► uygulama (Streamlit)
 (MODIS + 3×VIIRS,       temizle, tekrar    tek şema           tespit başına        weight_harm          query.py ─► app.py
  archive + NRT)         sil, archive/NRT                      weight_harm                                   │
                         birleştir                                   │                                       ▼
                                                               validate.py ──► metrikler + grafikler   takvim, harita, anomali
```

1. **Okuma (ingest)** — tüm MODIS C6.1 ve VIIRS C2 (S-NPP, NOAA-20, NOAA-21) tespitleri, standart
   (archive) ve yakın gerçek zamanlı (NRT), tek bir şemaya çevrilir ([docs/CONTRACT.md](docs/CONTRACT.md)).
   Birebir tekrarlar silinir; archive ile NRT çakıştığında bölge ve uydu bazında archive (daha kaliteli)
   kalır. Farklı uydulardan ya da farklı geçiş zamanlarından gelen tespitler asla birleştirilmez.
2. **Harmonizasyon** — her tespite bir `weight_harm` ağırlığı verilir; ağırlıkların toplamı MODIS-eşdeğeri
   tespit sayısının tahminidir. Yöntem: Arjantin'de (2012–2021) enlem bandı ve yerel mevsime
   göre kalibre edilen bir MODIS/VIIRS oranı `k`, o gün aktif VIIRS uydu sayısına bölünür. Az örnekli enlem
   bantları birleştirilir (en az 500 MODIS tespiti). Eğitimde olmayan NOAA-21 için NOAA-20'nin katsayısı kullanılır.
   Sadece Terra'nın uçtuğu 2000-11 → 2002-07 döneminde Terra ağırlığı veriden 2,753'tür (Aqua, Terra'dan ~1,75 kat
   fazla tespit yakalıyor). Ayrıntılar: [`pipeline/harmonize.py`](pipeline/harmonize.py).
3. **Doğrulama** — katsayılar eğitimde kullanılmayan yıllarda (2022–2024) ve farklı bir bölge ve
   yarımkürede (Aachen/Eifel) test edilir. Sonuçlar aşağıda ve [`docs/validation/`](docs/validation/) içinde.
4. **Keşif** — küçük bir sorgu katmanı ([`app/query.py`](app/query.py)) üzerine kurulu Streamlit
   uygulaması ([`app/app.py`](app/app.py)).

## Doğrulama sonuçları

Tahmin: harmonize VIIRS (`Σ weight_harm`), gerçek: MODIS tespit sayısı, 1° hücre × ay ölçeğinde.
Katsayılar sadece Arjantin 2012–2021'den öğrenildi. Kaynak: [`docs/validation/metrics.json`](docs/validation/metrics.json).

| Arjantin | Harmonize R² | Harmonize sapma | Harmonizasyonsuz (ham VIIRS) sapma | n (hücre-ay) |
|---|---|---|---|---|
| Eğitim 2012–2021 | 0,92 | −%0,9 | +%390 | 27.568 |
| **Test 2022–2024** | **0,79** | **+%6,7** | **+%786** | 8.616 |
| Test 2023–2024 (eğitimde olmayan NOAA-21 aktif) | 0,93 | −%2,5 | +%849 | 5.782 |
| Test 2022 | 0,71 | +%18,4 | +%707 | 2.834 |

- **Bölge aktarımı (Aachen/Eifel, 2012–2026, bölge eğitime hiç girmedi):** R² 0,79, sapma +%35 (n=54). Bu R²
  büyük ölçüde tek olaydan (Ağustos 2026) geliyor; o ay hariç R² 0,37, sapma −%4,3. Yani olağan dönemde toplam
  seviye tutuyor, ama büyük olayda fazla tahmin var.
- **Destekleyici kanıt (bağımsız doğrulama değil):** NASA MCD64A1 yanmış alan ürününde, ±16 gün ve 3×3 piksel
  (≈1,4 km) komşuluğunda Ağustos 2026 tespitlerinin %89'u (MODIS) ve %93'ü (VIIRS), Nisan 2011'in 9/17'si yanmış
  piksele düşüyor. MCD64A1 de MODIS aktif yangın verisini kullandığı için bu bağımsız bir doğrulama değildir.

## Veri

Tüm veriler **NASA FIRMS**'ten (Fire Information for Resource Management System) alınmıştır:

| Ürün | Uydu(lar) | Kullanılan dönem |
|---|---|---|
| MODIS Collection 6.1 aktif yangın (standart + NRT) | Terra, Aqua | 2000-11 → 2026-11 |
| VIIRS 375 m Collection 2 aktif yangın (standart + NRT) | Suomi NPP | 2012-01 → 2026-11-02 (veri akışının sonu) |
| VIIRS 375 m Collection 2 aktif yangın (standart + NRT) | NOAA-20 | 2018-04 → 2026-11 |
| VIIRS 375 m Collection 2 aktif yangın (standart + NRT) | NOAA-21 | 2023-03 → 2026-11 |

Çalışma alanları: **Arjantin** (kalibrasyon; La Rioja dahil) ve **Aachen/Eifel**
(koordinat kutusu 5,96–6,44° D, 50,44–50,83° K; Hohes Venn dahil).
Karşılaştırma görüntüleri: NASA Worldview. Tam atıflar ve DOI'ler: [`docs/pitch/sources.md`](docs/pitch/sources.md).

## Bu ne — ve ne değil

- Bir **tespit**, termal anomali içeren bir uydu pikselidir. **Doğrulanmış bir orman yangını olayı
  değildir**; tek bir yangın çok sayıda tespit üretebilir, bazı tespitler de bitki yangını değildir.
- Harmonize seri bir **tahmindir**. Dönüşüm katsayıları bir bölgede kalibre edilip başka bir bölgede
  test edilmiştir; doğrulanmış küresel bir ürün değildir.

### Bilinen sınırlamalar

- **Yörünge kayması:** Terra ve Aqua özgün geçiş saatlerinden kayıyor; bu yüzden MODIS "referansı" da
  son yıllarda daha az kararlı.
- **Suomi NPP 2026-11-02'de sona erdi**; harmonizasyon aktif VIIRS uydu sayısını hesaba katıyor, ama
  değişimden hemen sonraki aylar daha belirsiz.
- **Sadece Terra dönemi (2000-11 → 2002-07):** tek bir MODIS uydusu vardı; Terra ağırlığı 2,753 ile
  düzeltildi (Arjantin 2003–2011 verisinden).
- **Taşınabilirlik:** Arjantin'de kalibre edilen katsayılar her ekosistem için geçerli olmayabilir. Aachen/Eifel'de
  örneklem küçük ve büyük olayda (Ağustos 2026) harmonize tahmin MODIS'in ~1,6 katı (169 / 105).
- **2022 sapması:** Arjantin'de 2022'de harmonize toplam MODIS'ten %18 fazla; ham veride de MODIS/VIIRS oranı
  eğitim aralığının dışında. Uydu kesintileriyle açıklanmıyor; 2023–2024'te normale dönüyor.
- **Hipotez (doğrulanmadı):** katsayı yangın büyüklüğüne bağlı olabilir. Büyük bir yangın cephesinde VIIRS
  (375 m), MODIS'e (1 km) göre orantısız çok piksel sayıyor. Gelecek çalışma: katsayıyı yangın kümesinin
  büyüklüğüne göre koşullamak ve Avrupa'dan ikinci bir eğitim bölgesi eklemek.
- **NOAA-21:** eğitim döneminde yoktu; NOAA-20'nin katsayısı kullanıldı (test 2023–2024 sonuçları yukarıda).
- **Saat dilimi:** aylar UTC'ye göre atanır.

## Yerelde çalıştırma

**Python 3.12** gerekir ([`.python-version`](.python-version)); kurulum için [uv](https://docs.astral.sh/uv/) kullanıyoruz.

```bash
git clone https://github.com/barismuutlu/Nasa_Hackathon.git
cd Nasa_Hackathon
uv venv --python 3.12 .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
python tests/smoke_test.py           # ortamı, veri sözleşmesini ve sorgu katmanını kontrol eder
python -m streamlit run app/app.py
```

Repoda küçük bir **sentetik** veri seti var (`data/mock/`), bu yüzden uygulama hemen çalışır; ekranda
"SENTETİK TEST VERİSİ" uyarısı görünür. Gerçek veriyle çalışmak için FIRMS CSV'lerini
`data/raw/<bölge>/` altına indir ve şunları çalıştır:

```bash
python pipeline/ingest.py      # → data/hotspots.parquet
python pipeline/harmonize.py   # → data/hotspots_harm.parquet, monthly_grid.parquet, k_factors.csv
python pipeline/validate.py    # → docs/validation/
```

## Repo yapısı

```
app/            Streamlit uygulaması (app.py) ve sorgu katmanı (query.py)
pipeline/       ingest → harmonize → validate
contract.py     her pipeline adımının kullandığı ortak veri şeması + doğrulayıcı
docs/           CONTRACT.md (veri sözleşmesi), validation/ (sonuçlar), pitch/ (sunum)
tests/          uçtan uca duman testi
data/mock/      geliştirme için sentetik veri (gerçek veri repoya eklenmez)
```

## Ekip

| Rol | Üye |
|---|---|
| Veri mühendisliği (okuma) | Süleyman |
| Harmonizasyon | Bahtiyar |
| Doğrulama | Oğuzhan |
| Veri katmanı, entegrasyon, ekip lideri | Barış |
| Uygulama / arayüz | Yusuf |
| Sunum ve test | İbrahim |

## Yapay zekâ kullanımı

Kod ve belgelerin yazımında ve gözden geçirilmesinde yapay zekâ kodlama asistanları (Claude Code)
kullandık. Tüm veri işleme tercihleri, bilimsel varsayımlar ve sonuçlar ekip tarafından gözden geçirildi;
doğrulama sayıları asistandan değil, veri hattının NASA verisi üzerinde çalıştırılmasından gelir.
