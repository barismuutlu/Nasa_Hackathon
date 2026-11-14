# P6 — Sunum & Test: İbrahim

Ortak kurallar ve takvim kök `CLAUDE.md`'de, terminoloji **`docs/CONTRACT.md` §8**'de. Bu dosya sadece senin rolün.

## Sahip olduğun dosyalar (Claude SADECE bunlara yazar)
- `docs/pitch/` (slaytlar, görseller, metinler, demo senaryosu, test notları)

## Görev
1. **Pitch (~4 dk)** — `docs/pitch/slides/` + `docs/pitch/script.md` (konuşma metni, saniye saniye).
   Önerilen akış:
   1. Sorun (30 sn): 25 yıllık yangın kaydı, uydular değişiyor → sahte trend
   2. Kanıt (30 sn): aynı gün MODIS vs VIIRS Worldview görüntüsü
   3. Çözüm (60 sn): harmonizasyon fikri (k = MODIS/VIIRS, aktif uydu sayısına bölme)
   4. Demo (60 sn): Hohes Venn → Nisan 2011 & Ağustos 2026; La Rioja ham ↔ harmonize
   5. Doğrulama (30 sn): Oğuzhan'ın R², bias, tahmin-gerçek grafiği
   6. Etki + sonraki adım (30 sn)
2. **6 FIRMS görüntüsü** — `docs/pitch/img/`: dosya adında tarih + uydu + bölge
   (ör. `2026-08-xx_VIIRS_HohesVenn.png`). Kaynak/attribution notu `docs/pitch/img/SOURCES.md`.
3. **Worldview** — aynı gün, aynı bölge MODIS vs VIIRS fire katmanı yan yana.
4. **Proje sayfası metni** — `docs/pitch/project_page.md` (background hazır; özet, yöntem, veri
   kaynakları: NASA FIRMS MODIS C6.1 + VIIRS C2, araçlar, ekip).
5. **Demo senaryosu** — `docs/pitch/demo.md`: tıklama tıklama adımlar + internet giderse yedek
   (ekran kaydı / ekran görüntüleri).
6. **Kullanıcı testi** — 19:00 MVP'den sonra uygulamayı yabancı biri gibi kullan.
   Hataları `docs/pitch/test_notes.md`'ye yaz: adım, beklenen, olan, kime (Yusuf/Barış).
7. **Saat takibi ⏱️** — her kontrol noktasından 10 dk önce gruba hatırlat; Pazar 12:00 freeze,
   14:30 teslim.

## Girdi bekleyeceğin şeyler
| Saat | Ne | Kimden |
|---|---|---|
| 16:30 | Ham vs harmonize yıllık grafik | Bahtiyar (P2) |
| 19:00 | `docs/validation/` + 3 cümle özet | Oğuzhan (P3) |
| 19:00 | MVP (test için) | Yusuf (P5) |
| Pazar 10:00 | Canlı link | Yusuf (P5) |

## Teslimler
| Saat | Ne |
|---|---|
| 19:00 | Slayt taslağı (görsellerle) |
| Pazar 09:15 | Jüri kriterleri ↔ slayt eşleme tablosu |
| Pazar 13:00 | Prova (kronometreli, < 4 dk) |
| Pazar 14:00 | Sunum + proje sayfası + demo videosu hazır |

## Claude'a not
- Kod dosyalarına (`pipeline/`, `app/`) yazma. Uygulamada hata görürsen test_notes'a yaz.
- Sayıları (R², bias, sayımlar) uydurma; sadece `docs/validation/metrics.json`'dan al,
  yoksa `[TBD — Oğuzhan]` bırak.
- Görsellerde NASA logosu kullanma; kaynak olarak "NASA FIRMS / Worldview" yaz.
- Terminoloji (CONTRACT §8): tespit/hotspot ≠ doğrulanmış yangın olayı. Harmonizasyonu
  "doğrulanmış" diye sunma; "Arjantin'de kalibre, 2022–2024 testinde R²=…" gibi sayıyla anlat.
- Sentetik (mock) veriden ekran görüntüsü sunuma girmez (sayfada "SENTETİK" uyarısı varsa kullanma).
