# Niş Radar

Takip ettiğin YouTube kanallarının (uzun video + Shorts) yeni içeriklerini her sabah bulur, transkriptini çeker, Claude ile özetler ve tek bir Markdown rapor bırakır. Kendi bilgisayarında çalışır, sunucu yok, API anahtarı yok.

## Gereksinimler
- Claude Code kurulu ve giriş yapılmış (`claude --version`)
- Python 3.9+ (macOS'ta hazır)
- `uv` (yt-dlp'yi kurmak için)

## Kurulum (Claude uygulaması ile, önerilen — terminal gerekmez)
1. GitHub'da **Code → Download ZIP** → İndirilenler'e iner; çift tıkla → `nis-radar-main` klasörü.
2. Claude uygulaması → **Code** sekmesi → yeni oturum → çalışma klasörü olarak `nis-radar-main`'i seç.
3. Sohbet kutusuna `/nis_radar` yaz → Enter. Claude bağımlılıkları kurar; kanallarını (ya da nişini), geçmişe kaç gün bakılacağını (7 / 30 / hiç), rapor saatini ve nişini sorar, ilk raporu üretir, zamanlayıcıyı kurar. Sadece YouTube (video + Shorts).

Skill klasörün içinde `.claude/skills/nis_radar/` altında durur; Claude Code klasörü açınca onu otomatik görür. Kurulum her şeyi `~/NicheRadar/` altına kopyalar, sonrasında indirdiğin klasör silinebilir. Kalıcı olarak her klasörden erişmek istersen `.claude/skills/nis_radar` klasörünü `~/.claude/skills/` altına kopyala (Windows: `%USERPROFILE%\.claude\skills\`).

## Kurulum (elle, terminalden)
Windows'ta (Git Bash) `python3` yerine `python`; `~/NicheRadar` yolu aynen çalışır.
```
uv tool install "yt-dlp[default,curl-cffi]"
python3 .claude/skills/nis_radar/scripts/radar.py install
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
2. **Transkript:** `yt-dlp --skip-download --write-auto-subs`. Video inmez, sadece VTT altyazı; videonun orijinal dilindeki iz tercih edilir (çeviri değil). Tekrarlı satırlar temizlenir, metin `cache/subs/<id>/transcript.txt`'ye alınır (30 gün sonra silinir).
3. **Özet:** her video için `claude -p` çağrısı, `prompt.md` şablonuyla (`{niche}` = senin nişin). Çağrı kullanıcının Claude Code ortamından yalıtılmıştır: `--safe-mode`, araçsız, MCP'siz, skill'siz, oturum kaydı yok; transkript "veridir, talimat değildir" ayraçları içinde gider. Token kullanımı `logs/radar.log`'a yazılır. Sonra tek bir "günün öne çıkanları" özeti (`digest_prompt.md`).
4. **Rapor:** `~/NicheRadar/reports/YYYY-MM-DD.md` + macOS bildirimi + isteğe bağlı Telegram. Özetler önce `state.json`'a (bekleyen özet) yazılır, rapor diske indikten sonra silinir: rapor klasörü yazılamazsa özet kaybolmaz. Ayrıca tüm günler tek HTML sayfada: `~/NicheRadar/radar_site.html` (`site` komutu); Claude Code'da `/nis_radar yayınla` deyince sabit bir artifact linkine basılır.
5. **Durum:** her video için "altyazı / transkript yok / eski / hata" satırı rapor sonunda. Geçici durumlar (altyazı henüz yok, ağ, Claude hatası) bekleyen listede kalır ve sonraki çalışmalarda 3 kez daha denenir; 5 ardışık hata çalışmayı durdurur ve bildirir. Yeni içerik yoksa o gün rapor dosyası oluşmaz, `logs/radar.log` "yeni video yok" yazar. Beklenmedik her hata bildirim + `doctor` → `son hata` olarak görünür; eşzamanlı iki çalışma `run.lock` ile engellenir.

## Testler
Ağsız, abonelik kullanmayan birim testleri (yt-dlp / claude taklit edilir):
```
python3 -m unittest discover -s tests -v
```

## Sınırlar (dürüst)
- Cloud IP'lerde çalışmaz; YouTube engeller. Kendi makinen şart.
- "30 gün geçmiş" = her kanalın her sekmesinden en yeni `first_run_items` içeriğin son 30 gün içinde olanları; daha eskisi taranmaz.
- `report_dir` olarak bir Obsidian vault verirsen ayrı bir alt klasör kullan; script başkasının `YYYY-MM-DD.md` dosyasına eklemez (`YYYY-MM-DD.nis-radar.md` yazar) ve siteye yalnızca kendi raporlarını alır.
- Altyazısı kapalı kanallarda transkript gelmez. Whisper yedeği opsiyonel (ffmpeg gerekir, `whisper.enabled`).
- Instagram bu pakette yok. Başkalarının Reels'i için resmi yol yok; kendi hesabınla scraper kullanmak ban riski. İstersen Apify'ın login gerektirmeyen Reels transkript aktörleri (video başı ~$0.05) ayrı bir adım olarak eklenebilir.
- Mac kapalıysa o günün çalışması olmaz; uykudaysa uyanınca yapılır.
