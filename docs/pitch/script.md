# Yaklaşık dört dakikalık konuşma

P6 İbrahim · 14 Kasım 2026. Hedef 3:55; kronometreli prova henüz yapılmadı. Kaynak ve tam metrikler: [pitch_facts.md](pitch_facts.md); tıklama akışı: [demo.md](demo.md).

Sunucu notu: Köşeli parantezler sesli okunmaz. Ekranlar bu oturumda çekilmedi. Canlı demo için gerçek ve harmonize veri durumunu önceden kontrol et. Görüntü yoksa doğrulanmış sayı kartları ve P3'ün gerçek veri takvimiyle devam et; sentetik ekran kullanma.

## 00:00–00:30 · Sorun

[Ekran: “Tespit sayısı neden değişiyor?”]

“Bir bölgede uydu tespitleri artıyorsa, bunu nasıl yorumlarız? Gözlenen olaylar değişmiş olabilir; fakat gözlem yapan uydular da değişiyor. MODIS ve VIIRS farklı çözünürlüklere ve gözlem kapsamlarına sahip. Yeni uydular katıldığında ham tespit sayısını geçmiş yıllarla doğrudan karşılaştırmak yanıltıcı olabilir. Biz bu uzun kaydı, uydu kapsamını hesaba katarak okumak istiyoruz.”

## 00:30–01:00 · Aynı olay, farklı sayılar

[Ekran: Hohes Venn, Ağustos 2026; ham 1.899, harmonize yaklaşık 169.]

“Ağustos 2026'da Hohes Venn'de 105 MODIS ve 1.794 VIIRS tespiti var. Ham toplam 1.899; VIIRS sayısı MODIS'in yaklaşık 17 katı. Bunlar piksel tespitleri, yangın olayı sayısı değil. Bu tek örneğin oranı evrensel katsayı da değil. Harmonize aylık tahmin yaklaşık 169 MODIS-eşdeğeri; bu değer de 105 MODIS referansıyla tam eşleşmiyor.”

## 01:00–01:50 · Yöntem

[Ekran: DL_FIRE → ortak şema → ham / MODIS-eşdeğeri takvim.]

“Girdilerimiz FIRMS DL_FIRE archive ve NRT kayıtları. Arjantin ve Aachen/Eifel alanlarında tekrarları ve kaynak çakışmalarını ortak kurallarla ele alıyoruz. Her kayıt bir uydu geçişindeki termal anomali pikseli.

Bahtiyar'ın Yöntem A uygulaması, Arjantin'in 2012–2021 verisinden MODIS ile VIIRS arasındaki oranları öğreniyor. Katsayılar enlem bandı, yerel mevsim ve uyduya göre değişiyor; aktif VIIRS uydu sayısı da ağırlığa giriyor. Bu ağırlıkların toplamı MODIS-eşdeğeri tahmini veriyor.

Ham seriyi de koruyoruz. Böylece kullanıcı hem gözlenen kayıt sayısını hem ortak birime dönüştürülmüş tahmini görebiliyor. Dönüşümün ne kadar işe yaradığını, eğitimde kullanılmayan 2022–2024 yıllarında MODIS referansına karşı değerlendiriyoruz. Bu yöntem doğrulanmış yangın olayı sayısı üretmiyor.”

## 01:50–03:00 · Demo: Nisan 2011 ve La Rioja

[Hohes Venn → tüm veri dönemi → Harmonize → Log → 2011-04. Dar tarih filtresi kullanma; 26 Nisanlık taban korunmalı.]

“Nisan 2011'e bakalım. 25–26 Nisan'daki üç geçişte 17 MODIS piksel tespiti var; hepsi Belçika tarafında. Harmonize toplam da 17. 2001–2026'daki diğer 25 Nisanın harmonize ortalaması yaklaşık 0,59. Bu ay yaklaşık 29 katıyla incelenen 26 Nisanın en yükseği.

Ham seriye geçince değer yine 17, fakat kartın karşılaştırma ortalaması 2,64; oran yaklaşık 6,4 kat. Çünkü ham tabanda VIIRS döneminin tespitleri de var. Aynı ayı yorumlarken hangi seriyi ve tabanı kullandığımızı belirtmek bu yüzden önemli.

Ek destek olarak, 17 tespitin 9'u MCD64A1'in 24–28 Nisan'da yanmış işaretlediği alanlarla, yaklaşık 1,4 kilometrelik komşulukta örtüşüyor. Bu bağımsız doğrulama değil; ürün MODIS aktif yangın verisini de kullanıyor.

La Rioja'da yıllık ham toplam 2011'de 868'den 2012'de 3.437'ye çıkıyor; harmonize seri 868'den 808'e geliyor. Bu örnek faydalı, ancak her yıl kusursuz eşleşme demek değil.”

[La Rioja (AR), tüm tarih kapsamı, yıllık ham/harmonize grafik. Ekran hazır değilse sayı kartını kullan. Gerektiğinde 2017 sınırlamasını açıkla: 3.236 tahmin, 2.447 MODIS; yaklaşık %32 fazla.]

[MCD64A1 çerçevesi: kaynak “NASA MCD64A1 C6.1”; yalnız “destekleyici kanıt” de. 3×3 piksel ≈1,4 km genişlik; ±16 gün eşleştirme. P1: tek piksel 5/17, 3×3 9/17 (%53), 5×5 15/17. Ağustos: MODIS 93/105 (%89), VIIRS 1.674/1.794 (%93); ürün yanma tarihleri 15–23 Ağustos. Bunları aktif tespitlerin 14–17 Ağustos tarihleriyle karıştırma. Örtüşmeyi R²/bias veya bağımsız doğrulama metriği olarak sunma.]

## 03:00–03:30 · Bağımsız test ve sınır

[Ekran: Arjantin, 2022–2024, harm, 1° hücre-ay; R²=0,7918, bias=+1,3674 tespit/hücre-ay, bias %=+6,72, n=8.616.]

“Oğuzhan'ın bağımsız testinde, Arjantin'de bir derecelik hücre-ay ölçeğinde R kare yaklaşık 0,79; toplam sapma artı yüzde 6,72. Örnek sayısı 8.616 hücre-ay. 2022 tek başına değerlendirildiğinde fazla tahmin yüzde 18,36. Aachen/Eifel'de örneklem küçük ve büyük olayda fazla tahmin var. Bu nedenle uydu etkisini tamamen giderdiğimizi veya her bölgeye aynı başarıyla aktardığımızı söylemiyoruz.”

[Kaynak: docs/validation/metrics.json, b4cbbd4; ana kayıt data=harm, method=harm, region=argentina, split=test, scale=1deg. “R²=0,79” değeri Avrupa aktarım sonucuyla karıştırılmamalı.]

## 03:30–03:55 · Etki

[Ekran: “Ham tespit · MODIS-eşdeğeri tahmin · Açık kapsam”.]

“Hedefimiz, uzun dönemli uydu kayıtlarını yorumlarken tespit sayısını gözlem sistemiyle birlikte değerlendirmek. Takvim iki seriyi ve karşılaştırma tabanını görünür kılıyor. Sonraki adımımız büyük olaylara ve farklı bölgelere aktarımı geliştirmek. Her sayıyı bölgesi, zamanı, birimi ve sınırlamalarıyla birlikte sunuyoruz.”

## Alternatif 60 saniyelik kanıt anlatımı

Bu alternatif ana konuşmaya eklenmez; gerektiğinde kanıt/demo bölümünün yerine geçer. Süreler henüz ölçülmedi.

> Nisan 2011'de Hohes Venn'de üç geçişte 17 MODIS piksel tespiti var; hepsi Belçika tarafında. Harmonize toplam da 17. 2001–2026'daki diğer 25 Nisanın harmonize ortalaması yaklaşık 0,59: bu ay yaklaşık 29 katıyla 26 Nisanın en yükseği. Ham kartta ise farklı taban nedeniyle yaklaşık 6,4 kat görünüyor.
>
> Ağustos 2026'da 105 MODIS ve 1.794 VIIRS tespiti var; yaklaşık 17 kat ham fark evrensel katsayı değil. Harmonize aylık tahmin yaklaşık 169 MODIS-eşdeğeri. Arjantin'in 2022–2024 testinde, 1° hücre-ay ölçeğinde R² yaklaşık 0,79 ve toplam sapma +%6,72. Yöntem yararlı karşılaştırmalar sağlıyor; büyük olaylara aktarımda fazla tahmin sınırı sürüyor.

## Prova kontrolü

- Tam süre hedefi 3:55, üst sınır 4:00; ölçülen süre henüz yok.
- Nisan kartında Harmonize, tüm tarih kapsamı ve 1/26 görünmeli. Gösterimde 28,7× için “yaklaşık 29 kat” denmeli.
- Eski yaklaşık 25 katı yalnız MODIS 2001–2025 karşılaştırması olarak anlat.
- P3'ün ≈27× düzeltmesi MODIS-only 2001–2026 tabanıdır; harmonize kartın ≈29× değeriyle karıştırma. Tabanı açıklamayacaksan “incelenen 26 Nisanın en yükseği; diğer yıllarda en fazla 3” de.
- Ağustos 169 değerini aylık MODIS-eşdeğeri tahmin diye etiketle; 14–17 seçilirse kısmi ay işaretini koru.
- P1'in hassas aylık değeri 169,2; konuşma ve P3 grafiğindeki 169 bunun yuvarlatılmış gösterimidir.
- Arjantin test metriğini Aachen/Eifel başarısı olarak sunma. P3 grafiğindeki onay bekleyen aktarım panelini sunum sonucu olarak kullanma.
- Gerçek ekran görüntüsü, çevrimdışı video ve kronometreli prova henüz tamamlanmadı.
