# P6 kullanıcı testi ve belge kontrol notları

P6 İbrahim · 14 Kasım 2026. Durum: belge incelemesi yapıldı; uygulama ve veri testleri henüz çalıştırılmadı. Aşağıdaki beklenen sonuçlar test planıdır, gözlenmiş başarı değildir.

## Yerel başlangıç durumu

- Git ilk incelemede temizdi; `docs/pitch/` yalnız `.gitkeep` içeriyordu. Önceki cloud çalışmasının dosyaları veya patch'i kullanılmadı.
- `CLAUDE.md`, `docs/CONTRACT.md` ve `ekip/P6_Ibrahim.CLAUDE.md` okundu. Yerel sözleşme v1.3; ülke-yıl girdilerini dışlayan v1.2 kuralı korunuyor.
- `.python-version` Python 3.12 istiyor; `requirements.txt` bağımlılıkları `==` ile sabitliyor. İlk incelemede `.venv/Scripts/python.exe` ve `uv` bulunmadı. Python 3.12 ve paket sürümleri çalışma zamanında doğrulanmadı.
- `data/hotspots.parquet`, `data/hotspots_harm.parquet`, `data/satellite_coverage.csv`, `docs/validation/metrics.json` ve `docs/validation/summary.md` ilk incelemede bulunmadı.
- Olay sayımları Süleyman'ın kullanıcı tarafından iletilen doğrulamasından alındı; bu makinede yeniden hesaplanmadı. Gerçek veri görseli üretilmedi veya uygulama başarısı raporlanmadı.

## Çalıştırma önkoşulları

Python testleri ve uygulama yalnız repo kökünde, etkin Python 3.12 sanal ortamı ve sabit gereksinimlerle çalıştırılmalı. Sistem Python'uyla veya tek tek paket kurarak devam edilmez. Bu dokümantasyon çalışmasında ortam kurulmadı; yalnız `docs/pitch/` dosyaları değiştirildi.

Ortam kurulduktan sonra PowerShell'de:

```powershell
.\.venv\Scripts\Activate.ps1
python --version
python tests/smoke_test.py
```

Beklenen: Python `3.12.x`; smoke testindeki `ortam: Python 3.12 + requirements.txt sürümleri` kontrolü PASS; başarısız kontrol olmaması ve çıkış kodunun 0 olması. Eksik pipeline dosyaları için `ATLANDI` görülebilir; bu, gerçek veri veya harmonizasyonun test edildiği anlamına gelmez. Sentetik veriyle geçen smoke testi bilimsel doğrulama değildir.

Gerçek veri dosyaları geldikten ve ortam kontrolünden sonra:

```powershell
python -m streamlit run app/app.py
```

Beklenen: yerel uygulama açılır. `Veri / Data` bölümünde gerçek veri yolu ve uygun kapsam görülür. Veri önceliği nedeniyle farklı bir dosya seçilebileceğinden kaynak yolunu kontrol et; “SENTETİK TEST VERİSİ” varsa sunum için ekran görüntüsü alma. Harmonize testler için `data/hotspots_harm.parquet` ve hazır ağırlıklar gerekir.

## Bekleyen test senaryoları

Her senaryodan önce uygulama sürümünü, veri yolunu, kapsamı ve seçili alanı kaydet. Sayısal karşılaştırmalarda Süleyman'ın tam coğrafi filtresiyle uygulamadaki alanın eşleşmesi önkoşuldur. Haritadaki nokta sayısı yerine tablo/CSV kayıtlarını kontrol et; harita büyük sonuçları örnekleyebilir.

| ID | Adım | Beklenen | Gözlenen / durum | Sorun varsa sorumlu |
|---|---|---|---|---|
| T01 | Gerçek veriyle uygulamayı aç; `Veri / Data` bölümünü incele. | Yol, tarih aralığı ve uydular doğru; sentetik uyarısı yok. | Çalıştırılmadı — ortam ve gerçek veri bekleniyor. | Barış: veri seçimi; Yusuf: gösterim |
| T02 | `Hohes Venn`, `Ham / Raw`, 1–30 Nisan 2011 seç; CSV'yi incele. | P1 ile aynı alanda 17 MODIS tespiti; 25–26 Nisan ve üç geçiş. Tümü bitki yangını tipinde (`type=0`); Belçika tarafı bilgisi P1'in coğrafi kontrolüyle doğrulanır, yalnız bbox seçimine dayanmaz. | Çalıştırılmadı — veri ve P1 alan tarifi bekleniyor. | Barış: sorgu/sayı; Yusuf: arayüz; Süleyman: referans sayım |
| T03 | Aynı alan için 2001–2025 Nisanlarını karşılaştır; 2011'i ortalama tabanından çıkar. | Diğer Nisanların ortalaması yaklaşık 0,67; 2011 yaklaşık 25 kat ve incelenen dönemin en yüksek Nisanı. Yıl sayısını ayrıca teyit et. | Çalıştırılmadı — referans tabanla eşleşme bekleniyor. | Barış: anomali tabanı; Süleyman: kapsam; Yusuf: etiket |
| T04 | `Hohes Venn`, `Ham / Raw`, 14–17 Ağustos 2026 seç; CSV'deki `instrument` alanına göre say. | Aynı P1 alanında 105 MODIS ve 1.794 VIIRS tespiti; yaklaşık 17 kat. Sayılar olay sayısı veya harmonize tahmin olarak etiketlenmez. | Çalıştırılmadı — veri ve P1 alan tarifi bekleniyor. | Barış: sorgu/sayı; Yusuf: etiket; Süleyman: referans sayım |
| T05 | T04 aralığında Ağustos hücresini ve tarih açıklamasını incele. | Hücre kısmi ay olarak işaretli; 14–17 Ağustos sonucu tam ay diye sunulmuyor. | Çalıştırılmadı. | Yusuf |
| T06 | Harmonize veri olmadan `Harmonize / Harmonized` seç. | “Harmonize veri henüz hazır değil” mesajı; ham sayı harmonize sonuç olarak sunulmuyor. | Çalıştırılmadı. | Yusuf: mesaj; Barış: veri durumu |
| T07 | P2 çıktısı geldikten sonra `La Rioja (AR)` ve aynı tarih/alan için ham ↔ harmonize görünümünü karşılaştır. | Ham birim ile MODIS-eşdeğeri tahmin ayrılıyor; harmonize toplam ağırlık toplamıyla eşleşiyor. Beklenen sayı: [TBD — Bahtiyar]. Görselde düzleşme tek başına doğrulama sayılmıyor. | Çalıştırılmadı — P2 çıktısı bekleniyor. | Bahtiyar: ağırlıklar; Barış: toplam; Yusuf: gösterim |
| T08 | Çizimle seçili alanı değiştir; `Çizimi temizle` ve bölge seçimini dene. | Harita, takvim ve CSV aynı etkin alanı kullanıyor; temizleme hazır bölgeye dönüyor. | Çalıştırılmadı. | Yusuf: etkileşim; Barış: geometri sorgusu |
| T09 | Veri kapsamı içinde tespitsiz bir alan ve mevcutsa kapsam dışı bir ay incele. | Tespit yokluğu ile veri yokluğu ayrılıyor; harmonize verinin eksik olması sıfır tahmin sayılmıyor. | Çalıştırılmadı. | Barış: sorgu/takvim; Yusuf: mesaj/renk |
| T10 | Ham ve harmonize modda `CSV indir` çıktısını incele. | Türkçe UTF-8 okunuyor, bir satır bir tespit; `weight_harm` alanı korunuyor. CSV kayıt sayısı kendiliğinden harmonize toplam sayılmıyor. | Çalıştırılmadı. | Barış: dışa aktarım; Yusuf: indirme etiketi |
| T11 | P3 metriklerini ve grafikleri proje metnine almadan önce incele. | Sunuma yalnız `data="harm"` çıktıları alınır; ana sonuç `method="harm"`, `split="test"` kaydından, bölge/ölçek/`n` ile aktarılır. 2022 ve 2023–2024 ayrımı da kontrol edilir. Metrikler: [TBD — Oğuzhan]. | Çalıştırılmadı — P3 çıktısı bekleniyor. | Oğuzhan: çıktı; İbrahim: aktarım |
| T12 | Gerçek veriyle demo kaydını çevrimdışı aç; konuşmayı kronometreyle prova et. | Kaynak/tarih/alan etiketleri okunuyor, sentetik görüntü yok; video internet olmadan açılıyor; konuşma 4:00 altında. | Çalıştırılmadı — kayıt ve prova bekleniyor. | İbrahim |

## Hata kayıt şablonu

Uygulama çalıştırılmadığından doğrulanmış uygulama hatası kaydedilmedi. Sorun bulunursa P6 yalnız bu dosyaya kayıt açar; `app/`, `pipeline/`, sözleşme veya ortak testleri değiştirmez.

| Tarih / test ID | Sürüm ve veri yolu | Adım / alan / tarih / mod | Beklenen | Gözlenen ve kanıt | Sorumlu | Durum |
|---|---|---|---|---|---|---|
| — | — | — | — | Henüz uygulama gözlemi yok. | — | — |

## Belge teslim kontrolü

- [x] Dört P6 belgesi yerelde hazırlandı; yalnız `docs/pitch/` kapsamına yazıldı.
- [x] Sayıların kaynağı Süleyman olarak belirtildi; yerelde yeniden hesaplandığı iddia edilmedi.
- [x] Nisan için “incelenen dönemin en yüksek Nisanı” kullanıldı; 26 yıl ifadesi teyit bekliyor.
- [x] Ağustos olay penceresi tam aydan ayrıldı; yaklaşık 17 kat oranı evrensel katsayı sayılmadı.
- [x] Harmonize sayı `[TBD — Bahtiyar]`, metrikler `[TBD — Oğuzhan]` olarak bırakıldı.
- [x] DL_FIRE archive/NRT alanları ve eski ülke-yıl dosyalarının dışlandığı belirtildi.
- [x] Sentetik veri ekran görüntüsü veya uydurulmuş sonuç eklenmedi.
- [ ] Python 3.12 ve sabit paketlerle smoke testi ve gerçek veri kullanıcı testleri çalıştırıldı.
- [ ] Gerçek veri görselleri, çevrimdışı demo ve süre ölçümü tamamlandı.
- [ ] Kullanıcı belgeleri gözden geçirdi; gerekli düzeltmeler tamamlandı.
