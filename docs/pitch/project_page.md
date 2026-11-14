# MODIS ↔ VIIRS Aktif Yangın Tespit Takvimi

Durum: P6 İbrahim'in yerel proje sayfası taslağı, 14 Kasım 2026. Sayısal dayanaklar ve kullanım sınırları: [pitch_facts.md](pitch_facts.md).

## Özet

Uydu arşivindeki tespit sayısı arttığında, bunun ne kadarı gözlenen olaydan, ne kadarı değişen gözlem sisteminden kaynaklanıyor? Projemiz NASA FIRMS aktif yangın tespitlerinden 2000–2026 dönemini kapsaması hedeflenen bir aylık takvim oluşturuyor. MODIS ve VIIRS'in farklı çözünürlükleri ve değişen uydu kapsamı, ham sayıların yıllar arasında doğrudan karşılaştırılmasını güçleştiriyor. Ham tespitleri ve harmonize (MODIS-eşdeğeri) tahminleri birlikte incelemek, bu farkı görünür kılmayı amaçlıyor. Harmonizasyonun başarısına ilişkin sonuçlar henüz bekleniyor.

## Sorun ve yaklaşım

Bir FIRMS kaydı, bir uydu geçişinde gözlenen bir termal anomali pikselidir. Aynı olay, komşu piksellerde ve birden fazla geçişte birçok tespit üretebilir. Bu nedenle takvimdeki sayı, doğrulanmış yangın olayı sayısı değildir. Yeni bir uydunun devreye girmesi veya gözlem özelliklerinin değişmesi de ham seride artış yaratabilir.

Yaklaşımımız, bölge ve tarih seçimiyle bu kayıtları aylık olarak incelemek ve ham seriyle MODIS-eşdeğeri tahmini karşılaştırmaktır. Harmonizasyon, uydu değişimlerinin karşılaştırmaya etkisini azaltmayı hedefler; bu etkinin giderildiğini göstermek için bağımsız test sonuçları gerekir.

## Gerçek veriyle iki Hohes Venn örneği

**Nisan 2011:** Süleyman'ın `data/hotspots.parquet` üzerinden doğruladığı sayımda, 25–26 Nisan'daki üç uydu geçişinde 17 MODIS piksel tespiti bulunuyor. Tümü bitki yangını tipinde ve Belçika tarafında. 2001–2025 döneminde 2011 dışındaki Nisanların ortalaması 0,67 tespit; Nisan 2011 bunun yaklaşık 25 katı ve **incelenen dönemin en yüksek Nisanı**. Bu bulgu, bilinen yangın olayıyla örtüşen bir tespit artışıdır.

**14–17 Ağustos 2026:** Aynı olay penceresinde 105 MODIS ve 1.794 VIIRS tespiti bulunuyor. VIIRS tespit sayısı MODIS'in yaklaşık 17 katı. Bu oran yalnızca bu bölge ve zaman penceresindeki ham tespitlerin karşılaştırmasıdır; evrensel bir harmonizasyon katsayısı değildir. Bu dört günlük sayım, Ağustos ayının tamamının toplamı olarak sunulmaz.

Bu sayılar, Süleyman'ın kullanıcı tarafından iletilen doğrulamasına dayanır; bu yerel belge çalışmasında yeniden hesaplanmamıştır.

## Yöntem ve doğrulama durumu

1. FIRMS DL_FIRE archive/NRT girdileri `argentina` ve `aachen_eifel` indirme alanları için ortak şemaya alınır. Birebir tekrarlar temizlenir; archive/NRT çakışmaları her bölge ve uydu için archive son tarihine göre giderilir.
2. Ham seride kayıtlar sayılır. Harmonize seride `weight_harm` toplamı MODIS-eşdeğeri tespit sayısı tahminini verir. Yöntemin sahibi P2 Bahtiyar'dır.
3. Sözleşmedeki başlangıç önerisi, Arjantin'in 2012–2021 verisinde MODIS/VIIRS oranı ve aktif VIIRS uydu sayısını kullanır. Bu, P2'nin nihai yöntemi ve P3'ün sonuçları gelene kadar doğrulanmamış bir hipotezdir.
4. Planlanan bağımsız test dönemi 2022–2024'tür. P3 çıktılarında R², bias, bias yüzdesi ve örnek sayısı; yöntem, bölge, dönem ve ölçek ile birlikte değerlendirilir. NOAA-21 öncesi 2022 ile 2023–2024 alt dönemleri de ayrı incelenir.

| Beklenen sonuç | Mevcut durum |
|---|---|
| Hohes Venn için harmonize (MODIS-eşdeğeri) tahmin; kapsamı ve tarih penceresiyle | [TBD — Bahtiyar] |
| Bağımsız test metrikleri ve üç cümlelik doğrulama özeti | [TBD — Oğuzhan] |

Sunumda kullanılacak metriklerin kaynağı `docs/validation/metrics.json`, açıklayıcı özetin kaynağı `docs/validation/summary.md` olacaktır. Sözleşme v1.3 §7.3 gereği yalnızca `data="harm"` çıktıları kullanılacak; sentetik veya yalnız ham veriden üretilmiş doğrulama metrikleri sonuç olarak sunulmayacaktır.

## Veri kaynakları ve araçlar

- NASA FIRMS: MODIS C6.1 ve VIIRS C2; DL_FIRE archive/NRT indirmeleri. S-NPP, NOAA-20 ve NOAA-21 VIIRS akışları sözleşmedeki uydu adlarıyla işlenir.
- İndirme alanları: `argentina` ve `aachen_eifel`. Hohes Venn ve La Rioja, uygulamada koordinatlarla seçilen görüntüleme alanlarıdır; indirme alanı adı doğrudan uygulama filtresi değildir.
- Eski ülke-yıl CSV dosyaları sözleşme v1.2 §5 uyarınca kapsam dışıdır; bu kural mevcut v1.3'te de korunur.
- Ortam: Python 3.12 ve kökteki `requirements.txt` dosyasının sabit sürümleri. Veri işleme için pandas, NumPy ve PyArrow; coğrafi sorgular için Shapely; arayüz için Streamlit, Folium ve Plotly.
- Görsel kaynak gösterimi: “NASA FIRMS / Worldview”. Gerçek veriyle doğrulanmış ekran görüntüleri bekleniyor; bu taslakta görüntü kullanılmadı. Sentetik veri ekran görüntüleri sunuma alınmaz; NASA logosu kullanılmaz.

## Kullanım ve sonraki adımlar

Takvim, bölgesel tespit örüntülerini inceleyen araştırmacılar ve çevre verisini yorumlayan kullanıcılar için uydu kapsamıyla birlikte okunabilen bir görünüm sunmayı hedefler. Sonraki adımlar, P2 çıktısını almak, P3'ün bağımsız test sonuçlarıyla yöntemin sınırlarını belirlemek ve gerçek veriyle kullanıcı testini tamamlamaktır. Arjantin'de geliştirilen yaklaşımın Hohes Venn'e aktarılabilirliği de değerlendirilmelidir.

## Ekip

| Rol | Sorumlu | Katkı |
|---|---|---|
| P1 | Süleyman | Veri alımı, ortak şemaya dönüşüm ve ham sayımlar |
| P2 | Bahtiyar | Harmonizasyon yöntemi ve çıktıları |
| P3 | Oğuzhan | Model değerlendirme ve bağımsız doğrulama |
| P4 | Barış | Ekip liderliği, veri sözleşmesi, sorgu katmanı ve testler |
| P5 | Yusuf | Uygulama arayüzü |
| P6 | İbrahim | Sunum, proje metni ve kullanıcı testi notları |
