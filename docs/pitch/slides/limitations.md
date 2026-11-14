# Slayt: Sınırlamalar ve sonraki adım

P6 İbrahim · 14 Kasım 2026. Gerçek veri kaynakları: P3 `metrics.json` (`b4cbbd4`), `summary.md` (`c6f15ad`) ve P1/P4 teslimleri. Bu dosya slayt metnidir; tamamlanmış sunum dosyası değildir.

## Ekranda gösterilecek üç madde

1. **2022 fazla tahmini:** Arjantin, 2022 bağımsız test, 1° hücre-ay: toplam sapma **+%18,36**; R²=0,7052, n=2.834. Aynı ölçekte 2023–2024 sapması −%2,51'dir; bir yılın hatası genel ortalama içinde saklanmamalı.
2. **Bölge ve büyük olay aktarımı sınırlı:** Hohes Venn Ağustos 2026 tahmini **169,2 MODIS-eşdeğeri**, MODIS referansı 105; yaklaşık **+%61**. Aachen/Eifel 2022–2024'te yalnız 7 MODIS tespiti var; bu bölgenin test R²'sini başarı iddiası için kullanmıyoruz. La Rioja 2017'de de yaklaşık +%32 fazla tahmin var.
3. **Sonraki adım — sınanacak hipotez:** Katsayı yangın büyüklüğüne bağlı olabilir; bu henüz doğrulanmadı. Tespit kümelerinin alanı / toplam FRP ile koşullama ve Avrupa'dan ikinci eğitim bölgesi değerlendirilmeli.

## Konuşmacı notları

- 2022 sapmasını tek başına S-NPP/Aqua kesintisine veya yörünge kaymasına bağlama; P3 özeti bunu açıklayıcı sonuç olarak desteklemiyor.
- `transfer_2012-2026` ve büyük olay hariç aktarım R² sonuçları mevcut `metrics.json` içinde değil; P4 onayı ve sözleşmeye uygun kayıt bekleniyor. Bu slaytta bunların sayısal R² değerlerini kullanma.
- P3 mesajındaki yıllık belirsizlik bandı için JSON'da ayrı hesap/yöntem kaydı yok; sayısal bant bu slayta eklenmedi.
- Kaynak **NASA MCD64A1 C6.1**. Örtüşme yalnız **destekleyici kanıt**: 3×3 piksel komşuluğu ≈1,4 km genişlik, ±16 gün; Nisan 9/17 (%53), Ağustos MODIS 93/105 (%89), VIIRS 1.674/1.794 (%93). Ürün MODIS aktif yangın girdisini de kullanır; bağımsız doğrulama veya olay sınıflandırma doğruluğu değildir. R²/bias tablosuna eklenmez.
- Her R²'nin yanında bölge, test dönemi, ölçek ve n bulunmalı. “Gerçek yangın sayısı” ve “uydu sıçramaları tamamen giderildi” ifadeleri kullanılmaz.
