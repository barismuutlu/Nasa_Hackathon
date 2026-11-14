# MODIS ↔ VIIRS Aktif Yangın Tespit Takvimi

P6 İbrahim · 14 Kasım 2026 · Sözleşme v1.3. Sayısal kaynaklar ve kapsam: [pitch_facts.md](pitch_facts.md).

## Özet

Uydu tespitleri arttığında, gözlenen olaylarla değişen gözlem sistemini nasıl ayırırız? NASA FIRMS kayıtlarından geliştirilen takvimimiz, 2000–2026 dönemindeki aktif yangın tespitlerini bölge ve ay bazında gösterir. Ham seri ile harmonize (MODIS-eşdeğeri) tahmin birlikte incelenir. Bir kayıt bir uydu geçişindeki termal anomali pikselidir; doğrulanmış yangın olayı değildir.

## Sorun ve çözüm

MODIS ve VIIRS'in çözünürlükleri ve gözlem kapsamları farklıdır. Yeni uyduların katılması, ham sayıları yıllar arasında doğrudan karşılaştırmayı güçleştirir. Arjantin'in 2012–2021 verisiyle geliştirilen Yöntem A, enlem bandı, yerel mevsim ve uyduya göre MODIS/VIIRS katsayıları ile aktif VIIRS uydu sayısını kullanır. Harmonize sayı, kayıtların `weight_harm` ağırlıkları toplamıdır; MODIS-eşdeğeri tespit sayısı tahmini olarak okunur.

## Hohes Venn: bilinen olaylarla örtüşen tespit artışları

**Nisan 2011:** 25–26 Nisan'daki üç uydu geçişinde 17 MODIS piksel tespiti vardır; Terra 14, Aqua 3. Hepsi bitki yangını tipinde ve Belçika tarafındadır. Harmonize seride de değer 17'dir. 2001–2026'daki diğer 25 Nisanın harmonize ortalaması yaklaşık 0,59: Nisan 2011 yaklaşık 29 katıyla incelenen 26 Nisanın en yükseğidir (1/26).

Ham, tüm-uydu serisinde aynı ayın karşılaştırma ortalaması 2,64 ve oranı 6,4 kattır. Bu fark, hangi seri ve karşılaştırma tabanının seçildiğini açıkça belirtmenin önemini gösterir. Önceki yaklaşık 25 kat ifadesi yalnız MODIS, 2001–2025 tabanına aittir.

**Ağustos 2026:** Aylık ham toplam 1.899 tespit: 105 MODIS ve 1.794 VIIRS. Harmonize aylık toplam P1'in son bildiriminde 169,2 MODIS-eşdeğeridir; konuşmada yaklaşık 169 denir. P1 tüm aktif tespitlerin 14–17 Ağustos'ta olduğunu teyit etmiştir. Yaklaşık 17,1 kat VIIRS/MODIS oranı evrensel katsayı değildir. Tahminin 105 MODIS referansından yaklaşık %61 yüksek olması, büyük olaya aktarım sınırını da gösterir.

**La Rioja:** Ham yıllık toplam 2011'de 868'den 2012'de 3.437'ye çıkarken harmonize seri 868'den 808'e gelir. Sınırlama: 2017 harmonize değeri 3.236, MODIS referansı 2.447; yaklaşık %32 fazla tahmin.

Bu sayımlar P1/P4'ün tam veri sorgularından iletilmiş; P6 yerelde yeniden hesaplamamıştır.

## MCD64A1 ile destekleyici yanmış alan kontrolü

Nisan 2011'deki 17 MODIS tespitinin 9'u, NASA'nın MCD64A1 ürününün 24–28 Nisan'da yanmış işaretlediği alanlarla 3×3 piksel komşuluğunda (yaklaşık 1,4 km genişlik) örtüşür. Zaman toleransı ±16 gündür. Ağustos 2026'da eşleşmeler MODIS için 93/105, VIIRS için 1.674/1.794; ürünün bildirilen yanma tarihleri 15–23 Ağustos'tur.

Kaynak: **NASA MCD64A1 C6.1**, aylık yanmış alan ürünü, yaklaşık 500 m. Sunum ifadesi: “Nisan 2011'de tespitlerin yarıdan fazlası (%53), Ağustos 2026'da MODIS tespitlerinin %89'u ve VIIRS tespitlerinin %93'ü, ürünün aynı dönemde yanmış haritaladığı alanlarla bu komşuluk ayarında örtüşüyor — destekleyici kanıt.”

Bu **destekleyici kanıttır, bağımsız doğrulama değildir**: MCD64A1 algoritması MODIS aktif yangın verisini de kullanır. Sayı komşuluk ayarına bağlıdır; küçük yanıklar kaçabilir. Bu tarihler aktif tespit tarihleriyle karıştırılmaz. Kaynak P1 mesajı (`26fa38d`) ve P3 `summary.md` güncellemesi (`c6f15ad`); ayrıntılar [pitch_facts.md](pitch_facts.md) içindedir.

## Bağımsız test

Kaynak: `docs/validation/metrics.json`, `b4cbbd4`; `data="harm"`, `method="harm"`, `region="argentina"`, ölçek `1deg`.

| Test dönemi | R² | Bias, tespit/hücre-ay | Bias % | n, hücre-ay |
|---|---:|---:|---:|---:|
| 2022–2024 | 0,7918 | +1,3674 | +6,72 | 8.616 |
| 2022 | 0,7052 | +5,0232 | +18,36 | 2.834 |
| 2023–2024 | 0,9291 | -0,4244 | -2,51 | 5.782 |

Hedef MODIS tespit sayısıdır; R² doğrulanmış yangın olayı doğruluğu değildir. 2022–2024, katsayı eğitiminden ayrılmış test dönemidir. NOAA-21 eğitimde bulunmadığı için NOAA-20 katsayıları vekil olarak kullanılır. 2022 fazla tahmini, küçük Aachen/Eifel örneklemi ve büyük olayda fazla tahmin yöntemin sınırlamalarıdır.

P3'ün geniş dönem bölgesel aktarım sonuçları henüz `metrics.json` içinde yoktur ve P4 onayı bekler; ana sunumun R² değeri yerine kullanılmaz. Aachen/Eifel 2022–2024 test metriği de yalnız 7 MODIS tespiti nedeniyle pitch'te kullanılmaz. Sayılar yöntem, bölge, dönem, ölçek ve n ile birlikte verilmelidir; uydu sıçramalarının tamamen giderildiği iddia edilmez. [Sınırlama slaytı](slides/limitations.md) bu ayrımı korur.

## Veri, araçlar ve demo

- NASA FIRMS MODIS C6.1 ve VIIRS C2; DL_FIRE archive/NRT. İndirme alanları `argentina` ve `aachen_eifel`; eski ülke-yıl CSV dosyaları kullanılmaz.
- Hohes Venn görüntüleme kutusu: boylam 5.95–6.25, enlem 50.45–50.60, sınırlar dahil. Aachen/Eifel indirme kutusu `(5.96, 50.44, 6.44, 50.83)`; ülke sınırı filtresi değildir.
- Bildirilen tam veri kapsamı 2000-11-01 → 2026-11-13. Cloud'daki deploy verisi yalnız hazır alanları kapsar; tam veriyle aynı satır sayısı beklenmez. Uydu kapsamı uygulamada `data_info()["satellite_ranges"]` üzerinden alınır.
- Python 3.12 ve `requirements.txt` sabit sürümleri; pandas, NumPy, PyArrow, Shapely, Streamlit, Folium ve Plotly. Ham `version` alanı korunur; enstrüman uydu kodundan belirlenir. MCD64A1 destekleyici kontrolü ayrı akıştır; FIRMS sayımlarıyla karıştırılmaz.
- Ekipten bildirilen [public demo](https://nasahackathon-6dh2dds5wpz3r6q9mz5zx3.streamlit.app/) gerçek ve harmonize veriye geçirilmiştir. P6 bu oturumda canlı tarayıcı kontrolünü tamamlayamamıştır. [Demo akışı](demo.md) ve [test notları](test_notes.md) gözlem kaynaklarını ayırır.
- Gerçek veri P3 [Hohes Venn takvimi](../validation/venn_check.png) çevrimdışı destek olarak kullanılabilir; bu bir uygulama ekran görüntüsü değildir. Görsellerde “NASA FIRMS / Worldview” kaynak bilgisi, bölge, tarih ve seri birimi belirtilir; NASA logosu ve sentetik ekran görüntüsü kullanılmaz.

Tarihsel 144 ülke-yıl CSV'si ve cloud ortam raporu [data_handoff.md](data_handoff.md), [data_transfer_package.json](data_transfer_package.json) ve [environment_check.md](environment_check.md) içinde ayrı kayıt olarak korunmuştur.

## Etki ve sonraki adımlar

Takvim, bölgesel tespit örüntülerini uydu kapsamıyla birlikte okumayı sağlar. Sonraki adımlar gerçek Cloud ekran görüntüleri, çevrimdışı demo kaydı ve kronometreli prova; ardından büyük olaylara ve farklı bölgelere aktarımı iyileştirmektir.

## Ekip

| Rol | Sorumlu | Katkı |
|---|---|---|
| P1 | Süleyman | Veri mühendisliği ve ham sayımlar |
| P2 | Bahtiyar | Harmonizasyon |
| P3 | Oğuzhan | Bağımsız test ve doğrulama |
| P4 | Barış | Liderlik, sözleşme, veri ve sorgu katmanı |
| P5 | Yusuf | Arayüz ve uygulama testleri |
| P6 | İbrahim | Sunum, proje metni, demo ve test notları |
