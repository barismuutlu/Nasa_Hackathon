# Pitch: doğrulanmış sayılar, tabanlar ve sınırlamalar

P6 İbrahim · 14 Kasım 2026 · Güncel sözleşme v1.3.

## Kaynak ve doğrulama düzeyi

- P1 Süleyman: kullanıcı tarafından iletilen coğrafi filtre, ham sayımlar, Nisan kapsamı ve MCD64A1 kontrolü; ilk referans `7ddfc51`, yeni teslim `26fa38d`. Ağustos harmonize aylık toplamı daha hassas gösterimle 169,2 olarak iletildi.
- P1 son inceleme (`9c8abb9` referanslı mesaj): Nisan geçişleri ve taban tablosu, Ağustos toplamları/harmonize tahmin, MCD64A1 sayıları/tarihleri/duyarlılığı ve La Rioja yıllıkları veriden tek tek kontrol edilmiş; sayısal fark bildirilmemiştir. Bu P1'in kontrol raporudur; P6'nın yerel tekrar hesabı değildir.
- P5 Yusuf: AppTest + query API ile T01–T10 sonuçları; bildirilen uygulama referansı `2bc0e31`. T08 elle, T06 benzetimle test edilmiş. Bu kayıtlar P6'nın yerel tekrar testi değildir; uygulama commit'i veri dosyasının sürümünü tek başına tanımlamaz.
- P4 Barış: `f0f0759` tesliminde tam harmonize veriyle sorgulanan Hohes Venn ve La Rioja sayıları. P2 uygulaması `f44bca1` ile gelmiş.
- P3 Oğuzhan: `b4cbbd4` ile gelen [metrics.json](../validation/metrics.json), [summary.md](../validation/summary.md) ve gerçek veri grafikleri; `c6f15ad` ile MCD64A1 destekleyici özeti eklendi. Aşağıdaki test metrikleri doğrudan JSON kayıtlarından alınmıştır.
- P6 yerel kontrolü: belgeler, JSON ve grafikler incelendi. Tam parquet ve Python 3.12 ortamı bu makinede bulunmadığından sayımlar veya model testleri burada yeniden çalıştırılmadı.

## Coğrafi filtre ve veri kapsamı

Hohes Venn: boylam 5.95–6.25, enlem 50.45–50.60; sınırlar dahil, `query.PRESETS["Hohes Venn"]` ile aynı kutu. İndirme alanı `aachen_eifel`; kutu Belçika tarafını da kapsar. P1/P5'in bildirdiği tam veri kapsamı 2000-11-01 → 2026-11-13, tam harmonize veri 7.082.663 satırdır.

Nisan 2000 veri kapsamı dışındadır. İncelenen Nisanlar 2001–2026: toplam 26 Nisan; 2011 hariç karşılaştırma tabanı 25 Nisan. “26 yıl” yerine bu ay kapsamını açıkça yaz.

## Nisan 2011: aynı 17 tespit, farklı karşılaştırma tabanları

25 Nisan: Terra 9; 26 Nisan: Terra 5 + Aqua 3. Toplam 17 MODIS piksel tespiti, üç geçiş; tümü `type=0` ve Belçika tarafında. Nisan 2011'de MODIS ağırlığı 1 olduğu için harmonize toplam da 17 MODIS-eşdeğeridir. Yalnız Almanya verisi alınsaydı bu tespitler görünmeyecekti.

| Seri / dönem | 2011 değeri | Diğer Nisanların ortalaması | Ortalamanın katı | Sıra |
|---|---:|---:|---:|---|
| Yalnız MODIS, 2001–2025; önceki karşılaştırma | 17 MODIS tespiti | 0,67; 24 referans Nisanı | 25,5×; konuşmada yaklaşık 25× | İncelenen dönemin en yüksek Nisanı |
| Yalnız MODIS, 2001–2026 | 17 MODIS tespiti | 0,64; 25 referans Nisanı | 26,6× | 1/26 |
| Ham, tüm uydular, 2001–2026 | 17 tespit | 2,64; 25 referans Nisanı | 6,4× | 1/26 |
| Harmonize, 2001–2026; ana demo tanımı | 17 MODIS-eşdeğeri | 0,59; 25 referans Nisanı | 28,7×; konuşmada yaklaşık 29× | 1/26 |

Ortalama ve oranlar gösterim için yuvarlatılmıştır; kat değerleri yuvarlanmamış tabanla hesaplanır. Örneğin eski 0,67 gösterimini yeniden bölerek 25,5× sonucunu değiştirme. Kartın ≈29× değeriyle eski MODIS-only ≈25× değerini aynı tabanmış gibi sunma.

P3'ün yeni “0,64, yaklaşık 27 kat” düzeltmesi, tablodaki **yalnız MODIS, 2001–2026** tanımına karşılık gelir; harmonize kartın ≈0,59 / ≈29× tanımının yerine geçirilmez. P1/P4'ün seri ayrımı ve P3 özetinin ayrı `modis` / `harm` satırları bunu ayırır. Taban belirtmeden kullanılabilecek güvenli ifade: “2001–2026'daki 26 Nisan içinde birinci; harmonize seride diğer yıllarda en fazla 3 MODIS-eşdeğeri tespit.”

Ana sunum cümlesi:

> Nisan 2011'de 17 MODIS-eşdeğeri tespit var. 2001–2026'daki diğer 25 Nisanın ortalaması yaklaşık 0,59: bu ay yaklaşık 29 katıyla incelenen 26 Nisanın en yükseği.

Ham kartta yaklaşık 6,4×, harmonize kartta 28,7× görünmesi taban farkıdır; hata değildir. Ham tabanda VIIRS Nisanları da bulunur. Bu değişim “yangın gerçekte beş kat daha şiddetliydi” veya yöntemin tek başına doğrulandığı anlamına gelmez.

## Ağustos 2026: aylık toplam ve olay penceresi

| Ölçü | Değer | Kaynak / kapsam |
|---|---:|---|
| MODIS | 105 piksel tespiti | P1/P5: 14–17 Ağustos; P1 aynı kutuda ayın tüm tespitlerinin bu aralıkta olduğunu bildirdi |
| VIIRS | 1.794 piksel tespiti | Aynı olay penceresi |
| Ham toplam | 1.899 tespit | P4 ve P3: Ağustos ayının tamamı |
| Harmonize toplam | 169,2 MODIS-eşdeğeri; konuşmada yaklaşık 169 | P1 yeni tam veri bildirimi; P4/P3 özeti ve grafiği tam sayıya yuvarlatır |
| Ham VIIRS/MODIS oranı | Yaklaşık 17,1× | 1.794 / 105; evrensel katsayı değildir |

P1'in son teyidi: kutudaki tüm Ağustos aktif tespitleri 14–17 Ağustos'tadır. P4'ün önceki 13–25 Ağustos kontrol aralığı bu dar aralığı içerir. Bunlar MCD64A1 ürününün aşağıda verilen **15–23 Ağustos yanma tarihleriyle aynı tarih alanı değildir**. P6 tarih sınırlarını yerelde tekrar sorgulamadı. Ana demoda 169,2 tahminini aylık birimle etiketle. 14–17 Ağustos seçildiğinde sonuç aynı sayıda olsa da hücre tarih seçimi nedeniyle kısmi ay olarak işaretlenmelidir.

Bu, eşleştirilmiş aynı-geçiş deneyi değildir. Sensör, çözünürlük, uydu sayısı ve gözlem kapsamı ham oranı etkileyebilir. “VIIRS her zaman 17 kat daha hassas” denmez. Yaklaşık 169 tahmin, 105 MODIS referansının yaklaşık %61 üzerindedir; bu olayda tam eşleşme veya kusursuz düzeltme iddia edilmez.

## MCD64A1 yanmış alan: destekleyici kanıt

Kaynak: P1'in `26fa38d` referanslı mesajı; `pipeline/burned_area_check.py` yöntem açıklaması; P3'ün `c6f15ad` ile güncellenen `summary.md` içindeki destekleyici tablo. Ayrı çıktı `data/burned_area_check.csv`; bu CSV P6 makinesinde yeniden çalıştırılmadı ve git'e eklenmedi.

Görsel ve slayt kaynak adı: **NASA MCD64A1 C6.1** (aylık yanmış alan, yaklaşık 500 m). P3'ün yenilenmiş [venn_check.png](../validation/venn_check.png) grafiğinde bu destekleyici sayımlar alt not olarak bulunur; P6 grafiği değiştirmez.

Eşleştirme ayarı: tespitin düştüğü MCD64A1 pikseli ve çevresinde **3×3 piksel komşuluğu (yaklaşık 1,4 km genişlik)**; aktif tespit tarihi ile ürünün yanma tarihi arasında **±16 gün**. Bu yaklaşık mesafe bir dairesel yarıçap veya kesin yangın sınırı değildir.

| Dönem / enstrüman | Eşleşen / toplam aktif tespit | MCD64A1 ürününde bildirilen yanma tarihleri |
|---|---:|---|
| Nisan 2011 / MODIS | 9/17 (%53) | 24–28 Nisan 2011 |
| Ağustos 2026 / MODIS | 93/105 (%89) | 15–23 Ağustos 2026 |
| Ağustos 2026 / VIIRS | 1.674/1.794 (%93) | 15–23 Ağustos 2026 |

Sunum cümlesi:

> Nisan 2011'deki 17 MODIS tespitinin 9'u, 3×3 piksel komşuluğunda (yaklaşık 1,4 km), NASA'nın MCD64A1 ürününün 24–28 Nisan'da yanmış işaretlediği alanlarla örtüşüyor. Bu destekleyici kanıttır; bağımsız doğrulama değildir.

MCD64A1 algoritması MODIS aktif yangın verisini de kullanır; küçük yanıkları kaçırabilir. “Doğrulandı” veya “kanıtlandı” denmez. Nisan eşleşmesi ayara bağlıdır: tek pikselde 5/17, 3×3'te 9/17, 5×5'te 15/17 (P1 bildirimi; zaman toleransı ±16 gün). P1'in son konum açıklamasına göre kalan 8 tespit, eşleşenlerin güney/doğu çevresindedir; 5×5 komşulukta bu 8 tespitin 6'sı daha eşleşir. Yanık sınırı haritasıyla ölçüm yapılmadığından bunlar “yanık kenarında” diye tanımlanmaz. Eşleşmeme, yanlış aktif tespit kanıtı değildir. `unknown` / `no_data`, “yanmamış” ile aynı değildir. Bu örtüşme oranları bağımsız sınıflandırma doğruluğu veya harmonizasyon test metriği olarak sunulmaz.

Eski Belçika ülke-yıl dosyasındaki 17 satırla yeni DL_FIRE çıktısının aynı olması, P1'in bildirdiği **iki FIRMS indirmesi arasında tutarlılık kontrolüdür**; bağımsız sensör veya yangın olayı doğrulaması değildir.

## La Rioja: yıllık örnekler

P4'ün tam veri `query.py` sorgusundan ilettiği sonuçlar:

| Yıl | Ham, tüm uydular | Harmonize, MODIS-eşdeğeri | Yalnız MODIS referansı |
|---|---:|---:|---:|
| 2011 | 868 | 868 | 868 |
| 2012 | 3.437 | 808 | 731 |
| 2018 | 7.240 | 931 | 1.057 |
| 2023 | 10.728 | 985 | 907 |

2012'de ham seri yaklaşık dört katına çıkarken harmonize değer 868'den 808'e gelir. Bu görsel örnek bağımsız test metriği yerine geçmez. Sınırlama: 2017'de harmonize 3.236, MODIS 2.447; tahmin referansın yaklaşık %32 üzerindedir.

## P3: bağımsız test sonuçları

Kaynak `docs/validation/metrics.json`, commit `b4cbbd4`. Aşağıdaki bütün satırlarda `data="harm"`, ölçek `1deg`. Hedef MODIS tespit sayısıdır; doğrulanmış yangın sayısı değildir. `n` hücre-ay örnek sayısıdır. `bias` tespit/hücre-ay biriminde, `bias_pct` toplam göreli sapmadır.

| Bölge | Yöntem | Split / dönem | R² | Bias | Bias % | n |
|---|---|---|---:|---:|---:|---:|
| argentina | harm | test / 2022–2024 | 0,7918 | +1,3674 | +6,72 | 8.616 |
| argentina | raw_viirs | test / 2022–2024 | -74,8202 | +159,8763 | +785,90 | 8.616 |
| argentina | harm | test_2022 / 2022 | 0,7052 | +5,0232 | +18,36 | 2.834 |
| argentina | harm | test_2023-2024 / 2023–2024 | 0,9291 | -0,4244 | -2,51 | 5.782 |

Eğitim bölgesi Arjantin, VIIRS katsayıları için dönem 2012–2021; P2/P3 teyidine göre 2022–2024 katsayılara girmemiştir. Terra-only erken dönem düzeltmesi için ayrı 2003–2011 eğitim aralığı kullanılır. NOAA-21 için eğitimde doğrudan örnek yok; yöntemde NOAA-20 katsayıları vekil olarak kullanılır.

Ana test cümlesi: “Arjantin'de 2022–2024 bağımsız testinde, 1° hücre-ay ölçeğinde R² yaklaşık 0,79; toplam sapma +%6,72; n=8.616.” 2022'deki +%18,36 fazla tahmini saklama. P3'ün son yönlendirmesi gereği Aachen/Eifel 2022–2024 test R²'si pitch'te kullanılmaz: bu dönemde yalnız 7 MODIS tespiti vardır ve örneklem yetersizdir.

`summary.md` ve `pred_vs_true.png` ayrıca `transfer_2012-2026` sonuçları içeriyor. Bu split mevcut sözleşmenin izinli değerlerinde ve `metrics.json` içinde yok; P3 özeti P4 onayının beklendiğini belirtiyor. Bu nedenle aktarım R²'si ana sunuma alınmaz; iki panelli `pred_vs_true.png` bütün olarak sunuma hazır sayılmaz.

Sınırlama slaytı [slides/limitations.md](slides/limitations.md) içindedir. P3 mesajındaki yıllık belirsizlik bandı için mevcut JSON'da ayrı bir hesap/yöntem kaydı bulunmadığından bu bant slayta sayısal sonuç olarak eklenmedi.

## Veri ve yöntem kuralları

Girdiler yalnız FIRMS DL_FIRE archive/NRT; indirme alanları `argentina` ve `aachen_eifel`. Eski ülke-yıl CSV dosyaları kapsam dışıdır. Yöntem A uygulaması enlem bandı, yerel mevsim ve uydu için MODIS/VIIRS katsayılarını aktif VIIRS uydu sayısına böler; `Σ weight_harm` MODIS-eşdeğeri tahmindir. Bölge ve olay aktarımı sınırlıdır; uydu etkisinin tamamen giderildiği söylenmez.

Bir piksel tespiti yangın olayı değildir; üç geçiş üç yangın anlamına gelmez. FIRMS bitki yangını tipi bağımsız olay doğrulaması değildir. Anomali etiketi tespit sayısına ilişkindir. Sentetik ekran görüntüsü ve NASA logosu kullanılmaz.

## Tekrar üretim ve görseller

Python 3.12 + sabit `requirements.txt` ortamı etkin ve gerçek harmonize veri hazırken, repo kökünde:

~~~powershell
python -c "import sys; sys.path.insert(0,'app'); import query; v=query.get_hotspots('Hohes Venn'); [print(m, query.anomaly(query.monthly_matrix(v,m),2011,4)) for m in ('raw','harm')]"
~~~

Beklenen, P1/P4 bildirimi: raw value=17, mean≈2,64, rank=1, n_years=26; harm value=17, mean≈0,59, rank=1, n_years=26. Bu komut burada çalıştırılmadı.

Gerçek veri P3 takvimi [venn_check.png](../validation/venn_check.png) yerelde görsel olarak incelendi. Canlı Cloud ekran görüntüleri ve prova henüz P6 tarafından tamamlanmadı; akış [demo.md](demo.md), durum [test_notes.md](test_notes.md) içinde. Tarihsel 144 CSV manifesti ve cloud ortam raporu [data_handoff.md](data_handoff.md) ile [environment_check.md](environment_check.md) içinde korunur; güncel pipeline/test kanıtı yerine kullanılmaz.
