# Niş Radar

Takip ettiğin YouTube kanallarının (uzun video + Shorts) yeni içeriklerini her sabah bulur, transkriptini çeker, Claude ile özetler ve tek bir Markdown rapor bırakır. Kendi bilgisayarında çalışır, sunucu yok, API anahtarı yok.

## Gereksinimler
- Claude Code kurulu ve giriş yapılmış (`claude --version`)
- Python 3.9+ (macOS'ta hazır)
- `uv` (yt-dlp'yi kurmak için)

## Kurulum (Claude Code ile, önerilen)
1. Bu klasörü `~/.claude/skills/nis_radar/` altına kopyala (Windows: `%USERPROFILE%\.claude\skills\nis_radar\`).
2. Claude Code'u aç, `/nis_radar` yaz. Claude bağımlılıkları kurar; kanallarını (ya da nişini) sorar, geçmişe kaç gün bakılacağını (7 / 30 / hiç) ve rapor saatini sorar, ilk raporu üretir, zamanlayıcıyı kurar. Sadece YouTube (video + Shorts).

## Kurulum (elle)
Windows'ta (Git Bash) `python3` yerine `python`; `~/NicheRadar` yolu aynen çalışır.
```
uv tool install "yt-dlp[default,curl-cffi]"
python3 scripts/radar.py install
python3 ~/NicheRadar/radar.py add-channel @nicksaraev https://www.youtube.com/@NateHerk   # handle, kanal veya video linki
python3 ~/NicheRadar/radar.py check-channel @aday        # eklemeden dogrula
python3 ~/NicheRadar/radar.py remove-channel @nicksaraev
python3 ~/NicheRadar/radar.py doctor
python3 ~/NicheRadar/radar.py run --dry-run              # kesif
python3 ~/NicheRadar/radar.py run                        # ilk calisma: config'deki first_run_days (7/30/0) kadar gecmis
python3 ~/NicheRadar/radar.py schedule install
```

## Nasıl çalışır
1. **Keşif:** her kanalın `videos` ve `shorts` sekmesinden son 10 içerik (yt-dlp flat listing; API anahtarı gerekmez). RSS yedek. İlk çalışmada `first_run_days` (7 / 30 / 0) penceresi uygulanır; günlük tavanı (`max_per_run`) aşan içerik bekleyen listede tutulur ve sonraki çalışmalarda önce işlenir. Kanallar sırayla pay alır.
2. **Transkript:** `yt-dlp --skip-download --write-auto-subs`. Video inmez, sadece VTT altyazı. Tekrarlı satırlar temizlenir.
3. **Özet:** her video için `claude -p` çağrısı, `prompt.md` şablonuyla. Sonra tek bir "günün öne çıkanları" özeti (`digest_prompt.md`).
4. **Rapor:** `~/NicheRadar/reports/YYYY-MM-DD.md` + macOS bildirimi + isteğe bağlı Telegram. Ayrıca tüm günler tek HTML sayfada: `~/NicheRadar/radar_site.html` (`site` komutu); Claude Code'da `/nis_radar yayınla` deyince sabit bir artifact linkine basılır.
5. **Durum:** her video için "altyazı / transkript yok / eski / hata" satırı rapor sonunda. Yeni içerik yoksa o gün rapor dosyası oluşmaz, `logs/radar.log` "yeni video yok" yazar.

## Sınırlar (dürüst)
- Cloud IP'lerde çalışmaz; YouTube engeller. Kendi makinen şart.
- Altyazısı kapalı kanallarda transkript gelmez. Whisper yedeği opsiyonel (ffmpeg gerekir, `whisper.enabled`).
- Instagram bu pakette yok. Başkalarının Reels'i için resmi yol yok; kendi hesabınla scraper kullanmak ban riski. İstersen Apify'ın login gerektirmeyen Reels transkript aktörleri (video başı ~$0.05) ayrı bir adım olarak eklenebilir.
- Mac kapalıysa o günün çalışması olmaz; uykudaysa uyanınca yapılır.
