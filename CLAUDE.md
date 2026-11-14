# CLAUDE.md — Space Apps 2026: MODIS ↔ VIIRS Yangın Takvimi

> Bu dosya tüm ekip için ortaktır. Sahibi: **P4 Barış**. Değişiklik → önce Barış'a sor.

## 0. Claude için ilk adım (ZORUNLU)
1. Kullanıcının rolünü `CLAUDE.local.md` dosyasından öğren (gitignore'da, herkesin kendi makinesinde).
2. `CLAUDE.local.md` yoksa kullanıcıya **"Hangi roldesin (P1–P6)?"** diye sor, sonra
   `ekip/` altındaki ilgili dosyayı oku ve kullanıcıya şu içerikle `CLAUDE.local.md` oluşturmayı öner:
   ```
   @ekip/P1_Suleyman.CLAUDE.md
   ```
3. **Sadece o rolün sahip olduğu dosyalara yaz.** Başka birinin dosyasında değişiklik gerekiyorsa
   kodu yazma; kullanıcıya "şu kişiye şunu söyle" diye kısa bir not ver.
4. Şema veya API (`docs/CONTRACT.md`) değişikliği gerekiyorsa: dur, kullanıcıya "önce P4'e sor" de.
5. Başkasına etki eden her teslimde **§8 Teslim Protokolü**'nü uygula (test → onay → push → prompt).
6. Kullanıcı `[Px İsim → Py İsim]` başlıklı bir prompt yapıştırırsa: önce `git pull --rebase`,
   sonra prompttaki KONTROL adımını çalıştır, sonucu kullanıcıya göster, ardından YAPMAN GEREKEN'e geç.

## 1. Proje
NASA FIRMS aktif yangın **tespitleri** ile 2000–2026 arası **tutarlı bir aylık tespit takvimi**.
Sorun: MODIS (Terra/Aqua, 2000→) ve VIIRS (S-NPP 2012→2026-11-02, NOAA-20 2018→, NOAA-21 2023→) farklı
hassasiyette; her yeni uydu ham sayılarda **yapay sıçrama** yaratır. Biz VIIRS tespitlerini
**MODIS-eşdeğeri** birime çevirip (harmonizasyon) kesintisiz bir seri gösteriyoruz.
Harmonizasyon katsayıları **doğrulanmamış bir hipotezdir**; P3'ün test metrikleri (2022–2024)
gelmeden "doğru/kalibre" diye sunulmaz, metrikler geldikten sonra da sayılarıyla birlikte sunulur.

Pitch'in ana görseli: ham takvimde 2012/2018/2023 sıçramaları → harmonize takvimde yok.
Doğrulama hikâyesi: Hohes Venn'de bilinen yangın olaylarıyla örtüşen tespit artışları
**Nisan 2011** ve **Ağustos 2026**'da takvimde görünmeli. (Tespit ≠ doğrulanmış yangın olayı.)

## 2. Ekip & dosya sahipliği
| Rol | Kişi | Sahip olduğu dosyalar |
|---|---|---|
| P1 Veri Mühendisi | Süleyman | `pipeline/ingest.py`, `pipeline/burned_area_check.py` (MCD64A1 destekleyici kontrol, ana şemaya dokunmaz), `data/sample/` |
| P2 Harmonizasyon | Bahtiyar | `pipeline/harmonize.py` |
| P3 ML & Doğrulama | Oğuzhan | `pipeline/validate.py`, `docs/validation/` |
| P4 Veri Katmanı + LİDER | Barış | `app/query.py`, `contract.py`, `docs/CONTRACT.md`, `tests/`, `README.md`, `CLAUDE.md`, `ekip/`, `requirements.txt`, `.gitignore`, `data/mock/`, `data/deploy/` |
| P5 Arayüz | Yusuf | `app/app.py`, `.streamlit/config.toml` |
| P6 Sunum & Test | İbrahim | `docs/pitch/` |

Ortak dosyalara (`requirements.txt` vb.) paket eklemek gerekirse → Barış'a söyle, o ekler.

## 3. Veri sözleşmesi (KİLİTLİ — değişiklik sadece P4 onayıyla; sürüm: `docs/CONTRACT.md` başlığı)
Tam şema, tekrar kuralları, bölge adları, pipeline girdi/çıktıları ve `query.py` API'si:
**`docs/CONTRACT.md`** (aşağıda içe aktarılıyor). Kod karşılığı: **`contract.py`**
(sabitler + `validate_hotspots(df, stage)`). P1 ve P2 parquet yazmadan önce doğrulayıcıyı çağırır.

@docs/CONTRACT.md

Hatırlatma (en sık hata):
- Sütunlar FIRMS adlarıyla: `latitude`, `longitude`, `brightness`, `confidence` (**orijinal değer**),
  `type`. Sınıf için `confidence_class`.
- Bir satır = bir **tespit** (termal anomali), doğrulanmış yangın olayı değil (CONTRACT §8).
- `weight_harm` ingest'te NaN; yöntemi P2'nin, doğrulaması P3'ün (CONTRACT §6).

### 3.1 Dosya konumları
```
contract.py       şema sabitleri + doğrulayıcı (P4)
data/raw/<region>/  FIRMS CSV'leri, klasör adı = region slug'ı (git'e GİRMEZ)
data/sample/      P1'in örnek dosyası (küçük, git'e girer)
data/mock/        P4'ün sentetik parquet'i + üretici (git'e girer)
data/deploy/      Streamlit Cloud için küçültülmüş veri (<50 MB, git'e girer)
data/*.parquet, data/*.csv   tam veri ve ara çıktılar (git'e GİRMEZ — Drive/USB)
docs/CONTRACT.md  sözleşme (P4)
docs/validation/  P3 çıktıları (png + metrics.json)
docs/pitch/       P6
tests/smoke_test.py  uçtan uca duman testi (P4)
```

### 3.2 Paylaşılan modülü içe aktarma
`pipeline/*.py` ve `app/*.py` kök dizini import yoluna ekleyerek `contract`'ı kullanır:
```python
import sys; from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from contract import validate_hotspots
```

## 4. Ortam ve çalıştırma
### 4.1 Herkes AYNI ortamı kullanır (ZORUNLU)
- **Python 3.12** (`.python-version`) + `requirements.txt`'teki **sabit (==) sürümler**.
  Sebep: pandas 2 ↔ 3 gibi farklar aynı kodda farklı dtype üretir → `contract.py` doğrulaması
  bir makinede geçer, diğerinde patlar. Streamlit Cloud da 3.12 ile yayınlanır.
- Kurulum `uv` ile (Python 3.12'yi kendisi indirir, yönetici izni gerekmez):
  ```bash
  # uv yoksa:  Linux/Mac: curl -LsSf https://astral.sh/uv/install.sh | sh
  #            Windows (PowerShell): powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  uv venv --python 3.12 .venv
  source .venv/bin/activate            # Windows: .venv\Scripts\activate
  uv pip install -r requirements.txt
  python tests/smoke_test.py           # ilk satır: "ortam: Python 3.12 + requirements.txt sürümleri" ✅
  ```
- Claude: kod çalıştırmadan önce `.venv` aktif mi ve Python 3.12 mi kontrol et. Değilse kurulumu
  kullanıcıya hatırlat; sistem Python'uyla ya da `pip install <paket>` ile devam etme.
- Paket ekleme/sürüm değiştirme sadece P4 (`requirements.txt`). Değişince herkes
  `uv pip install -r requirements.txt` çalıştırır.

### 4.2 Çalıştırma
```bash
source .venv/bin/activate
python pipeline/ingest.py        # P1 → data/hotspots.parquet
python pipeline/harmonize.py     # P2 → data/hotspots_harm.parquet, monthly_grid.parquet, k_factors.csv
python pipeline/validate.py      # P3 → docs/validation/
python tests/smoke_test.py       # P4 → sözleşme + query uçtan uca kontrol
streamlit run app/app.py         # P5
```
Tüm script'ler **repo kökünden** çalıştırılır; yollar köke göreli.

## 5. Kod kuralları
- Python 3.12 (§4.1), pandas 3 + pyarrow. Kod/değişken isimleri İngilizce, yorumlar Türkçe olabilir.
- Her pipeline script'i: `main()` + `if __name__ == "__main__":`, başta yol sabitleri.
- Sessiz hata yok: beklenmeyen sütun/değer → açık `ValueError`.
- Büyük veriyi tek seferde belleğe alma gerekiyorsa `pyarrow`/`usecols` kullan.
- Yeni paket gerekirse ekleme, kullanıcıya "Barış'a söyle" de.

## 6. Git kuralları
- Commit'ten önce: `git pull --rebase`
- 30–60 dk'da bir küçük commit; mesaj: `P1: archive+nrt birleştirme` gibi rol önekli.
- Sadece kendi dosyalarını `git add` et (`git add -A` YOK).
- Ajan (Claude) kodunu commit'ten önce oku ve en az bir kez çalıştır.
- Veri dosyası (`data/raw`, büyük parquet) asla commit'lenmez.
- Başkasını etkileyen push'lar §8'e göre yapılır.

## 7. Takvim (Cumartesi 14 Kasım → Pazar 15 Kasım 2026)
| Saat | Kontrol noktası |
|---|---|
| 08:55 | P4: repo iskeleti push |
| 10:30 | Roller + şema + repo hazır (5 dk toplantı) |
| 11:00 | P4: mock parquet → P5 |
| 11:30 | P1: örnek dosya (1 bölge, 1 yıl) |
| 12:30 | P1: tam veri |
| 13:00 | Gerçek veri herkeste, mock uygulama ayakta |
| 16:30 | ✅ Ham takvim uçtan uca (P2 harmonize veri, P4 gerçek veri) |
| 19:00 | ✅ Harmonize MVP (P3 doğrulama → P6) |
| Pazar 09:15 | Jüri kriterleri gözden geçirme |
| Pazar 12:00 | ❄️ FEATURE FREEZE — sadece bug fix |
| Pazar 14:00 | Sunum hazır |
| Pazar 14:30 | 📤 TESLİM (son saat 15:00) |

**Takıldın mı? 15 dk'dan fazla uğraşma, söyle.** Claude: kullanıcı aynı hatada 15 dk'yı geçtiyse
bunu hatırlat ve "Barış'a yaz" öner.

## 8. Teslim Protokolü — her önemli adımda (ZORUNLU)
**Önemli adım** = başka birinin işini etkileyen her teslim: §7'deki teslimler, şema/API değişikliği,
başkasının kullanacağı yeni dosya/fonksiyon, birinin beklediği bug fix.
Üç adım sırayla yapılır; **kullanıcının açık onayı olmadan push yok.**

### Adım 1 — Kullanıcıya test ettir, onay al
- İş bittiğinde Claude push ETMEZ. Kullanıcıya kısa bir test listesi verir:
  - çalıştırılacak komut(lar), kopyala-yapıştır hazır
  - her komut için **beklenen sonuç** (sayı, tablo, ekranda ne görünmeli)
  - rol dosyasındaki "Bitti kontrolü" maddelerinden ilgili olanlar
- Kullanıcı kendisi çalıştırır / bakar. "Onay", "tamam push et" gibi **açık onay** gelene kadar
  Adım 2'ye geçilmez. Sorun bildirilirse düzelt → Adım 1'i tekrarla.
- Claude kendi testlerini de çalıştırabilir ama "testlerim geçti" kullanıcı onayının yerine geçmez.

### Adım 2 — Değişiklik türüne göre GitHub'a gönder
| Tür | Örnek | Yöntem |
|---|---|---|
| Küçük | kendi dosyanda iyileştirme, tek dosyalık bug fix | `main`'de commit → `git pull --rebase` → `git push` |
| Yapısal | şema / API (`docs/CONTRACT.md`), ortak dosya (`CLAUDE.md`, `requirements.txt`), yeni çıktı dosyası, birden çok dosya | `git switch -c <rol>/<konu>` (ör. `p4/query-api`) → commit(ler) → `git switch main` → `git pull --rebase` → `git merge --no-ff <dal>` → `git push` → `git branch -d <dal>` |
- Sadece kendi dosyalarını `git add` et. Commit mesajı: rol öneki + ne değişti + kimi etkiler.
- Şema/API'ye dokunan yapısal değişiklik → önce P4 onayı (§0 madde 4).
- Merge çakışması çıkarsa **çözmeye çalışma**: dur, kullanıcıya hangi dosyada ve kiminle çakıştığını söyle.
- Push sonrası kısa commit hash'ini al (`git log --oneline -1`).

### Adım 3 — Etkilenen arkadaşın Claude'u için prompt yaz
Push'tan sonra etkilenen **her kişi için ayrı**, tek kod bloğunda, kopyala-yapıştır hazır prompt yaz.
Alıcı Claude bu sohbeti görmedi: dosya yolları, fonksiyon adları ve CLAUDE.md bölüm numaraları
açıkça yazılmalı, prompt tek başına anlaşılır olmalı. Şablon:
```
[P4 Barış → P5 Yusuf] <konu> — commit <hash>

ÖNCE: git pull --rebase

NE DEĞİŞTİ:
- <dosya>: <değişiklik>

SENİN İÇİN ANLAMI:
- <alıcının işini nasıl etkiliyor>

YAPMAN GEREKEN:
1. <somut adım>

KONTROL (çalıştır, sonucu kullanıcıya göster):
- <komut>  →  beklenen: <sonuç>

DOKUNMA: <alıcının sahibi olmadığı dosyalar>. Sorun varsa kod yazma, <gönderen>'e bildir.
```
Prompt sohbette verilir; kullanıcı WhatsApp/Discord ile ilgili kişiye iletir.
