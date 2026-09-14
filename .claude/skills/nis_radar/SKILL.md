---
name: nis_radar
description: Nişindeki YouTube kanallarını (video + Shorts) her gün otomatik tarayıp transkriptlerinden Türkçe özet raporu çıkaran kişisel radar sistemini kurar, çalıştırır ve yönetir. "niche radar", "youtube kanal takibi", "rakipleri izle", "günlük video özeti", "transkript raporu" gibi isteklerde kullan.
---

# Niş Radar

Kullanıcının kendi bilgisayarında çalışan günlük YouTube izleme asistanı. Akış:
`yt-dlp ile keşif (videos + shorts sekmesi)` → `altyazı indir (video indirmeden)` → `claude -p ile özet` → `~/NicheRadar/reports/YYYY-MM-DD.md` → `bildirim`.

Tüm mantık `scripts/radar.py` içindedir (sadece Python standart kütüphanesi). Sen kod YAZMAZSIN; script'i kurar, çalıştırır ve çıktıyı kullanıcıya anlatırsın.

## Değişmez kurallar

1. **Cloud'da çalıştırma.** YouTube, AWS/GCP/Azure IP'lerinden altyazı isteğini engeller. Bu sistem kullanıcının kendi makinesinde (Mac/Windows/Linux masaüstü) çalışmalıdır. Sunucuya/VPS'e taşıma önerme. Kullanıcıya sade anlat: "Bazı işler bulutta değil, kendi bilgisayarında daha güvenilir çalışır."
2. **Kullanıcının kendi YouTube/Instagram hesabı kullanılmaz.** Cookie ile giriş yalnızca kullanıcı açıkça isterse ve ban riskini söyleyerek (`ytdlp_extra_args`).
3. **Script'i yeniden yazma.** Hata varsa önce `doctor` ve `logs/radar.log`. Değişiklik gerekiyorsa `config.json` üzerinden. Geçici hatalar (altyazı henüz yok, ağ, Claude) otomatik tekrar denenir (3 deneme); `state.json`'ı elle düzenleme.
4. **Kurulum adımlarını tek tek doğrula.** Her komutun çıktısını oku; "muhtemelen çalıştı" yok.
5. **Uzun komutları arka planda çalıştır.** `run` dakikalar sürer (video başına ~30 sn + özet). Bash aracını arka planda ya da en az 600000 ms zaman aşımıyla kullan; bitişi `logs/radar.log`'daki `=== run bitti` satırından doğrula.

## Kurulum akışı (ilk kez)

Bu skill'in klasörü: `SKILL_DIR` (bu dosyanın bulunduğu klasör). Script: `SKILL_DIR/scripts/radar.py`.

### 0. Açılış (komut çalıştırmadan ÖNCE söyle)
Tek paragraf: "Bu sistem şu an sadece YouTube'u takip ediyor: video ve Shorts. Instagram, TikTok, LinkedIn yok. Şimdi bilgisayarına iki küçük araç kuracağım, birkaç onay soracağım; sonra hangi kanalları izleyeceğimizi konuşacağız. Başlayalım mı?" Onay gelmeden komut çalıştırma.

Sonra ortamı tespit et: işletim sistemi (`uname` / `ver`), Python (`python3 --version`, Windows'ta `python --version`), `claude --version`, `uv --version`, `yt-dlp --version`.
- Python 3.9+ gerekir. macOS'ta hazır gelir. Windows'ta yoksa: `uv python install 3.12` ve script'i `uv run --python 3.12 python radar.py ...` ile çalıştır.
- `claude` yoksa dur: Claude Code kurulu ve giriş yapılmış olmalı (özetleme `claude -p` ile yapılır, kullanıcının aboneliğini kullanır).

### 1. Bağımlılıklar
- `uv` yoksa: macOS/Linux `curl -LsSf https://astral.sh/uv/install.sh | sh`, Windows `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`.
- `uv tool install "yt-dlp[default,curl-cffi]"` (curl-cffi bot kontrolü riskini azaltır).
- **PATH tuzağı:** her Bash çağrısı yeni kabuk açar, `source ~/.zshrc` işe yaramaz. Kurulumdan sonraki komutları aynı satırda `export PATH="$HOME/.local/bin:$PATH" && ...` ile çalıştır. Zamanlayıcı için PATH'i script kendisi yazar, ek işlem gerekmez.
- ffmpeg gerekmez. Sadece altyazısı olmayan videolar için Whisper yedeği istenirse gerekir (varsayılan kapalı).

### Windows notu (tüm komutlar için geçerli)
Claude Code Windows'ta Git Bash kullanır: `~/NicheRadar` yolları aynen geçerli. Sadece `python3` → `python` (Python yoksa `uv run --python 3.12 python`). Kullanıcıya gösterilecek klasör: `C:\Users\<ad>\NicheRadar`.

### 2. Kur
```
python3 SKILL_DIR/scripts/radar.py install
```
`~/NicheRadar/` altında `config.json`, `prompt.md`, `digest_prompt.md`, `radar.py` kopyası, `reports/`, `logs/`, `cache/` oluşur. Bundan sonra komutları `~/NicheRadar/radar.py` üzerinden çalıştır.

### 3. Kanalları al
Sor: "Aklında takip etmek istediğin kanallar var mı? Varsa linklerini yapıştır. Yoksa nişini / işini söyle, senin için kanal önereyim."

**A) Kullanıcı link verdiyse:** `@handle`, kanal linki, **video/Shorts linki** veya `UC...` id kabul edilir (video linkinden kanalı script bulur). Hepsini tek komutta ekle; biri çözülmezse diğerleri yine kaydedilir, çözülmeyeni kullanıcıya söyle.
```
python3 ~/NicheRadar/radar.py add-channel @nicksaraev https://www.youtube.com/@NateHerk https://youtu.be/VIDEO_ID
```

**B) Kullanıcı niş söylediyse:** iki soru daha: "Global (İngilizce) kanallar mı, Türkiye'deki (Türkçe) kanallar mı, ikisi de mi?" ve "Rakiplerin mi (senin işini yapanlar), yoksa senin müşterinin izlediği üreticiler mi?" Sonra web araması yap (ör. "best <niş> youtube channels 2026", "<niş> youtube kanalları"), 5-8 aday çıkar: kanal adı, @handle, tek cümle neden. Adayları **eklemeden** doğrula:
```
python3 ~/NicheRadar/radar.py check-channel @aday1 @aday2 @aday3
```
"YOK" çıkanı listeden at, uydurma handle önerme. Kullanıcı seçsin; sadece seçilenleri `add-channel` ile ekle. 3-6 kanal ideal; 10'dan fazlasını önerme.

Sonunda `list` ile listeyi göster ve onaylat. Çıkarmak için: `python3 ~/NicheRadar/radar.py remove-channel <@handle|kanal URL|UC id|tam ad>` (kullanıcıyı JSON'a yönlendirme). Alt-dize yalnızca tek kanala denk gelirse kabul edilir; birden fazla kanala uyan bir parça ("ai" gibi) hiçbir şeyi silmez, adayları listeler. Kurulumdan sonra eklenen kanal da ilk çalışmadaki geçmiş penceresini (`first_run_days` / `first_run_items`) görür; keşfi boş dönen kanal başlatılmış sayılmaz, sonraki çalışmada tekrar denenir.

### 4. Kurulum soruları (hepsini SOR, cevapları `~/NicheRadar/config.json`'a yaz)
Kanallar eklendikten sonra sırayla, kısa ve Türkçe sor; cevap gelmeden varsayım yapma. Değerleri sayı olarak yaz (tırnaksız).
1. **Geçmiş:** "Başlangıçta geçmişe ne kadar bakalım? Son 7 gün / son 30 gün / hiç (sadece bundan sonra çıkanlar)."
   - 7 gün → `"first_run_days": 7`, `"first_run_items": 10`
   - 30 gün → `"first_run_days": 30`, `"first_run_items": 20`. Kullanıcıya söyle: "Her kanalın her sekmesinden en yeni 20 içeriğe bakılır, bunlardan son 30 gün içinde olanlar işlenir (daha eski içerik ve 20'den sonrası tarama dışıdır). İlk gün en fazla 20 içerik işlenir, kalanı bekleyen listede tutulur ve sonraki günlerde sırayla işlenir; ilk rapor birkaç güne yayılabilir."
   - hiç → `"first_run_days": 0`, `"first_run_items": 0`. İlk çalışma hiçbir şey işlemez, sadece başlangıç noktasını koyar.
2. **Saat:** "Bilgisayarın açıkken her gün saat kaçta çalışsın? Önerim 08:00. Kapalıysa o gün atlanır, uykudaysa uyanınca çalışır; rapor `~/NicheRadar/reports` klasörüne düşer ve bildirim gelir." → `"schedule_time": "08:00"` (HH:MM).
3. **Dil:** "Özetler Türkçe olsun, değil mi?" → `"summary_lang"` (varsayılan "Türkçe"). Kanal altyazıları `sub_langs` ile çekilir (varsayılan en + tr); başka dilde kanal eklenecekse o dili de listeye ekle. Script her videoda orijinal dilin altyazısını tercih eder (çeviri değil).
4. **Niş:** "Senin işin / nişin ne? Özetlerdeki 'içerik fikri puanı' buna göre verilir." → `"niche"` (kısa metin, ör. "KOBİ'ler için n8n otomasyonu"). Boş kalırsa puan genel verilir.

Sorma, varsayılan kalsın; kullanıcı kendisi isterse ayarla: `report_dir` (boşsa `~/NicheRadar/reports`; Obsidian gibi bir klasör isterse tam yol — **günlük notlarının durduğu klasörü değil, vault içinde ayrı bir alt klasörü** ver; script başkasının yazdığı aynı isimli `YYYY-MM-DD.md` dosyasına asla eklemez, `YYYY-MM-DD.nis-radar.md` yazar ve siteye yalnızca kendi raporlarını alır), `telegram` (BotFather token + @userinfobot chat id), `model` ("sonnet" ucuz ve yeterli), `max_per_run` (günlük tavan 20), `max_age_days` (günlük çalışmada 14 günden eski içerik atlanır), `max_attempts` (geçici hata için deneme sayısı, 3), `claude_extra_args` (ek `claude -p` bayrakları).

### 5. Sağlık kontrolü
```
python3 ~/NicheRadar/radar.py doctor
```
"SONUC: hazir" görmeden ilerleme. "eksik var" ise satırlara bak: `yt-dlp YOK` → PATH (Bölüm 1); `kesif bos dondu` → kullanıcıya VPN / iCloud Private Relay'i kapatmasını söyle, tekrar dene; `saat GECERSIZ` → HH:MM biçimine çevir; `claude -p : HATA` → terminalde `claude -p ok` (login düşmüş olabilir).
`doctor` bir tane minik `claude -p` çağrısı yapar: `claude -p : OK giris=N ...` satırı bağlam boyutunu gösterir. Özet çağrıları kullanıcının Claude Code ortamından (CLAUDE.md, plugin, MCP, araçlar) yalıtılmıştır; birkaç bin token normaldir, 15k üstü "izolasyon calismiyor" uyarısıdır (`claude update`). Diğer satırlar: `son hata` (son çalışmanın hatası, başarılı çalışma siler), `bekleyen ozet` (rapor yazılamamış özetler), `kilit` (süren çalışma).

### 6. İlk çalışma
Önce keşfi göster, sonra gerçek çalıştır (arka planda, bkz. kural 5). İlk gerçek çalışmada `--limit` ve `--only` KULLANMA (`--only` ile seçilmeyen kanallar başlatılmaz; sonraki tam çalışmada onlar da geçmiş penceresini görür):
```
python3 ~/NicheRadar/radar.py run --dry-run
python3 ~/NicheRadar/radar.py run
```
- 7 / 30 gün seçildiyse: kuyruk kanallar arasında sırayla dağıtılır, bu çalışmada en fazla `max_per_run` içerik işlenir, kalanı `state.json` içinde bekleyen listede tutulur ve sonraki çalışmalarda önce onlar işlenir (geçmiş penceresi korunur). Rapor açılır (`reports/YYYY-MM-DD.md`), kullanıcıya ilk 20-30 satırı göster.
- "hiç" seçildiyse: dry-run listesi BOŞ ve rapor dosyası OLUŞMAZ; bu normaldir. `run` yine çalıştırılır (başlangıç noktasını koyar). Kullanıcıya de ki: "Sıfır noktası kondu. İlk raporun, kanallardan biri yeni içerik yükledikten sonraki ilk çalışmada (saat HH:MM) gelecek. Şimdi bir örnek görmek istersen geçmişi 7 güne çevirebilirim."
- Hızlı test istersen: `run --no-llm --limit 3` (transkript çeker, Claude'u çağırmaz; bu da başlangıç noktasını koyar, kalanı bekleyen listeye yazar).
- Durum tablosunda "transkript yok (deneme 1/3 …)" ya da "hata" görürsen normaldir: içerik bekleyen listede kalır, sonraki çalışmalarda tekrar denenir, 3 denemeden sonra "vazgecildi" olur. Aynı çalışmada 5 ardışık geçici hata olursa script durur ve bildirir (ağ / bot kontrolü / Claude girişi).
- Zamanlayıcı ile elle çalışma çakışamaz (`run.lock`); ikinci çalışma "baska bir calisma devam ediyor" der ve çıkar.

### 7. Zamanlayıcı
```
python3 ~/NicheRadar/radar.py schedule install
python3 ~/NicheRadar/radar.py schedule status
```
- macOS: `~/Library/LaunchAgents/com.nicheradar.daily.plist`. Uykudan uyanınca kaçan çalışmayı yapar; Mac kapalıysa yapmaz. Anında test: `launchctl kickstart -k gui/$(id -u)/com.nicheradar.daily` sonra `logs/launchd.out.log`.
- Windows: Task Scheduler görevi "NicheRadar", WakeToRun + StartWhenAvailable açık. Anında test: `schtasks /Run /TN NicheRadar`.
- Linux: cron satırı ekrana yazılır.

### 8. Rapor sayfası (artifact) · ilk yayın
Her `run` sonunda tüm raporlar tek bir HTML sayfaya dökülür: `~/NicheRadar/radar_site.html` (gün gün, en yeni üstte; `site` komutu elle de üretir). Bu sayfayı Artifact aracıyla yayınla:
1. `python3 ~/NicheRadar/radar.py site`
2. Dosyayı **scratchpad** klasörüne kopyala (Artifact aracı çalışma dizini ya da scratchpad altını kabul eder; çalışma dizinine kopyalama, kullanıcının o anki reposunu kirletir): `cp ~/NicheRadar/radar_site.html <scratchpad>/nis_radar_rapor.html`
3. Artifact aracı: `file_path` = o kopya, `favicon` 📡, `description` "Takip edilen YouTube kanallarının günlük video ve Shorts özetleri".
4. Dönen URL'i `~/NicheRadar/config.json` içine `"artifact_url"` olarak yaz ve kullanıcıya ver: "Raporun sabit linki bu; her sabah rapor bilgisayarında güncellenir, sayfaya yansıtmak için bana `/nis_radar yayınla` de."
Sınır (kullanıcıya söyle): sabah koşusu sayfayı kendisi basamaz (yayın aracı sadece açık Claude Code oturumunda var); yayın tek komutla, istediğin sıklıkta.

### 9. Yeniden yayın (`/nis_radar yayınla` / "yayınla" / "sayfayı güncelle")
`site` çalıştır, scratchpad'e kopyala, önce Artifact aracını `action: read` + `url` = config'deki `artifact_url` ile oku (okunmamış artifact'e yayın reddedilir), sonra aynı `url` ile yayınla (aynı link güncellenir, favicon geçme). Config'de `artifact_url` yoksa Bölüm 8'deki ilk yayını yap.

### 10. Kullanıcıya teslim
Şunları açıkça söyle: rapor nerede (klasör + artifact linki), kanal nasıl eklenir (`add-channel`) ve çıkarılır (`remove-channel`), nasıl kapatılır (`schedule remove`), hata olursa ne yapılır (`doctor` + `logs/radar.log`), günlük maliyet (Claude aboneliği içinde, ekstra altyapı yok), `prompt.md` dosyasını kendi işine göre değiştirebileceği (özet formatı ve odak orada).

## Sorun giderme

| Belirti | Sebep | Çözüm |
|---|---|---|
| "Sign in to confirm you're not a bot" | VPN, Private Relay, CGNAT veya yoğun istek | VPN/Relay kapat; `sleep_seconds` artır; son çare `ytdlp_extra_args: ["--cookies-from-browser","chrome"]` (hesap riski, kullanıcıya söyle) |
| O gün rapor dosyası oluşmadı, logda "yeni video yok" | Gerçekten yeni içerik yok | Normal, rapor sadece yeni içerik varsa yazılır. `doctor` "bekleyen" satırına bak |
| "transkript yok (deneme 1/3 …)" | Auto-caption henüz oluşmamış (yeni yükleme), kanal altyazıyı kapatmış ya da dil `sub_langs`'ta yok | Hiçbir şey yapma: sonraki çalışmalarda otomatik tekrar denenir, 3 denemeden sonra "vazgecildi" olur. Kalıcıysa dili `sub_langs`'a ekle ya da `whisper.enabled: true` + ffmpeg |
| "config.json bozuk" / "state.json bozuk" | Elle düzenlerken virgül/tırnak hatası | Mesajdaki satıra bak; yedek `*.corrupt-<zaman>` olarak alınır. state.json silinirse sistem sıfırdan başlar (geçmiş penceresi yeniden uygulanır) |
| "claude: …" durumu / "Claude hicbir ozeti uretemedi" bildirimi | `claude` login düşmüş, CLI eski (bayrak tanımıyor) veya launchd PATH'i eksik | Terminalde `claude -p "ok"` dene; `claude update`; `schedule install` PATH'i yeniden yazar. İçerikler bekleyen listede, sonraki çalışmada tekrar denenir (transkript önbellekte, yt-dlp'ye gidilmez) |
| "Niş Radar hata" bildirimi | Çalışma beklenmedik hatayla bitti | `doctor` → `son hata` satırı; `logs/radar.log` sonundaki traceback |
| "Rapor yazilamadi; N ozet bekleyen listede" | `report_dir` yazılamıyor (izin, iCloud, silinmiş klasör) | Klasörü düzelt ya da `report_dir: ""`; özetler kaybolmaz, sonraki çalışma rapora yazar (`doctor` → `bekleyen ozet`). Özel klasör yazılamazsa rapor `~/NicheRadar/reports`'a düşer |
| "baska bir calisma devam ediyor" | Zamanlayıcı ile elle çalışma çakıştı ya da bayat `run.lock` | Bekle; ölü süreçten kalan / 3 saatten eski kilit otomatik silinir. Gerekirse `rm ~/NicheRadar/run.lock` |
| "N ardisik hata, calisma durduruldu" | Ağ / bot kontrolü ya da Claude girişi düşmüş | `doctor`; VPN/Relay kapat; `claude -p "ok"`. Kalanlar bekleyen listede, sonraki çalışma kaldığı yerden devam eder |
| Kanal çözülemedi | Handle yanlış | YouTube'da kanal sayfasını aç, URL'deki `@handle`'ı ya da herhangi bir videosunun linkini kullan |
| yt-dlp bozuldu | YouTube değişikliği | `uv tool upgrade yt-dlp` |

## Paylaşım
Repo klasörünü (`nis-radar-main`) Claude Code'da çalışma klasörü olarak açan herkes `/nis_radar` yazıp aynı kurulumu yapar; skill `.claude/skills/nis_radar/` altında olduğu için ek kopyalama gerekmez. Her klasörden erişmek isteyen `.claude/skills/nis_radar` klasörünü `~/.claude/skills/` (Windows: `%USERPROFILE%\.claude\skills\`) altına kopyalar. Aynı isimde iki kopya (proje + kullanıcı) varsa `/nis_radar` iki kez listelenir; birini kaldır.
