"""build.py / check_forbidden.py 단위 테스트 — 네트워크 없이 실행."""

import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build  # noqa: E402
import check_forbidden  # noqa: E402

ATOM = """<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>t</title>
  <entry>
    <title type="html">첫 글 &amp; 제목</title>
    <link href="https://dev.example.com/2026/09/02/a/" rel="alternate" type="text/html"/>
    <published>2026-09-02T09:00:00+09:00</published>
    <content type="html"><![CDATA[<p>본문 <b>요약</b>입니다. 두 번째 문장.</p>]]></content>
  </entry>
  <entry>
    <title>둘째</title>
    <link href="https://dev.example.com/b/"/>
    <updated>2026-09-01T00:00:00Z</updated>
    <summary>짧은 요약</summary>
  </entry>
</feed>""".encode("utf-8")

RSS = """<?xml version="1.0"?><rss version="2.0"><channel><title>r</title>
<item><title>RSS 글</title><link>https://x.example.com/p</link>
<pubDate>Tue, 02 Sep 2026 09:00:00 +0900</pubDate><description>&lt;p&gt;설명&lt;/p&gt;</description></item>
</channel></rss>""".encode("utf-8")

BLOGS = [
    {"id": "dev", "title": "개발 블로그", "desc": "d", "url": "https://dev.example.com", "feed": "https://dev.example.com/feed.xml", "emoji": "💻", "status": "live"},
    {"id": "life", "title": "생활 블로그", "desc": "l", "url": "", "feed": "", "emoji": "🏠", "status": "planned"},
]
TEMPLATE = "<main>{{CARDS}}|{{BANNER}}|{{RECENT}}|{{YEAR}}</main>"


class FeedParse(unittest.TestCase):
    def test_atom(self):
        items = build.parse_feed(ATOM)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["title"], "첫 글 & 제목")
        self.assertEqual(items[0]["url"], "https://dev.example.com/2026/09/02/a/")
        self.assertEqual(items[0]["date"].isoformat(), "2026-09-02")
        self.assertEqual(items[0]["summary"], "본문 요약입니다. 두 번째 문장.")
        self.assertEqual(items[1]["date"].isoformat(), "2026-09-01")

    def test_rss(self):
        items = build.parse_feed(RSS)
        self.assertEqual(items[0]["title"], "RSS 글")
        self.assertEqual(items[0]["date"].isoformat(), "2026-09-02")
        self.assertEqual(items[0]["summary"], "설명")

    def test_fetch_failure_returns_empty_and_does_not_raise(self):
        with mock.patch.object(build, "fetch", side_effect=OSError("boom")):
            self.assertEqual(build.load_feed("https://x/feed.xml", 5, offline=False), [])

    def test_parse_failure_returns_empty(self):
        with mock.patch.object(build, "fetch", return_value=b"<not xml"):
            self.assertEqual(build.load_feed("https://x/feed.xml", 5, offline=False), [])

    def test_limit(self):
        with mock.patch.object(build, "fetch", return_value=ATOM):
            self.assertEqual(len(build.load_feed("https://x/feed.xml", 1, offline=False)), 1)

    def test_shorten(self):
        s = "가" * 200
        self.assertTrue(build.shorten(s).endswith("…"))
        self.assertLessEqual(len(build.shorten(s)), build.SUMMARY_MAX + 1)
        self.assertEqual(build.shorten("짧다"), "짧다")


class Render(unittest.TestCase):
    def test_only_live_blogs_get_cards_and_no_soon_card(self):
        out = build.render_index(TEMPLATE, BLOGS, {}, {}, 2026)
        self.assertEqual(out.count('class="card"'), 1)
        self.assertIn('href="https://dev.example.com"', out)
        self.assertNotIn("생활 블로그", out)
        self.assertNotIn("준비 중", out)
        self.assertNotIn('href=""', out)

    def test_recent_rendered_statically(self):
        posts = build.parse_feed(ATOM)
        out = build.render_index(TEMPLATE, BLOGS, {"dev": posts}, {}, 2026)
        self.assertEqual(out.count('class="post-link"'), 2)
        self.assertIn("개발 블로그 최신 글", out)
        self.assertIn('<time datetime="2026-09-02">', out)
        self.assertIn("첫 글 &amp; 제목", out)
        self.assertNotIn("<script", out)

    def test_empty_feed_keeps_card_and_omits_recent_section(self):
        out = build.render_index(TEMPLATE, BLOGS, {"dev": []}, {}, 2026)
        self.assertIn('class="card"', out)
        self.assertNotIn("최신 글", out)

    def test_banner_off_by_default_and_on_when_enabled(self):
        off = build.render_index(TEMPLATE, BLOGS, {}, {"enabled": False, "title": "게임", "url": "https://g"}, 2026)
        self.assertNotIn("promo", off)
        no_url = build.render_index(TEMPLATE, BLOGS, {}, {"enabled": True, "title": "게임", "url": ""}, 2026)
        self.assertNotIn("promo", no_url)
        on = build.render_index(TEMPLATE, BLOGS, {}, {"enabled": True, "title": "게임", "url": "https://g", "label": "직접 만든 게임"}, 2026)
        self.assertEqual(on.count("promo-card"), 1)
        self.assertIn("직접 만든 게임", on)

    def test_year(self):
        self.assertIn("|2026<", build.render_index(TEMPLATE, BLOGS, {}, {}, 2026))


class Forbidden(unittest.TestCase):
    def test_email_allowed_but_company_strings_flagged(self):
        text = 'a <a href="mailto:blog@alreadymorning.com">blog@alreadymorning.com</a>\n벌써아침\n사업자등록번호 818-10-02994\n<a href="https://alreadymorning.com">x</a>\n'
        hits = check_forbidden.scan_text(text)
        self.assertEqual([h[1] for h in hits], ["벌써아침", "818-10-02994", "alreadymorning.com"])
        self.assertEqual([h[0] for h in hits], [2, 3, 4])

    def test_clean(self):
        self.assertEqual(check_forbidden.scan_text("© 2026 Haze · blog@alreadymorning.com"), [])


if __name__ == "__main__":
    unittest.main()
