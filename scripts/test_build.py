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
TEMPLATE = "<head><meta name=\"description\" content=\"{{META_DESC}}\"></head><main>{{BLOGS}}|{{BANNER}}|{{YEAR}}</main>"


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
    """허브 #9 — 블로그 하나 = 블록 하나(이름 링크 + 최신 글). planned 는 블록 자체가 없다."""

    def test_only_live_blogs_get_blocks_and_no_planned_block(self):
        out = build.render_index(TEMPLATE, BLOGS, {}, {}, 2026)
        self.assertEqual(out.count('class="blog-block"'), 1)
        self.assertIn('<h2 class="blog-title"><a href="https://dev.example.com"', out)
        self.assertNotIn("생활 블로그", out)
        self.assertNotIn("준비 중", out)
        self.assertNotIn('href=""', out)
        self.assertNotIn('class="card"', out)  # 옛 카드 섹션 없음

    def test_recent_posts_inside_block_title_and_date_only(self):
        posts = build.parse_feed(ATOM)
        out = build.render_index(TEMPLATE, BLOGS, {"dev": posts}, {}, 2026)
        block = out[out.index('class="blog-block"'):out.index("</section>")]
        self.assertEqual(block.count('class="post-link"'), 2)
        self.assertIn('<time datetime="2026-09-02">2026-09-02</time>', block)
        self.assertIn("첫 글 &amp; 제목", block)
        self.assertNotIn("본문 요약입니다", block)  # 요약문은 넣지 않는다 (#9)
        self.assertNotIn("최신 글", out[out.index("<main>"):])  # 별도 '최신 글' 섹션 없음
        self.assertNotIn("<script", out)

    def test_empty_feed_keeps_block_and_link_but_no_list(self):
        out = build.render_index(TEMPLATE, BLOGS, {"dev": []}, {}, 2026)
        self.assertIn('class="blog-block"', out)
        self.assertIn('href="https://dev.example.com"', out)
        self.assertNotIn('class="post-list"', out)

    def test_meta_desc_is_topics_not_operator(self):
        out = build.render_index(TEMPLATE, BLOGS, {}, {}, 2026)
        self.assertIn('content="개발 블로그의 최신 글 모음. 각 블로그의 새 글을 한곳에서 봅니다."', out)
        self.assertNotIn("Haze가", out)
        self.assertNotIn("운영", out)
        self.assertNotIn("{{META_DESC}}", out)

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

    def test_default_limit_is_five(self):
        import argparse  # noqa: F401
        src = Path(build.__file__).read_text(encoding="utf-8")
        self.assertIn('"--limit", type=int, default=5', src)


class NoSelfIntro(unittest.TestCase):
    """허브 #9 — 자기소개·운영자 서술 금지 (자기 지칭). 템플릿과 blogs.json 을 직접 본다."""
    ROOT = Path(__file__).resolve().parent.parent

    def test_template_has_no_operator_intro(self):
        html = (self.ROOT / "templates/index.html").read_text(encoding="utf-8")
        for bad in ("개발자 한 사람", "운영하는", "개발자 Haze가", "입구입니다"):
            self.assertNotIn(bad, html, bad)
        self.assertIn("{{META_DESC}}", html)
        self.assertIn("{{BLOGS}}", html)
        self.assertNotIn("{{CARDS}}", html)
        self.assertNotIn("{{RECENT}}", html)

    def test_blog_desc_is_topics_only(self):
        import json
        for b in json.loads((self.ROOT / "data/blogs.json").read_text(encoding="utf-8")):
            self.assertNotRegex(b["desc"], r"합니다|입니다|기록|정리합", b["id"])


class HeadSlots(unittest.TestCase):
    """애드센스·검색엔진 인증 슬롯 (이슈 #3)."""

    def test_empty_site_emits_nothing(self):
        # 파일 없음/빈 dict/빈 문자열 모두 아무것도 내지 않는다 (빈 메타 금지)
        for site in ({}, {"adsense_client": "", "google_site_verification": "", "naver_site_verification": ""}):
            self.assertEqual(build.render_head_extra(site), "")
            self.assertIsNone(build.ads_txt(site))

    def test_values_emit_tags_and_ads_txt(self):
        site = {
            "adsense_client": "ca-pub-8137295084344862",
            "google_site_verification": "gsv_abc123",
            "naver_site_verification": "nsv_def456",
        }
        head = build.render_head_extra(site)
        self.assertIn("pagead2.googlesyndication.com/pagead/js/adsbygoogle.js", head)
        self.assertIn("client=ca-pub-8137295084344862", head)
        self.assertIn('crossorigin="anonymous"', head)
        self.assertIn('<meta name="google-site-verification" content="gsv_abc123" />', head)
        self.assertIn('<meta name="naver-site-verification" content="nsv_def456" />', head)
        # ads.txt: ca- 제거한 pub-… + 고정 exchange ID, 한 줄
        ads = build.ads_txt(site)
        self.assertEqual(ads.strip(), "google.com, pub-8137295084344862, DIRECT, f08c47fec0942fa0")
        self.assertEqual(ads.count("\n"), 1)

    def test_partial_only_emits_present_slots(self):
        # 인증 코드만 있고 애드센스는 비어 있으면 → meta 만, 스크립트·ads.txt 없음
        site = {"adsense_client": "", "google_site_verification": "only_gsv", "naver_site_verification": ""}
        head = build.render_head_extra(site)
        self.assertIn('google-site-verification" content="only_gsv"', head)
        self.assertNotIn("adsbygoogle", head)
        self.assertNotIn("naver-site-verification", head)
        self.assertIsNone(build.ads_txt(site))

    def test_head_extra_injected_into_both_templates(self):
        head = "  <meta name='google-site-verification' content='X' />"
        idx = build.render_index("<head>{{HEAD_EXTRA}}</head>", BLOGS, {}, {}, 2026, head)
        self.assertIn("content='X'", idx)
        priv = build.render_privacy("<head>{{HEAD_EXTRA}}</head>", head)
        self.assertIn("content='X'", priv)

    def test_empty_head_extra_leaves_no_placeholder_or_adsense(self):
        for out in (
            build.render_index("<head>\n{{HEAD_EXTRA}}\n<link/>\n</head>", BLOGS, {}, {}, 2026, ""),
            build.render_privacy("<head>\n{{HEAD_EXTRA}}\n<link/>\n</head>", ""),
        ):
            self.assertNotIn("{{HEAD_EXTRA}}", out)
            self.assertNotIn("adsbygoogle", out)
            self.assertNotIn("site-verification", out)


class Forbidden(unittest.TestCase):
    def test_email_allowed_but_company_strings_flagged(self):
        text = 'a <a href="mailto:blog@alreadymorning.com">blog@alreadymorning.com</a>\n벌써아침\n사업자등록번호 818-10-02994\n<a href="https://alreadymorning.com">x</a>\n'
        hits = check_forbidden.scan_text(text)
        self.assertEqual([h[1] for h in hits], ["벌써아침", "818-10-02994", "alreadymorning.com"])
        self.assertEqual([h[0] for h in hits], [2, 3, 4])

    def test_clean(self):
        self.assertEqual(check_forbidden.scan_text("© 2026 Haze · blog@alreadymorning.com"), [])


class DesignSyncTest(unittest.TestCase):
    """허브 #6 — blog-dev 디자인 시스템 동기화 계약."""
    ROOT = Path(__file__).resolve().parent.parent

    def test_templates_have_favicon_and_single_webfont(self):
        for name in ("templates/index.html", "privacy/index.html"):
            html = (self.ROOT / name).read_text(encoding="utf-8")
            self.assertIn('rel="icon" href="/favicon.ico"', html, name)
            self.assertIn('rel="apple-touch-icon"', html, name)
            self.assertEqual(html.count("pretendardvariable-dynamic-subset"), 1, name)
            self.assertNotIn("googleapis.com/css", html, name)  # 웹폰트는 1종만

    def test_static_ships_favicon(self):
        self.assertIn("favicon.ico", build.STATIC)
        for f in ("favicon.ico", "assets/favicon.svg", "assets/apple-touch-icon.png"):
            self.assertTrue((self.ROOT / f).exists(), f)

    def test_css_sync_block_present(self):
        css = (self.ROOT / "assets/css/style.css").read_text(encoding="utf-8")
        self.assertIn("[동기화 블록 시작]", css)
        self.assertIn("--accent: #3f5fcf", css)
        self.assertEqual(css.count("@media (prefers-color-scheme: dark)"), 1)
        self.assertIn('font-family: "Pretendard Fallback"', css)


if __name__ == "__main__":
    unittest.main()
