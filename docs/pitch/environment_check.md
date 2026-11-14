# P6 cloud ortam kontrolü — tarihsel kayıt, 14 Kasım 2026

Kaynak: `P6_ibrahim.patch`. Bu rapor önceki Linux cloud oturumuna aittir; repo referansı `8d5894c`, o sıradaki sözleşme v1.2'dir. Cloud'da `git pull --rebase` fast-forward ile tamamlandığı bildirilmiştir. Aşağıdaki sonuçlar Windows yerel ortamında yeniden çalıştırılmadı.

Mevcut yerel sözleşme v1.3'tür. İlk yerel incelemede `.venv/Scripts/python.exe` ve `uv` bulunmadı; Python 3.12 ve sabit paketlerin yerel doğrulaması bekleniyor. Yerel durum ve PowerShell komutları [test_notes.md](test_notes.md) içindedir. Cloud'daki sentetik smoke testi, yerel veya bilimsel doğrulama kanıtı değildir.

## Cloud'da bildirilen kurulum

`uv` zaten kurulu olduğundan yeniden kurulmadı. Eski `.venv` yoktu; yeni ortam
repo kökünde oluşturuldu. Ek paket eklenmedi ve sabit sürümler değiştirilmedi.

```bash
uv venv --python 3.12 .venv
source .venv/bin/activate
uv pip install -r requirements.txt
python --version
python tests/smoke_test.py
```

Kontrol edilen yorumlayıcı: `.venv/bin/python`; sanal ortam aktif.
Python sürümü: **3.12.14**. `requirements.txt` içindeki 10 doğrudan bağımlılığın
tamamı istenen sürümle eşleşti:

```text
pandas==3.1.1
pyarrow==26.0.1
numpy==2.5.4
shapely==2.2.0
streamlit==1.67.0
streamlit-folium==0.27.4
folium==0.20.0
plotly==7.1.0
scikit-learn==1.9.1
matplotlib==3.11.2
```

## Smoke test sonucu

```text
✅ ortam: Python 3.12 + requirements.txt sürümleri      Python 3.12, 10 paket
13/13 geçti/atlandı, 0 hata
```

7 kontrol geçti; 6 kontrol henüz dosyası olmadığı için atlandı:

- `data/hotspots.parquet`
- `data/satellite_coverage.csv`
- `data/hotspots_harm.parquet`
- `data/monthly_grid.parquet`
- `data/k_factors.csv`
- `docs/validation/metrics.json`

Query testlerinde seçilen dosya `data/mock/hotspots_mock.parquet` idi
(`mock=True`). Bu sonuç gerçek veriyle uçtan uca doğrulama veya bilimsel başarı
iddiası değildir. Sentetik sonuçlar sunuma alınmaz.

## P6 kontrolünün yeniden çalıştırılması

Önceki ülke-yıl indirmesinin CSV kontrol betiği yeni `.venv` içinden yeniden
çalıştırıldı: 144 dosya, 6.893.939 ham veri satırı; alan sayısı bozuk satır ve
kontrol edilen temel alanlarda eksik değer yok. Bu dosyalar v1.1 tarihsel
arşividir; v1.2 yalnız DL_FIRE girdilerini kabul eder. Ingest çalıştırılmadı.

## Cloud editöründeki seçim notu

VS Code'da **Python: Select Interpreter** komutundan repo içindeki
`.venv/bin/python` seçilmelidir. Kullanıcının editör ayarı buradan değiştirilmedi.

## Güncel veri ve sunum kuralları

- `argentina` ve `aachen_eifel` bölgeleri; Aachen kutusu
  `5.96, 50.44, 6.44, 50.83`.
- Kaynak DL_FIRE archive + NRT; ülke-yıl CSV'leri kullanılmaz.
- Uydu eklenme dönemleri 2012/2018/2023; NOAA-21 başlangıcı 2023-03-01,
  S-NPP bitişi 2026-11-02. Grafik çizgileri verideki
  `data_info()["satellite_ranges"]` değerlerinden alınır.
- Geçerli DL_FIRE arşivinin bu çalışma alanına aktarımı henüz yapılmadı.
