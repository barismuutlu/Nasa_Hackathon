# Demo akışı ve gerçek veri çekim planı

P6 İbrahim · 14 Kasım 2026. Durum: akış hazır; P6 canlı ekran kontrolü, kayıt ve kronometreli prova henüz yapılmadı.

Ekipten bildirilen public URL: https://nasahackathon-6dh2dds5wpz3r6q9mz5zx3.streamlit.app/

## Başlamadan önce

- Gizli pencerede giriş istemeden açıldığını tekrar kontrol et. Bu oturumdaki web aracı URL'yi açamadı; bu sonuç sitenin kullanıcıya kapalı olduğu anlamına gelmez.
- `Veri / Data` bölümündeki kaynak, kapsam ve uyduları kaydet. Son P4 bildirimi `f0f0759`: gerçek + harmonize deploy. Eski sentetik veya harmonizesiz teslim mesajları son durum yerine kullanılmaz.
- Sentetik uyarı varsa o ekranı sunuma alma. Harmonize hazır-değil mesajı varsa akışı ham veriyle sürdürdüğünü belirt ve önceden doğrulanmış P3 takvimini kullan.
- Hazır bölgeyi seç, önceki çizimi temizle. Deploy yalnız hazır kutuları kapsar; dışındaki tespitsiz görünümü bölgenin gerçekten hiç tespiti olmadığı şeklinde genelleme.
- Nisan kartı ve yıllık karşılaştırmalar için tam veri dönemini koru. Yalnız 2011-04 filtresi, kartın 26 Nisanlık karşılaştırma tabanını bozar.

## Yaklaşık 60 saniyelik canlı akış

| Süre | İşlem | Beklenen / konuşma |
|---|---|---|
| 00–10 sn | `Bölge: Hohes Venn` → tam tarih kapsamı → `Harmonize / Harmonized` → `Log` | Gerçek veri; aylık birim MODIS-eşdeğeri tahmin. Log renk dönüşümü karttaki sayıyı değiştirmez. |
| 10–25 sn | 2011-04 hücresini seç; gerekirse Yıl/Ay seçicilerini kullan. | 17 MODIS-eşdeğeri; sıra 1/26; yaklaşık 28,7× (yuvarlatılmış gösterim 29× olabilir). Diğer 25 Nisanın ortalaması ≈0,59. |
| 25–35 sn | Aynı kapsam ve ayda `Ham / Raw` seç; sonra Harmonize'ye dön. | Değer yine 17; ham ortalama 2,64 ve oran ≈6,4×. Bu, farklı tabanların karşılaştırmasıdır. Eski ≈25× sayısı kartın tanımı değildir. |
| 35–45 sn | Hohes Venn 2026-08 hücresini göster; tam ayı koru. | Ham 1.899 = 105 MODIS + 1.794 VIIRS; harmonize ≈169 MODIS-eşdeğeri. 169, MODIS referansına eşit değildir. |
| 45–60 sn | `La Rioja (AR)` seç; tam tarih aralığında `Yıllık toplam: Ham vs Harmonize` grafiğine geç. | 2011: 868/868; 2012: 3.437/808 (ham/harm). Canlı akış uzarsa bu geçişi önceden alınmış gerçek veri karesiyle göster. |

Ayrı ayrıntı kontrolü: 14–17 Ağustos seçilirse P1/P5 raporuna göre ham toplam yine 1.899'dur; hücre • ile kısmi ay ve hover'da gün aralığı göstermelidir. Bu dar filtreyi ana Nisan kartı provasıyla aynı anda kullanma; sonra tam dönemi geri yükle.

P1'in hassas aylık harmonize değeri 169,2'dir; grafikte/konuşmada 169'a yuvarlatılır. MCD64A1 sorulursa Nisan 9/17 örtüşmesini 3×3 komşuluk ≈1,4 km genişlik ve ±16 gün ayarıyla **destekleyici kanıt** diye anlat; bağımsız olmadığını ekle. Ürünün yanma tarihleri ile FIRMS aktif tespit tarihlerini ayır. Slayt metni [slides/limitations.md](slides/limitations.md), tam kapsam [pitch_facts.md](pitch_facts.md) içinde.

## Çekilecek kareler

Bunlar planlanan dosya adlarıdır; henüz oluşturulmadı. Çekim tarihi 14 Kasım 2026 varsayılmıştır; gerçek çekim günü farklıysa dosya adını güncelle.

| Planlanan dosya | İçerik | Kontrol |
|---|---|---|
| `img/2026-11-14_harm_HohesVenn_calendar.png` | Hohes Venn, tam dönem, Harmonize, Log takvim | Sentetik uyarı yok; bölge ve seri görünür |
| `img/2026-11-14_harm_HohesVenn_2011-04_card.png` | Nisan kartı | 17; 1/26; ≈29×; taban 2001–2026, 2011 hariç |
| `img/2026-11-14_raw_HohesVenn_2011-04_card.png` | Aynı ayın ham kartı | 17; 1/26; ≈6,4×; aynı tarih/alan |
| `img/2026-11-14_raw_harm_LaRioja_annual.png` | La Rioja yıllık karşılaştırma | Ham/harm birimleri, bölge ve 2011/2012 değerleri açık |

Görüntü alındığında kaynak yolu, veri sürümü/commit, tarih kapsamı, bölge, seri ve çekim tarihini `img/SOURCES.md` içine kaydet. Kaynak: “NASA FIRMS / Worldview”; uygulama görseliyse uygulama URL'sini de ekle. NASA logosu kullanma. Bu uygulama kareleri, aynı gün/aynı alan MODIS–VIIRS Worldview katman karşılaştırmasının yerine geçmez; o görsel ayrıca bekleniyor.

## İnternet veya canlı veri sorunu olursa

- Öncelik, önceden alınmış gerçek uygulama ekranları ve çevrimdışı video. Bunlar henüz yok; varmış gibi sunma.
- Mevcut gerçek veri [P3 Hohes Venn takvimi](../validation/venn_check.png), 17/1.899 ham ve 17/169 harmonize aylık değerleriyle destek sağlar. Bunun uygulama ekranı olmadığını söyle.
- [P3 yıllık grafik](../validation/annual_raw_vs_harm.png) **Arjantin** içindir; La Rioja ekranının yerine kullanılırsa bölgenin değiştiğini açıkça belirt.
- `pred_vs_true.png` içindeki Avrupa aktarım paneli henüz izinli JSON metriğiyle eşleşmediğinden tam görseli sonuç slaydı olarak kullanma. Arjantin bağımsız testini `pitch_facts.md` içindeki sayısal tabloyla anlat.
- P3 grafikleri de açılamazsa kaynaklı sayı kartlarıyla konuşmayı sürdür; yeni sayılar üretme.

## Prova ve teslim kaydı

| Kontrol | Sonuç |
|---|---|
| P6 public/gizli pencere canlı kontrolü | Bekliyor |
| Gerçek uygulama kareleri ve kaynak notları | Bekliyor |
| Video kaydı ve çevrimdışı oynatma | Bekliyor |
| Tam konuşma ölçümü, hedef 3:55 / üst sınır 4:00 | Henüz ölçülmedi |

Testlerin kanıt ve gözlem kaynakları [test_notes.md](test_notes.md), konuşma [script.md](script.md), sayısal kapsam [pitch_facts.md](pitch_facts.md) içindedir.
