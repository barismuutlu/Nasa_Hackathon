# Pitch için doğrulanmış bilgiler ve bekleyen sonuçlar

P6 İbrahim · 14 Kasım 2026 · Yerel çalışma notu.

## Kaynak ve kapsam

Bu belgedeki olay sayımları, Süleyman'ın `data/hotspots.parquet` üzerinden doğruladığı ve kullanıcının bu oturumda ilettiği sonuçlardır. Yerelde yeniden hesaplanmadı. İlk incelemede `data/hotspots.parquet`, harmonize veri ve P3 metrik dosyaları bulunmadı. Ayrı cloud oturumundaki dosyalar veya commit'ler bu çalışmanın kaynağı değildir.

Kurallar: [CLAUDE.md](../../CLAUDE.md), [CONTRACT.md](../CONTRACT.md) ve [P6 rolü](../../ekip/P6_Ibrahim.CLAUDE.md). Yerel sözleşme v1.3'tür; v1.2'nin DL_FIRE ve ülke-yıl dosyalarını dışlama kuralları korunur.

## Kullanılabilir sayılar

| Konu | Doğrulanmış bilgi | Sunumda kullanılacak ifade |
|---|---|---|
| Hohes Venn, Nisan 2011 | 17 MODIS piksel tespiti; tespit tarihleri 25–26 Nisan; üç uydu geçişi | “Nisan 2011'de, üç geçişte 17 MODIS piksel tespiti.” |
| Nisan 2011 tipi ve konumu | 17 tespitin tümü bitki yangını tipinde ve Belçika tarafında | “Bilinen yangın olayıyla örtüşen tespit artışı.” |
| Nisan karşılaştırması | 2001–2025 içindeki diğer Nisanların ortalaması 0,67; 2011 hariç | “Nisan 2011, diğer Nisanların ortalamasının yaklaşık 25 katı.” |
| Nisan sıralaması | İncelenen dönemin en yüksek Nisanı | “İncelenen dönemin en yüksek Nisanı.” |
| Hohes Venn, 14–17 Ağustos 2026 | 105 MODIS ve 1.794 VIIRS tespiti; aynı olay penceresi | “Aynı olay penceresinde yaklaşık 17 kat VIIRS tespiti.” |
| Harmonize sayı | [TBD — Bahtiyar] | “Harmonize (MODIS-eşdeğeri) tahmin: [TBD — Bahtiyar].” |
| Doğrulama metrikleri | [TBD — Oğuzhan] | “2022–2024 bağımsız test metrikleri: [TBD — Oğuzhan].” |

Türkçe metinlerde `1.794` binlik, `0,67` ondalık gösterimdir. Tarih filtreleri sözleşmeye göre UTC ve başlangıç/bitiş günleri dahildir.

## Sayıların kullanım sınırları

- Bir piksel tespiti bir yangın olayı değildir. Farklı zamanlardaki geçişler ve komşu pikseller aynı olay için ayrı kayıtlar üretebilir. “17 yangın” veya “1.794 yangın” denmez.
- Yaklaşık 25 kat karşılaştırması `17 / 0,67` oranıdır; yuvarlanmış ortalamaya dayanır. Karşılaştırma tabanı yalnızca 2001–2025'in 2011 dışındaki Nisanlarıdır. “26 yılın en yükseği” ifadesi teyit bekliyor ve bu taslaklarda sonuç olarak kullanılmıyor.
- Yaklaşık 17 kat karşılaştırması `1.794 / 105` oranıdır. Tek olay penceresinin ham VIIRS/MODIS oranı, tüm dönemlere veya bölgelere uygulanabilecek bir katsayı değildir; bunun tersi de kendiliğinden doğrulanmış bir dönüşüm vermez.
- 14–17 Ağustos sayıları ayın tamamını kapsamaz. Takvimin bu tarihlere daraltılmış Ağustos hücresi kısmi aydır; tam Ağustos toplamı olarak etiketlenmez.
- Nisan 2011'deki bitki yangını tipi ve Belçika konumu bilgisi Ağustos 2026 kayıtlarına genellenmez. NRT kayıtlarında `type` boş olabilir.
- Uygulamadaki ortalama ve sıra, sorgunun dönemine ve sensör kapsamına bağlıdır. Arayüzün varsayılan tabanı Süleyman'ın 2001–2025 karşılaştırmasıyla eşleşmeden “25 kat” veya sabit bir sıra paydası beklenmez.
- Uyduların farklı gözlem özellikleri ham karşılaştırmayı etkiler; tek örnek hangi etkenin ne kadar katkı yaptığını ölçmez. “Uydu sıçramaları tamamen giderildi” sonucu P3 kanıtı gelmeden kullanılmaz.

## Veri ve yöntem çerçevesi

Girdiler `data/raw/argentina/` ve `data/raw/aachen_eifel/` altındaki FIRMS DL_FIRE archive/NRT dosyalarıdır. Eski ülke-yıl CSV dosyaları dışlanır. `aachen_eifel` indirme kutusu Belçika tarafını da içerir; ülke sınırı filtresi değildir.

Şema bir termal anomali pikseli için bir satır tutar. Archive/NRT çakışması `(region, satellite)` bazında archive bitiş tarihiyle giderilir. Ham tespit sayısı satır sayısıdır; harmonize sayı `Σ weight_harm` ile elde edilen MODIS-eşdeğeri tahmindir. Ingest aşamasındaki boş ağırlık, harmonizasyon yapılmadığını gösterir; sıfır tahmin anlamına gelmez.

Sözleşmedeki Yöntem A başlangıç önerisinde `k = MODIS / VIIRS` oranı Arjantin 2012–2021 verisinden hesaplanır; VIIRS satır ağırlığı `k / aktif_VIIRS_uydu_sayısı` olur. Bu öneride MODIS satır ağırlığı VIIRS dönemi öncesinde 1, sonrasında 0'dır. Aktif uydu hesabında başlangıç ve bitiş tarihleri dikkate alınır. Nihai yöntemi Bahtiyar belirler. Bu önerinin uygulandığı veya doğrulandığı varsayılmaz. Eğitim 2012–2021, bağımsız test 2022–2024 olarak planlanmıştır; NOAA-21'in eğitimde bulunmaması ayrı test alt dönemleriyle değerlendirilir.

## Tamamlanması gereken kanıtlar

| Beklenen girdi | Sorumlu | Kabul koşulu |
|---|---|---|
| Sayımların tam coğrafi filtresi ve tekrar üretim adımları | Süleyman | Aynı alan, tarihler, sensörler ve Nisan karşılaştırma tabanı belgelenmeli; uygulamadaki `Hohes Venn` seçimiyle eşleşmeli. |
| “26 yıl” ifadesinin kapsamı | Süleyman | Tam veri kapsamı ve karşılaştırmaya dahil Nisanlar teyit edilmeli; o zamana kadar “incelenen dönemin en yüksek Nisanı” korunmalı. |
| Harmonize sayı ve yöntem | Bahtiyar | [TBD — Bahtiyar]; sayı yanında bölge, tarih aralığı, yöntem ve MODIS-eşdeğeri birim bulunmalı. |
| `docs/validation/metrics.json` ve `summary.md` | Oğuzhan | [TBD — Oğuzhan]; v1.3 §7.3'e uygun `data="harm"` çıktıları olmalı. Ana harmonize test sonucu için `method="harm"`, `split="test"`; ayrıca `test_2022` ve `test_2023-2024` sonuçları kontrol edilmeli. |
| Gerçek veri ekran görüntüleri ve aynı gün/alan MODIS–VIIRS Worldview karşılaştırması | İbrahim | Henüz hazırlanmadı; tarih, alan, katman/uydu ve kaynak kaydedilmeli. NASA logosu ve sentetik ekran görüntüsü kullanılmamalı. |
| Gerçek veriyle kullanıcı testi | İbrahim | [test_notes.md](test_notes.md) içindeki bekleyen senaryolar çalıştırılmalı; gözlenen sonuç ve kanıt yazılmalı. |

R², bias, bias yüzdesi ve `n` yalnız `metrics.json` içindeki uygun kayıtlardan alınır; yöntem, bölge, test dönemi ve ölçekle birlikte sunulur. `data="mock"` veya `data="raw"` metrikleri sunuma alınmaz. `raw_viirs` sonucu kullanılırsa harmonize sonuçtan ayrı bir karşılaştırma olarak etiketlenir. Metrik veya grafik dosyasının yalnız var olması, sunuma uygun olduğunun kanıtı değildir.
