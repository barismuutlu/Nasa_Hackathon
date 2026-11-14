# P6 test notları ve kanıt durumu

P6 İbrahim · 14 Kasım 2026 · Güncel sözleşme v1.3.

Durum: Yusuf'un T01–T10 sonuçları kaydedildi; T08 elle, T06 benzetimle, T09'un tespitsiz-alan kısmı test edilmiş. T11 için P3 dosyaları geldi ve belge/JSON incelemesi burada yapıldı. P6'nın yerel uygulama tekrarı, gerçek Cloud ekran görüntüleri ve T12 prova/kayıt hâlâ bekliyor.

## Kaynaklar ve ortamlar

| Kaynak | Kanıt / veri | P6'nın yaptığı |
|---|---|---|
| P5 Yusuf, bildirilen uygulama referansı `2bc0e31` | AppTest + query API; tam `data/hotspots_harm.parquet`; 7.082.663 satır; `is_mock=False`, `has_harm=True` | Kullanıcı tarafından iletilen sonuçları aşağıya işledi; bu makinede tekrar çalıştırmadı |
| P1 Süleyman | Hohes Venn kutusu, dönem ve MODIS-only Nisan tabanları; kaynak tam parquet | Sayı/filtre tanımlarını belgelere işledi |
| P1 Süleyman, yeni teslim `26fa38d` | Güncel DL_FIRE ZIP'leri; Ağustos harm 169,2; MCD64A1 örtüşmeleri | Veri teslim notunu ve destekleyici kanıtı kaynak atfıyla güncelledi; ham dosya taşımadı |
| P4 Barış, `f0f0759` | Tam veri query sorguları; Hohes Venn aylık harmonize 169, Nisan 17; La Rioja yıllıkları; Cloud harmonize deploy bildirimi | Kaynak atfıyla kaydetti |
| P3 Oğuzhan, `b4cbbd4`, destekleyici özet `c6f15ad` | `docs/validation/metrics.json`, `summary.md` ve üç gerçek veri PNG'si | JSON kayıtlarını, özeti ve grafik içeriklerini inceledi; modeli yeniden çalıştırmadı |
| P6 yerel Windows ortamı | İlk incelemede `.venv/Scripts/python.exe` ve `uv` yok; tam parquet yok; repo deploy parquet'i mevcut | Python 3.12/sabit paket doğrulaması ve runtime testleri yapılmadı |

P5'in bildirdiği kapsam 2000-11-01 → 2026-11-13; uydular Aqua, NOAA20, NOAA21, SNPP, Terra. Uygulama commit'i ile veri sürümü farklı kanıtlardır; `2bc0e31` tek başına 7.082.663 satırlık dosyayı veya test koşusunu yeniden üretmez. Test zamanı, tam veri dosyasının SHA-256 değeri ve AppTest çıktıları bu mesajda verilmedi.

## Cloud teslimlerinin sırası

1. Yusuf: public link gizli pencerede girişsiz açılmış; o sırada sentetik uyarı bekleniyormuş.
2. Barış `0c8f808`: 139.779 satırlık gerçek deploy veri; harmonize ağırlıklar henüz boşmuş.
3. Barış `f0f0759`: gerçek + harmonize deploy hazır olarak bildirilmiş. Bu son bildirim önceki “harmonize henüz yok” durumunu günceller.

URL: https://nasahackathon-6dh2dds5wpz3r6q9mz5zx3.streamlit.app/

P6'nın bu oturumdaki web erişim denemesi “URL is not accessible via this tool” hatasıyla sonuçlandı. Etkileşimli tarayıcı aracı da sunulmadı. Bu, sitenin kullanıcılar için kapalı olduğunu göstermez; P6 public erişimi, canlı veri durumunu veya gizli pencere akışını bağımsız doğrulamadı. Ekran görüntüsü alınmadı.

Cloud deploy yalnız hazır bölgeleri kapsar; kutular dışında “tespit yok” görüntüsü veri kapsamıyla ilişkili olabilir. Tam veri ile deploy dosyasının satır sayısı eşit olmak zorunda değildir.

## T01–T12: beklenen ve aktarılan gözlenen sonuçlar

T01–T10 gözlemleri aksi belirtilmedikçe Yusuf'un kullanıcı aracılığıyla ilettiği rapordur. T01–T10 P6'nın yerel testi olarak işaretlenmez. P1'in teyit ettiği kutu: `lon 5.95–6.25, lat 50.45–50.60`, sınırlar dahil; `query.PRESETS["Hohes Venn"]` ile aynı.

| ID | Adım | Beklenen | Gözlenen / kaynak / durum | İlgili kişi |
|---|---|---|---|---|
| T01 | Gerçek veriyle aç; kaynak/kapsam/uyduları kontrol et. | Sentetik uyarısı yok; uygun kaynak ve kapsam. | ✅ Yusuf: uyarı yok; 2000-11-01 → 2026-11-13; Aqua, NOAA20, NOAA21, SNPP, Terra. Tam harmonize dosya, `is_mock=False`, `has_harm=True`. P6 yerel tekrarı yok. | Barış / Yusuf |
| T02 | Hohes Venn, Ham, 1–30 Nisan 2011; CSV/geçişleri incele. | 17 MODIS tespiti; üç geçiş; tümü `type=0`. | ✅ Yusuf: 25 Nis Terra 9; 26 Nis Terra 5 + Aqua 3. P1 ayrıca Belçika tarafını teyit etti. | Süleyman / Barış / Yusuf |
| T03 | Nisan karşılaştırmasında sensör/dönem tabanlarını ayır. | Aynı tanımla aynı ortalama ve sıra. | ✅ Yusuf: MODIS-only 2001–2025, diğer 24 Nisan ort. ≈0,67 → 25,5×. P1/P4: 2001–2026 ham ort. 2,64 → 6,4×; harm ort. 0,59 → 28,7×; her iki kart 1/26. Fark hata değil, taban farkı. | Süleyman / Barış / Yusuf |
| T04 | Hohes Venn, Ham, 14–17 Ağustos 2026; `instrument` bazında say. | MODIS 105, VIIRS 1.794; yaklaşık 17,1×. | ✅ Yusuf aynı sayıları raporladı. P1 ayın tüm tespitlerinin bu dar aralıkta olduğunu; P4 aynı aylık ham toplamı 1.899 olarak bildirdi. P6 tarih sınırlarını yeniden sorgulamadı. | Süleyman / Barış |
| T05 | T04 dar tarih aralığında Ağustos hücresini incele. | Kısmi ay işareti ve hover'da gün aralığı. | ✅ Yusuf: • işareti ve gün aralığı mevcut. Sayı tam ayla aynı olsa da tarih filtresi kısmi ay. | Yusuf |
| T06 | `has_harm=False` durumunu benzet; Harmonize seç. | “Harmonize veri henüz hazır değil”. | ✅ Yusuf: benzetimle test edildi. Bu sonuç güncel gerçek veride ağırlıkların boş olduğu anlamına gelmez. | Yusuf / Barış |
| T07 | La Rioja, aynı tam kapsam; yıllık ham/harmonize toplamı karşılaştır. | Harm toplamı `Σ weight_harm`; ham ve tahmin birimleri ayrı. | ✅ Yusuf: 2011 ham/harm 868/868; 2012 3.437/808; `monthly_matrix(...,"harm")` ağırlık toplamı. P4 ek yılları ve 2017 sınırlamasını iletti; tam tablo `pitch_facts.md` içinde. | Bahtiyar / Barış / Yusuf |
| T08 | Alan çiz; takvim/CSV eşleşmesini ve Çizimi temizle'yi dene. | Aynı etkin alan; temizleme hazır bölgeye döner. | 🖐 Yusuf sabah elle test etmiş: eşleşiyor, temizleme bölgeye dönüyor. P6 bilgisayarında tekrar edilmedi. | Yusuf |
| T09 | Tespitsiz alanı ve ayrıca kapsam dışı ayı incele. | Tespit yokluğu ile veri yokluğu ayrı; çökme yok. | ✅ Yusuf: tespitsiz alan “Bu bölgede tespit yok”, çökme yok. Kapsam dışı ay alt kontrolü bu raporda ayrıca doğrulanmadı; bekliyor. | Barış / Yusuf |
| T10 | Ham/harmonize modda CSV indir. | UTF-8; kanonik alanlar; `weight_harm` korunur. | ✅ Yusuf: Hohes Venn Nisan 2011 her iki modda 17 satır; UTF-8 okunuyor, `weight_harm` var. CSV satır sayısı diğer dönemlerde harm toplamı sayılmaz. | Barış / Yusuf |
| T11 | P3 JSON, özet ve grafiklerin sunuma uygunluğunu incele. | `data="harm"`; yöntem/bölge/split/ölçek/n açık. | ✅ P6 belge incelemesi: `b4cbbd4` dosyaları geldi; Arjantin test 1deg: R²=0,7918, bias=+1,3674, bias %=+6,72, n=8.616. Alt dönemler kontrol edildi. Aktarım paneli için aşağıdaki sınır geçerli. Model yeniden çalıştırılmadı. | Oğuzhan / İbrahim |
| T12 | Gerçek ekranları kaydet, çevrimdışı aç ve süreyi ölç. | Sentetik görüntü yok; kaynak/alan/tarih açık; video çevrimdışı açılır; konuşma <4:00. | ⏳ Bekliyor. Akış ve çekim planı `demo.md` içinde; kayıt ve kronometreli prova yapılmadı. | İbrahim |

## T11 sınırlamaları ve görsel inceleme

- Arjantin 1deg `harm` metrikleri: 2022 R²=0,7052, bias %=+18,36, n=2.834; 2023–2024 R²=0,9291, bias %=-2,51, n=5.782. Toplam testteki +%6,72, 2022 fazla tahminini gizlememeli.
- Aachen/Eifel test örneklemi küçük: `1deg/test` n=12; 2022 n=3. P3 bu üç yılda toplam 7 MODIS tespiti nedeniyle bölgenin 2022–2024 test R²'sinin pitch'te kullanılmamasını istedi; ana metrik tablosundan çıkarıldı. Bu iç kontrol model başarısı iddiası değildir.
- `pred_vs_true.png` yerelde açıldı: sol panel Arjantin 2022–2024, sağ panel Aachen/Eifel 2012–2026 aktarımı. Sağdaki aktarım metrikleri `metrics.json` içinde yok ve P3 özetine göre P4 onayı bekliyor. Tam iki panelli görsel ana sunuma alınmadan bu konu çözülmeli; P6 dosyayı değiştirmedi.
- `venn_check.png` yerelde açıldı; aylık ham 17/1.899 ve harmonize 17/169 etiketleri görüldü. Gerçek veri takvimidir, canlı uygulama ekran görüntüsü değildir.
- `annual_raw_vs_harm.png` yerelde açıldı; bölge Arjantin'dir, La Rioja değildir. Çevrimdışı kullanımda bölge etiketini değiştirme.
- Ağustos 169 MODIS-eşdeğeri tahminin 105 MODIS referansından yaklaşık %61 yüksek olması ve La Rioja 2017'de yaklaşık %32 fazla tahmin sınırlamalarda korunur.

## P1/P3 MCD64A1 destekleyici kontrol kaydı

P1'in ilettiği `data/burned_area_check.csv` sonuçları: 3×3 piksel komşuluğu (≈1,4 km genişlik), ±16 gün. Nisan MODIS 9/17; Ağustos MODIS 93/105, VIIRS 1.674/1.794. Ürünün yanma tarihleri sırasıyla 24–28 Nisan ve 15–23 Ağustos; aktif Ağustos tespitleri 14–17 Ağustos'tur. P1'in tek piksel / 5×5 Nisan karşılaştırması 5/17 ve 15/17'dir. Bu sonuçlar P6 tarafından yeniden çalıştırılmadı.

Yeni `summary.md` (`c6f15ad`) tablosu 9 eşleşen + 8 yanmamış = 17; 93 + 12 = 105; 1.674 + 120 = 1.794 olarak aynı toplamları veriyor. Buradaki “yanmamış” MCD64A1 kontrolünün sınıfıdır; aktif tespitin yanlış olduğunu kanıtlamaz. `unknown/no_data` bundan ayrıdır. Ürün MODIS aktif yangın girdisini de kullandığı için bu yalnız destekleyici kanıttır; bağımsız doğrulama değildir.

P3'ün son teslim kontrolü PowerShell `Select-String` ile çalıştırıldı: tabloda 9 (%53), 93 (%89), 1.674 (%93) görüldü. Yerel `venn_check.png` Git nesne kimliği `c6f15ad` sürümüyle birebir eşleşti; `docs/validation/` altında yerel değişiklik yok. Kaynak adı sunum metinlerinde “NASA MCD64A1 C6.1” olarak netleştirildi. Bu kontrol dosya/teslim tutarlılığıdır; yanmış alan analizinin yeniden çalıştırılması değildir.

P1 ayrıca eski Belçika ülke-yıl dosyasındaki 17 kayıtla DL_FIRE kayıtlarının birebir eşleştiğini bildirdi. Bu iki FIRMS indirmesinin tutarlılığıdır; bağımsız yer gerçeği kontrolü olarak sunulmaz. Sayısal metriklerden ayrı tutuldu; yeni [sınırlama slaytı](slides/limitations.md) aynı çerçeveyi korur.

## P1'in son sayısal incelemesi

Kaynak: Süleyman'ın `9c8abb9` referanslı mesajı. Nisan geçişleri, 25,5× / 26,6× / 6,4× / 28,7× tabanları ve 26 Nisan kapsamı; Ağustos 105 + 1.794 = 1.899, harmonize 169,2 ve yaklaşık +%61; MCD64A1 oranları/tarihleri/duyarlılığı; La Rioja 2011/2012/2017/2018/2023 değerleri ve 2017 yaklaşık +%32 veriden kontrol edilmiş ve fark bildirilmemiştir. Bu P1'in raporudur; P6 bu makinede yeniden hesaplamadı.

Konumsal ifade netleştirildi: kalan 8 tespit eşleşenlerin güney/doğu çevresinde; 5×5 komşulukta 6'sı daha eşleşiyor. Yanık sınırı haritasıyla ölçülmediğinden “yanık kenarında” yorumu kullanılmıyor. Sayısal sonuçlar değiştirilmedi.

## P3 teslimindeki kontrol komutu

İstenen Python kontrolü bu makinede çalıştırılmadı: Python 3.12 sanal ortamı yok. Aynı JSON kaydı PowerShell ile yerelde okunarak kontrol edildi: `data=harm`, `method=harm`, `region=argentina`, `split=test`, `scale=1deg`; R²=0,7918, bias_pct=6,72, n=8.616. `summary.md` açılıyor ve “Sunum için 3 cümle” bölümü mevcut. Bu dosya incelemesidir; runtime/model testi değildir.

## Yerelde tekrar çalıştırma — henüz yapılmadı

Yalnız Python 3.12 sanal ortamı ve sabit `requirements.txt` kurulmuşken repo kökünde:

~~~powershell
.\.venv\Scripts\Activate.ps1
python --version
python tests/smoke_test.py
python -m streamlit run app/app.py
~~~

Beklenen: Python 3.12.x, sabit paket kontrolü PASS ve smoke çıkış kodu 0. Eksik dosyalar için ATLANDI, o verinin test edildiği anlamına gelmez. Uygulamada veri yolunu kontrol et: `HOTSPOTS_PATH` → tam harm → tam raw → deploy → mock önceliği; ham tam dosya deploy'u gölgeleyebilir. “SENTETİK” ekranlar sunuma alınmaz.

Nisan kartını tüm dönemle kontrol et; yalnız Nisan 2011 tarih filtresi seçilirse 26 Nisanlık taban korunmaz. Tekrar üretim komutu ve beklenen raw/harm çıktıları `pitch_facts.md` içindedir.

## Hata / açık kontrol kaydı

P6 yerel uygulama testi yapmadı; Yusuf'un aktardığı sonuçlarda uygulama hatası bildirilmedi. Kod değişikliği yapılmadı.

| ID | Konu | Kanıt / beklenen | Durum / ilgili kişi |
|---|---|---|---|
| A01 | Aktarım panelinin metrik kaydı | `summary.md` ve `pred_vs_true.png` içinde var; izinli split/JSON kaydı yok | P3/P4 onayı ve sözleşmeye uygun çıktı bekleniyor; P6 ana sunumda kullanmıyor |
| A02 | Canlı ekranlar ve public erişimin P6 kontrolü | Ekip public ve gerçek/harmonize bildirdi; bu oturumdaki web aracı açamadı | Ekran görüntüleri ve P6 tekrarı bekliyor; İbrahim/Yusuf |
| A03 | T09 kapsam dışı ay alt kontrolü | Gelen rapor yalnız tespitsiz alanı kapsıyor | Ek kontrol bekliyor; Barış/Yusuf |

## Aktarılan cloud kontrolleri — tarihsel kayıt

Kaynak: `P6_ibrahim.patch`, önceki cloud referansı `8d5894c`, sözleşme v1.2. Aşağıdaki sonuçlar cloud oturumunun raporudur; bu Windows çalışma alanında yeniden üretilmedi. Mevcut yerel sözleşme v1.3'tür. Bu eski rapor, bu belgedeki yeni P5/P3 sonuçlarından ayrıdır; P6'nın yerel uygulama tekrarı değildir.

| Cloud kontrolü | Cloud'un bildirdiği gözlem | Kullanım sınırı / ilgili kişi |
|---|---|---|
| Python ve sabit paketler | Python 3.12.14; 10 doğrudan bağımlılık sabit sürümleriyle eşleşmiş | Yerel ortamın kurulu olduğunu göstermez. Ayrıntı: `environment_check.md`; P4 Barış. |
| Smoke testi | 7 kontrol geçmiş, 6 atlanmış, 0 hata; query dosyası `data/mock/hotspots_mock.parquet` | Sentetik kontrol, gerçek veri veya harmonizasyon başarısı değildir; P4 Barış. |
| Tarihsel ülke-yıl CSV'leri | Almanya, Belçika, Arjantin: ülke başına 48, toplam 144 dosya ve 6.893.939 ham satır | Güncel DL_FIRE girdisi değildir; P1 Süleyman. |
| CSV alanları | MODIS `brightness/bright_t31`; VIIRS `bright_ti4/bright_ti5`; tüm tarihsel dosyalarda `type` bulunduğu bildirilmiş | DL_FIRE veya NRT başlıkları/tip doluluğuna genellenmez; P1/P4. |
| Ham sürüm alanı | MODIS `6.2`, `6.03`, `61.03`; VIIRS `2`; değerler değiştirilmemiş | Yayın koleksiyonu ifadesi ayrıca teyit edilmeli; P4 Barış. |
| Yapı ve kaynak boyutları | Alan sayısı bozuk satır ve kontrol edilen temel alanlarda boşluk bulunmamış; 144 dosyanın boyutu NASA listesiyle eşleşmiş | SHA-256 kayıtları manifestte; yerel dosyalar burada kontrol edilmedi; P1 Süleyman. |
| Tarihsel Belçika ön kontrolü | 50.45–50.60 enlem, 5.95–6.25 boylam kutusunda, 25–26 Nisan 2011 için 17 MODIS satırı | P1'in kanonik parquet doğrulamasından ayrı ön kontrol; olay doğrulaması değildir. |
| Eksik kapsam | Ülke-yıl arşivinde 2026 ve NOAA-21 yok; önceki NOAA-21 başlangıç sorusu v1.2'de 1 Mart 2023 olarak çözülmüş | Güncel girişler yalnız DL_FIRE archive/NRT; P1/P4. |
| Aktarım paketi | ZIP bütünlük kontrolü geçmiş olarak raporlanmış; bayt ve SHA-256 `data_transfer_package.json` içinde | ZIP veya CSV'ler bu patch ile aktarılmadı; güncel girdi klasörlerine açılmaz; P1/P4. |
| Jüri kriterleri belgesi | `2026 Judging Criteria.docx` cloud çalışma alanında bulunamamış; taşıma yapılmamış | Yerel veya Drive araması yapıldığı anlamına gelmez; P6 İbrahim. |

Eski indirme akışına ait komutlar ve taşıma yönergeleri tarihsel belgelerdir; bu birleştirmede çalıştırılmadı. Ham CSV yapısının uygunluğu; ingest doğrulaması, kapsam, tekrar temizliği veya P3 bilimsel doğrulaması yerine geçmez.

## Yerel belge kontrolü ve teslim

- [x] P1 kutu/dönem teyidi, P4 harmonize sayıları ve P5 gözlemleri kaynaklarıyla işlendi.
- [x] P1 güncel girdi teslimi, tarihsel arşivi `data/raw/` dışında tutma kuralı ve MCD64A1 bağımlılık/ayar çerçevesi işlendi.
- [x] 26 Nisan kapsamı ve yaklaşık 25× / 26,6× / 6,4× / 28,7× tabanları ayrıldı.
- [x] P3 metrikleri yalnız `data="harm"` JSON kayıtlarından, alan/split/ölçek/n ile alındı; aktarım paneli ayrıldı.
- [x] Tarihsel cloud ortam raporu, P5 testleri ve P6 belge incelemesi birbirinden ayrıldı.
- [ ] P6 yerel Python/runtime tekrarı ve T08 elle tekrar tamamlandı.
- [ ] Canlı Cloud ekranları, çevrimdışı demo videosu ve <4:00 prova tamamlandı.
- [x] Önceki toplu belge teslimi (`9c8abb9`) için kullanıcı açık push onayı verdi.

Tarihsel manifest için önceki yerel kontrol: 144 kayıt, 6.893.939 ham satır, 554.614.725 bayt; JSON/CSV iç tutarlılığı eşleşmişti. Kaynak CSV/ZIP dosyaları veya SHA-256 içerikleri yerelde yeniden doğrulanmadı.
