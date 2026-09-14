"""radar.py icin agsiz birim testleri (stdlib unittest).

Calistir:  python3 -m unittest discover -s tests -v
yt-dlp, claude, osascript ve time.sleep taklit edilir; HOME gecici klasore alinir.
"""
from __future__ import annotations

import datetime as dt
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import radar  # noqa: E402

CHANNELS = [
    {"name": "Nate Herk | AI Automation", "id": "UC2ojq-nuP8ceeHqiroeKhBA", "handle": "@nateherk"},
    {"name": "Matt Wolfe", "id": "UChpleBmo18P08aKCIgti38g", "handle": "@mreflow"},
]
TODAY = dt.date.today()


def vid(ch_idx: int, tab: str, k: int) -> str:
    """11 karakterlik sahte video id: V<kanal><sekme><sira>."""
    return "V%d%s%08d" % (ch_idx, tab[0].upper(), k)


def meta_for(item_id: str, channel: str = "Kanal", days_old: int = 0) -> dict:
    return {
        "upload_date": (TODAY - dt.timedelta(days=days_old)).strftime("%Y%m%d"),
        "duration": "60", "view_count": "100", "channel": channel, "title": "Baslik %s" % item_id,
    }


class RadarCase(unittest.TestCase):
    """Gecici HOME + taklit araclar. Her test kendi klasorunde calisir."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name) / "NicheRadar"
        self.home.mkdir()
        for name, sub in (("HOME", ""), ("CONFIG", "config.json"), ("STATE", "state.json"),
                          ("REPORTS", "reports"), ("LOGS", "logs"), ("CACHE", "cache")):
            p = mock.patch.object(radar, name, self.home / sub if sub else self.home)
            p.start()
            self.addCleanup(p.stop)
        for name in ("prompt.md", "digest_prompt.md"):
            shutil.copy(ROOT / "scripts" / name, self.home / name)
        self.notifications: list = []
        patches = [
            mock.patch.object(radar.time, "sleep", lambda *a, **k: None),
            mock.patch.object(radar, "notify", lambda cfg, title, body: self.notifications.append((title, body))),
            mock.patch.object(radar, "ytdlp_bin", lambda: "yt-dlp"),
            mock.patch.object(radar, "claude_bin", lambda: "claude"),
            mock.patch.object(radar, "print", lambda *a, **k: None, create=True),  # stdout sessiz; log dosyasi kalir
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        self.write_config()

    # ---- yardimcilar
    def write_config(self, **over) -> dict:
        cfg = {"channels": [dict(c) for c in CHANNELS], "first_run_days": 7, "first_run_items": 1,
               "discover_items": 10, "max_per_run": 20, "max_age_days": 14, "sleep_seconds": 0}
        cfg.update(over)
        radar.save_json(radar.CONFIG, cfg)
        return cfg

    def read_state(self) -> dict:
        return json.loads(radar.STATE.read_text(encoding="utf-8"))

    def write_state(self, state: dict) -> None:
        radar.save_json(radar.STATE, state)

    @staticmethod
    def discover_n(n: int):
        """Her kanal/sekme icin n sahte icerik dondur (en yeni once)."""
        def _d(channel, tab, limit):
            idx = next(i for i, c in enumerate(CHANNELS) if c["id"] == channel["id"])
            return [{"id": vid(idx, tab, k), "title": "%s %s %d" % (channel["name"], tab, k), "tab": tab}
                    for k in range(1, n + 1)]
        return _d

    @staticmethod
    def fetch_ok(cfg, item_id):
        return meta_for(item_id), "kelime " * 200, "altyazi"

    @staticmethod
    def ask_ok(cfg, prompt, timeout=420):
        return "**Tek cümle:** ozet"

    def run_once(self, discover=None, fetch=None, ask=None, limit=0, only="", no_llm=False, dry_run=False):
        args = SimpleNamespace(dry_run=dry_run, no_llm=no_llm, limit=limit, only=only)
        with mock.patch.object(radar, "discover_tab", side_effect=discover or self.discover_n(3)) as d, \
             mock.patch.object(radar, "fetch_transcript", side_effect=fetch or self.fetch_ok) as f, \
             mock.patch.object(radar, "ask_claude", side_effect=ask or self.ask_ok) as a:
            radar.cmd_run(args)
        return SimpleNamespace(discover=d, fetch=f, ask=a)

    def report_files(self) -> list:
        return sorted(p for p in radar.REPORTS.glob("*.md")) if radar.REPORTS.exists() else []

    def log_text(self) -> str:
        p = radar.LOGS / "radar.log"
        return p.read_text(encoding="utf-8") if p.exists() else ""


class FirstRunTests(RadarCase):
    def test_first_run_happy_path(self):
        """7 gun / sekme basina 1 icerik: 4 ozet, kalan 8 icerik baseline, rapor marker ile baslar."""
        calls = self.run_once()
        state = self.read_state()
        self.assertTrue(state["initialized"])
        statuses = [v["status"] for v in state["seen"].values()]
        self.assertEqual(statuses.count("altyazi"), 4)
        self.assertEqual(statuses.count("baseline"), 8)
        self.assertEqual(state.get("backlog", []), [])
        self.assertEqual(calls.fetch.call_count, 4)
        reps = self.report_files()
        self.assertEqual(len(reps), 1)
        text = reps[0].read_text(encoding="utf-8")
        self.assertTrue(text.startswith("# Niche Radar · %s" % TODAY.isoformat()))
        self.assertIn("**4 yeni içerik**, 4 özet", text)
        self.assertTrue((self.home / "radar_site.html").exists())
        self.assertEqual(len(self.notifications), 1)

    def test_dry_run_leaves_no_state(self):
        self.run_once(dry_run=True)
        self.assertFalse(radar.STATE.exists())
        self.assertEqual(self.report_files(), [])


if __name__ == "__main__":
    unittest.main()
