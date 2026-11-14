# VPS kurulumu — Active Fire Detection Calendar

Sahibi: P2 Bahtiyar (hazırlık) · sunucu ve karar: P4 Barış. Hedef: `srv1.barismutlu.de` (netcup VPS nano,
2 vCore / 2 GB RAM, Ubuntu 24.04, Apache 2.4 + Let's Encrypt, ufw 22/80/443).

Uygulama Apache'nin arkasında, sadece `127.0.0.1:8501`'de dinleyen bir systemd servisi olarak çalışır.
Yeni port açılmaz; ufw'ye dokunulmaz.

## Karar: hangi veri dosyası

| Veri | Dosya | Tepe bellek (ölçüm) | 2 GB sunucu |
|---|---|---|---|
| Hazır bölgeler (Hohes Venn, Aachen/Eifel, La Rioja) | `data/deploy/hotspots_deploy.parquet` — git'te, 3,4 MB, 139.779 satır | ≈ 375 MB | uygun |
| Tam veri (Arjantin'in tamamı) | `data/hotspots_harm.parquet` — git'te değil, 163 MB, 7.082.663 satır | ≈ 1.840 MB | **çalışmaz** |

Ölçüm: uygulamanın açılışı + 3 bölge × Ham/Harmonize, tek kullanıcı, macOS'ta `ru_maxrss`. Servis bu yüzden
`HOTSPOTS_PATH` ile küçük dosyaya sabitlenmiştir; Streamlit Cloud da aynı dosyayı kullanıyor.
Sonuç: sunucuda haritaya elle çizilen alan sadece bu üç bölgenin içinde veri gösterir.

## Karar: adres (Barış seçer)

- **A — alt alan adı (önerilen):** `https://fire.barismutlu.de` → `apache-subdomain.conf`.
  Gerekir: DNS A kaydı `fire` → `159.195.126.141` ve yeni sertifika (`certbot --apache -d …`).
- **B — alt yol:** `https://barismutlu.de/fire/` → `apache-subpath.conf`. DNS ve sertifika gerekmez;
  mevcut 443 sanal sunucusunun içine eklenir ve serviste `STREAMLIT_SERVER_BASE_URL_PATH=fire` açılır.

## Adımlar

1. **Swap (önerilir, bir kez).** Kayıtta swap'ın açıldığı doğrulanmamış. `free -h` ile bak; yoksa:
   ```bash
   sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile
   echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
   ```
2. **Uygulama + servis.** Depoyu `/opt/firecal`'a kurar, `firecal` sistem kullanıcısını açar, Python 3.12
   sanal ortamını ve paketleri kurar, servisi başlatır, sağlık kontrolünü çalıştırır. Apache'ye dokunmaz.
   ```bash
   curl -fsSL https://raw.githubusercontent.com/barismuutlu/Nasa_Hackathon/main/deploy/vps/install.sh | bash
   ```
   Başka bir dalı yayınlamak için: `BRANCH=<dal> bash install.sh`. Paket kurulumu ≈ 550 MB disk.
3. **Apache.** Seçilen varyantın dosyasının başındaki komutları uygula (`a2enmod …`, `a2ensite`,
   `apache2ctl configtest`, `reload`, A varyantında `certbot`).
4. **Kontrol.**
   ```bash
   bash /opt/firecal/deploy/vps/check.sh          # service: active · health: 200 · bellek
   curl -sI https://fire.barismutlu.de/_stcore/health | head -1     # HTTP/2 200  (B: …/fire/_stcore/health)
   ```
   Tarayıcıda: sayfa açılır, harita ve takvim gelir, "Hohes Venn · August 2026" düğmesi 169,2 gösterir.
   Sayfa "Please wait…"te kalıyorsa WebSocket kuralı çalışmıyordur: `a2enmod proxy_wstunnel rewrite`.

## Güncelleme ve geri alma

```bash
bash /opt/firecal/deploy/vps/update.sh                         # son commit'i çek, servisi yeniden başlat
sudo -u firecal git -C /opt/firecal checkout <commit> && sudo systemctl restart firecal    # geri alma
sudo systemctl disable --now firecal && sudo a2dissite firecal && sudo systemctl reload apache2   # kaldırma
journalctl -u firecal -n 50 --no-pager                          # hata günlüğü
```

## Doğrulanan / doğrulanmayan

- Doğrulandı (geliştirici makinesinde): servis komutu aynı ortam değişkenleriyle kök ve `/fire` alt yolunda
  `_stcore/health` = 200; betiklerin kabuk sözdizimi; iki Apache dosyasının sözdizimi (`httpd -t`, macOS Apache 2.4).
- **Sunucuda denenmedi:** `install.sh`, systemd birimi (bellek sınırları, sandbox ayarları), Apache üzerinden
  WebSocket, certbot. İlk kurulumda `check.sh` ve tarayıcı kontrolü bunun testidir.
- Bellek sınırı: `MemoryMax=1100M`. Aşılırsa servis yeniden başlar; aynı anda çok ziyaretçi olursa
  `journalctl`'de görünür.
