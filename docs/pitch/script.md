# Yaklaşık dört dakikalık konuşma taslağı

P6 İbrahim · 14 Kasım 2026. Hedef süre 3:55; kronometreli prova henüz yapılmadı. Bölüm süreleri planlanan bütçedir. Sayısal dayanak: [pitch_facts.md](pitch_facts.md).

Sunucu notu: Köşeli parantezler hazırlık notudur, sesli okunmaz. Gerçek veri ekran görüntüleri ve demo henüz doğrulanmadı. “SENTETİK TEST VERİSİ” görünen ekranı kullanma. Görsel yoksa doğrulanmış sayıları metin olarak göster. P2/P3 sonucu gelmezse aşağıdaki bekleyen-sonuç cümlelerini kullan.

## 00:00–00:30 · Sorun

[Ekran: proje adı ve “Tespit sayısı neden değişiyor?” sorusu.]

“Bir bölgede uydu tespitleri artıyorsa, bu artışı nasıl yorumlarız? Gözlenen olaylar değişmiş olabilir; fakat gözlem yapan uydular da değişiyor. NASA FIRMS arşivinde MODIS ve VIIRS farklı gözlem özelliklerine sahip. Yeni uydular eklendiğinde ham tespit sayısını geçmiş yıllarla doğrudan karşılaştırmak yanıltıcı olabilir. Bizim sorumuz şu: Bu uzun kaydı, uydu değişimlerini hesaba katarak nasıl okuyabiliriz?”

## 00:30–01:00 · Aynı olay, farklı tespit sayıları

[Ekran: Hohes Venn, 14–17 Ağustos 2026; MODIS 105, VIIRS 1.794. Kaynak: Süleyman'ın `data/hotspots.parquet` sayımı.]

“Hohes Venn'de 14–17 Ağustos 2026 olay penceresine bakalım. Süleyman'ın gerçek veriden doğruladığı sayımda 105 MODIS ve 1.794 VIIRS tespiti var. Aynı pencere için VIIRS tespit sayısı yaklaşık 17 kat. Buradaki sayılar piksel tespitleri; yangın olayı sayısı değil. Bu tek örneğin oranını evrensel bir harmonizasyon katsayısı olarak da kullanmıyoruz.”

## 01:00–02:00 · Çözüm ve yöntem

[Ekran: FIRMS DL_FIRE → ortak şema → ham aylık takvim / MODIS-eşdeğeri tahmin. Bu bir yöntem şemasıdır; sonuç grafiği değildir.]

“Çözümümüz, ham tespitlerle harmonize tahmini birlikte okuyabileceğimiz aylık bir takvim. Verilerimiz FIRMS DL_FIRE archive ve NRT indirmelerinden geliyor. İndirme alanlarımız Arjantin ve Aachen/Eifel. Önce kayıtları ortak şemaya alıyor, birebir tekrarları ve archive ile NRT arasındaki çakışmaları gideriyoruz.

Ham seri, seçilen alan ve zamandaki tespitlerin sayısı. Harmonize seri ise ağırlıkların toplamından elde edilen MODIS-eşdeğeri tahmin. Amaç, gözlem sistemi değişiminin uzun dönem karşılaştırmasına etkisini azaltmak.

Başlangıç önerimizde k katsayısı, Arjantin'in 2012–2021 verisindeki MODIS sayısının VIIRS sayısına oranı. VIIRS tespitlerinin ağırlığı için bu katsayı aktif VIIRS uydu sayısına bölünüyor. Bahtiyar'ın nihai yöntemi ve harmonize sayısı henüz bekleniyor. Bu aşamada yöntemi doğrulanmış bir dönüşüm olarak sunmuyoruz. Uyduların etkisinin gerçekten azalıp azalmadığını bağımsız test belirleyecek.”

## 02:00–03:00 · Hohes Venn demosu

[Hazırlık: `Hohes Venn`, `Ham / Raw`, Nisan karşılaştırması için 2001–2025 kapsamı. Alanın P1 sayımıyla eşleştiğini önceden kontrol et.]

“Şimdi Hohes Venn'de Nisan 2011'e bakalım. 25–26 Nisan'daki üç uydu geçişinde 17 MODIS piksel tespiti bulunuyor. Tümü bitki yangını tipinde ve Belçika tarafında. 2001–2025 dönemindeki diğer Nisanların ortalaması 0,67. Nisan 2011 bunun yaklaşık 25 katı ve incelenen dönemin en yüksek Nisanı. Bunu, bilinen yangın olayıyla örtüşen bir tespit artışı olarak anlatıyoruz.

Ardından tarih aralığını 14–17 Ağustos 2026'ya daraltıyoruz. Az önceki MODIS ve VIIRS karşılaştırması bu dört günlük pencereye ait; Ağustos ayının tamamına değil. Kullanıcının hangi bölgeye, hangi döneme ve hangi seri birimine baktığını bilmesi, sayının kendisi kadar önemli.”

[Canlı ekran yoksa aynı anlatımı doğrulanmış sayı kartlarıyla sürdür. Arayüzdeki varsayılan anomali ortalaması farklı bir kapsam kullanırsa 0,67 veya 25 kat iddiasını o karta bağlama.]

[La Rioja geçişi: Son 10 saniyede yalnız gerçek harmonize veri hazır ve önceden kontrol edilmişse `La Rioja (AR)` seçip aynı alan/tarih için ham ↔ harmonize görünümünü göster. Sonuç yoksa bu geçişi atla; iyileşme iddiası kurma. Harmonize sayı: [TBD — Bahtiyar].]

## 03:00–03:30 · Doğrulama

[Ekran: “Bağımsız test 2022–2024 · Sonuç bekleniyor”. Doğrulama metrikleri: [TBD — Oğuzhan].]

“Bir yöntemin işe yaradığını tek bir olay üzerinden söyleyemeyiz. Planlanan bağımsız test dönemimiz 2022–2024. Oğuzhan'ın R kare, yanlılık ve örnek sayısı sonuçları henüz bekleniyor. Eğitimde bulunmayan NOAA-21'in etkisini değerlendirmek için 2022 ile 2023–2024 sonuçlarını ayrı da inceleyeceğiz. Bu metrikler gelene kadar, harmonizasyonun uydu geçişlerinden kaynaklanan sıçramaları giderdiğini iddia etmiyoruz.”

[Sonuç gelirse bu paragrafı yalnız `metrics.json` içindeki `data="harm"` kayıtları ve `summary.md` ile güncelle. Yöntem, bölge, ölçek, test dönemi ve örnek sayısını belirt; sentetik veya yalnız ham veriden üretilmiş metrik kullanma.]

## 03:30–03:55 · Etki ve sonraki adım

[Ekran: “Ham tespit · MODIS-eşdeğeri tahmin · Açık veri kapsamı”.]

“Hedefimiz, uzun dönemli tespit kayıtlarını yorumlarken gözlenen artışla değişen uydu kapsamını birlikte değerlendirebilmek. Sonraki adımımız harmonize çıktıyı ve bağımsız test sonuçlarını birleştirmek, ardından gerçek veriyle kullanıcı testini tamamlamak. Takvim bir inceleme aracı: Her sayıyı bölgesi, zamanı ve gözlem sistemiyle birlikte okuyoruz.”

## Prova kontrolü

- Kronometreyle toplam süreyi ölç; hedef 3:55, üst sınır 4:00. Ölçülen süre: henüz yok.
- Nisan tabanını 2001–2025 ve 2011 hariç olarak koru; “26 yıl” ifadesini kullanma.
- Ağustos penceresini tam ay gibi anlatma; 17 kat oranını dönüşüm katsayısına çevirme.
- P2/P3 sonucu gelmezse bekleyen-sonuç cümlelerini koru. Sentetik ekran görüntüsü yerine doğrulanmış sayı kartı kullan.

## Cloud taslağından korunan 60 saniyelik kanıt anlatımı

Bu kısa alternatif, yukarıdaki 3:55 konuşmaya eklenmez; gerektiğinde kanıt bölümünün yerine kullanılır. Süreler taslaktır, kronometreli prova yapılmadı.

### 00:00–00:25 · Nisan ve veri kapsamı

> Hohes Venn'de 25–26 Nisan 2011'de üç uydu geçişinde 17 MODIS piksel tespiti var. Diğer Nisanların, 2001–2025 içinde 2011 hariç, ortalaması 0,67. Bu, yaklaşık 25 katı ve incelenen dönemin en yüksek Nisanı. Tespitlerin tamamı Belçika tarafında; yalnız Almanya verisini alsaydık bunları göremeyecektik.

### 00:25–00:45 · Ağustos ve gözlem sistemi

> 14–17 Ağustos 2026 olay penceresinde MODIS 105, VIIRS 1.794 tespit veriyor: yaklaşık 17 kat fark. Bu, aynı-geçiş deneyi veya evrensel katsayı değil. Ham sayıları yorumlarken gözlem sistemi farkını da hesaba katmalıyız.

### 00:45–01:00 · Çözüme geçiş

> Amacımız tespitleri ortak bir MODIS-eşdeğeri tahminle karşılaştırmak. Harmonize sayı ve bağımsız test sonuçları bekleniyor; başarıyı ancak bu sonuçlarla değerlendireceğiz.

Hazırlık notu: Harmonize sayı `[TBD — Bahtiyar]`; doğrulama metrikleri `[TBD — Oğuzhan]`. Gerçek veri görselleri kullanılmalı; 17 piksel tespiti yangın olayı sayısına çevrilmemeli.
