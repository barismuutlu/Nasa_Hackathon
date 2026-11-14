🔥 SPACE APPS 2026 – GÖREV DAĞILIMI 🛰️
Lider: P4 Barış (entegrasyon + hızlı kararlar)

━━━━━━━━━━━━━━━━━━
🟦 VERİ & BİLİM EKİBİ
━━━━━━━━━━━━━━━━━━

P1 – Veri Mühendisi: SÜLEYMAN
📁 pipeline/ingest.py
* FIRMS CSV'leri oku (MODIS + VIIRS S-NPP/N20/N21)
* archive + nrt birleştir, tekrarları sil (çakışmada archive kalır)
* Ortak şemaya çevir → data/hotspots.parquet
⏰ 11:30 örnek dosya (1 bölge, 1 yıl) → herkese
⏰ 12:30 tam veri + uydu ilk/son tarih tablosu → Bahtiyar

P2 – Harmonizasyon: BAHTİYAR
📁 pipeline/harmonize.py
* Grid (0.25°) + ay bazında MODIS/VIIRS sayıları
* Yöntem A: k = MODIS / VIIRS (enlem bandı × yerel mevsim × uydu)
* weight_harm = k / aktif VIIRS uydu sayısı
* Eğitim: Arjantin 2012–2021, uygulama: her yer
⏰ 14:30 k_factors.csv → Oğuzhan
⏰ 16:30 harmonize veri hazır

P3 – ML & Doğrulama: OĞUZHAN
📁 pipeline/validate.py
* Eğitim 2012–2021, test 2022–2024
* Metrikler: R², bias + tahmin-gerçek grafiği
* Kontrol: Venn Ağustos 2026 + Nisan 2011 görünüyor mu?
* Zaman kalırsa: Yöntem B (lojistik regresyon)
⏰ 19:00 doğrulama sonuçları → İbrahim

━━━━━━━━━━━━━━━━━━
🟩 UYGULAMA EKİBİ
━━━━━━━━━━━━━━━━━━

P4 – Veri Katmanı + LİDER: BARIŞ
📁 app/query.py + CLAUDE.md
* 08:55 CLAUDE.md, .gitignore, requirements.txt, klasörler push
* 11:00 mock parquet → Yusuf
* get_hotspots(), monthly_matrix(), anomaly(), to_csv_bytes()
⏰ 16:30 gerçek veriyle çalışıyor

P5 – Arayüz: YUSUF
📁 app/app.py
* Streamlit: harita + bölge çizimi (streamlit-folium)
* Takvim ısı haritası: ay × yıl, viridis (plotly)
* Anomali kartı, ham/harmonize düğmesi, CSV indir
* Hazır bölgeler: Aachen/Eifel + La Rioja + Hohes Venn
* Streamlit Cloud'a yayınla (Pazar sabah)
⏰ 16:30 ham takvim çalışıyor
⏰ 19:00 MVP hazır

━━━━━━━━━━━━━━━━━━
🟨 HİKÂYE EKİBİ
━━━━━━━━━━━━━━━━━━

P6 – Sunum & Test: İBRAHİM
📁 docs/pitch/
* Slaytlar (~4 dk pitch), 6 FIRMS görüntüsü
* Worldview: aynı gün MODIS vs VIIRS
* Proje sayfası metni
* Demo senaryosu + uygulamayı kullanıcı gibi test et
* Saat takibi ⏱️
⏰ Pazar 14:00 sunum hazır

━━━━━━━━━━━━━━━━━━
⏰ KONTROL NOKTALARI (5 dk)
━━━━━━━━━━━━━━━━━━
10:30 Roller + şema + repo hazır
13:00 Gerçek veri herkeste, mock uygulama ayakta
16:30 ✅ Ham takvim uçtan uca
19:00 ✅ Harmonize MVP
Pazar 09:15 Jüri kriterleri
Pazar 12:00 ❄️ FEATURE FREEZE
Pazar 14:30 📤 TESLİM (son saat 15:00)

━━━━━━━━━━━━━━━━━━
🤖 CLAUDE KURULUMU (herkes, 1 kez)
━━━━━━━━━━━━━━━━━━
git clone … && cd …
echo "@ekip/P1_Suleyman.CLAUDE.md" > CLAUDE.local.md   ← kendi dosyanı yaz
(P2_Bahtiyar / P3_Oguzhan / P4_Baris / P5_Yusuf / P6_Ibrahim)

━━━━━━━━━━━━━━━━━━
📌 KURALLAR
━━━━━━━━━━━━━━━━━━
* Herkes SADECE kendi dosyasında çalışır
* Şema değişikliği → önce Barış'a sor
* Commit'ten önce: git pull --rebase
* Her 30–60 dk küçük commit, sadece kendi dosyanı git add
* Ajan kodunu commit'ten önce kontrol et
* Takıldın mı? 15 dk'dan fazla uğraşma, söyle!
