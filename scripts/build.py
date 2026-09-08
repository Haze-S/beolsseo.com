#!/usr/bin/env python3
"""beolsseo.com 허브 빌드 (이슈 #1)

- data/blogs.json 의 status=live 블로그만 **블로그 블록**(이름 링크 + 최신 글 5개)으로 렌더링한다 (허브 #9 — 카드와 최신 글 섹션을 하나로 합침).
  그 외 상태(planned 등)는 블록 자체를 만들지 않는다 — 빈 링크·"준비 중" 블록 금지(애드센스 심사 감점).
- 각 live 블로그의 feed(Atom/RSS)를 **빌드 타임**에 읽어 최신 글 목록을 정적 HTML 로 넣는다. 요약문은 넣지 않는다(제목+날짜만, #9).
  런타임 JS 페치 없음 — 크롤러가 본문에서 그대로 읽는다.
- 피드 조회·파싱 실패 시 빌드를 깨뜨리지 않는다: 경고만 남기고 그 블로그의 글 목록을 비운다(카드 링크는 유지).
- data/banner.json enabled=true 일 때만 자기 제품 배너 1개를 렌더링한다.
- 결과는 dist/ (index.html + privacy/ + assets/ + robots.txt + sitemap.xml + CNAME + .nojekyll).

표준 라이브러리만 사용한다.

사용: python3 scripts/build.py [--offline] [--out dist] [--limit 8]
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import shutil
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UA = "Mozilla/5.0 (compatible; beolsseo-hub-build/1.0; +https://beolsseo.com)"
# privacy 는 STATIC 복사가 아니라 렌더(HEAD_EXTRA 주입)로 처리한다 — 아래 build() 참조.
STATIC = ["assets", "robots.txt", "sitemap.xml", "CNAME", ".nojekyll", "favicon.ico"]  # favicon.ico: scripts/favicon.py 산출물 (#6)
ATOM = "{http://www.w3.org/2005/Atom}"
SUMMARY_MAX = 110  # shorten() 용 — 허브 목록에는 요약을 쓰지 않는다(#9). 다른 용도 대비 함수만 유지
ADS_TXT_EXCHANGE = "f08c47fec0942fa0"  # Google AdSense 고정 relationship ID


def esc(s: object) -> str:
    return html.escape(str("" if s is None else s), quote=True)


def log(msg: str) -> None:
    print(msg, file=sys.stderr)


# ---------- 피드 ----------

def fetch(url: str, timeout: int = 20) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


INLINE_TAGS = r"(?:a|b|i|em|strong|code|span|small|sup|sub|mark|abbr|u|s|del|ins|kbd)"


def strip_html(s: str) -> str:
    """태그 제거. 인라인 태그는 붙여 쓰고(요약<b>입</b>니다 → 요약입니다), 블록 태그는 공백으로 나눈다."""
    s = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", s, flags=re.DOTALL | re.IGNORECASE)
    s = re.sub(rf"</?{INLINE_TAGS}(?:\s[^>]*)?>", "", s, flags=re.IGNORECASE)
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def shorten(s: str, n: int = SUMMARY_MAX) -> str:
    s = s.strip()
    if len(s) <= n:
        return s
    cut = s[:n]
    # 단어·문장 경계에서 자르되 너무 짧아지면 그냥 자른다
    for sep in ("다. ", ". ", " "):
        i = cut.rfind(sep)
        if i >= n * 0.6:
            cut = cut[: i + (len(sep) - 1 if sep != " " else 0)]
            break
    return cut.rstrip(" ,·—-") + "…"


def parse_date(s: str | None) -> dt.date | None:
    if not s:
        return None
    s = s.strip()
    try:
        return dt.datetime.fromisoformat(s.replace("Z", "+00:00")).date()
    except ValueError:
        pass
    for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z"):
        try:
            return dt.datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    m = re.match(r"(\d{4}-\d{2}-\d{2})", s)
    return dt.date.fromisoformat(m.group(1)) if m else None


def parse_feed(raw: bytes) -> list[dict]:
    """Atom 또는 RSS 2.0 → [{title, url, date, summary}] (피드 순서 유지)."""
    root = ET.fromstring(raw)
    items: list[dict] = []
    if root.tag == f"{ATOM}feed":
        for e in root.findall(f"{ATOM}entry"):
            link = ""
            for l in e.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate" and l.get("href"):
                    link = l.get("href")
                    break
            title = (e.findtext(f"{ATOM}title") or "").strip()
            date = parse_date(e.findtext(f"{ATOM}published") or e.findtext(f"{ATOM}updated"))
            summary = e.findtext(f"{ATOM}summary") or e.findtext(f"{ATOM}content") or ""
            items.append({"title": strip_html(title), "url": link, "date": date, "summary": strip_html(summary)})
    else:
        channel = root.find("channel")
        for it in (channel.findall("item") if channel is not None else []):
            items.append({
                "title": strip_html(it.findtext("title") or ""),
                "url": (it.findtext("link") or "").strip(),
                "date": parse_date(it.findtext("pubDate")),
                "summary": strip_html(it.findtext("description") or ""),
            })
    return [i for i in items if i["title"] and i["url"]]


def load_feed(url: str, limit: int, offline: bool) -> list[dict]:
    """실패해도 예외를 내지 않는다 — 빈 목록 반환."""
    if offline:
        log(f"[feed] offline — {url} 건너뜀")
        return []
    try:
        items = parse_feed(fetch(url))
    except Exception as e:  # noqa: BLE001 — 어떤 실패든 빌드는 계속
        log(f"[feed] ⚠️ {url} 조회/파싱 실패 → 목록 비움: {type(e).__name__}: {e}")
        return []
    log(f"[feed] {url} → {len(items)}건 (상위 {limit}건 사용)")
    return items[:limit]


# ---------- 애드센스·인증 슬롯 (이슈 #3) ----------

def render_head_extra(site: dict) -> str:
    """값이 채워진 슬롯만 head 태그로 출력한다. 빈 값이면 아무것도 내지 않는다
    — 빈 메타/빈 스크립트가 나가면 애드센스·서치콘솔 검증이 깨진다(#3, blog-dev #26 교훈).
    부분 입력(예: 인증만)도 있는 것만 출력한다."""
    lines: list[str] = []
    client = str(site.get("adsense_client") or "").strip()
    if client:
        lines.append(
            '    <script async '
            f'src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={esc(client)}" '
            'crossorigin="anonymous"></script>'
        )
    gsv = str(site.get("google_site_verification") or "").strip()
    if gsv:
        lines.append(f'    <meta name="google-site-verification" content="{esc(gsv)}" />')
    nsv = str(site.get("naver_site_verification") or "").strip()
    if nsv:
        lines.append(f'    <meta name="naver-site-verification" content="{esc(nsv)}" />')
    return "\n".join(lines)


def ads_txt(site: dict) -> str | None:
    """adsense_client 가 있을 때만 ads.txt 내용을 만든다. 없으면 None → 파일 자체를 만들지 않는다
    (빈 ads.txt 를 200 으로 서빙하지 않는다, #3). ca-pub-… → ads.txt 에는 ca- 를 뗀 pub-… 를 쓴다."""
    client = str(site.get("adsense_client") or "").strip()
    if not client:
        return None
    pub = client[3:] if client.startswith("ca-") else client
    return f"google.com, {pub}, DIRECT, {ADS_TXT_EXCHANGE}\n"


# ---------- 렌더 ----------

def render_blog_block(b: dict, posts: list[dict]) -> str:
    """블로그 하나 = 블록 하나 (허브 #9). 이름(사이트 링크) + 주제 한 줄 + 최신 글 목록(제목·날짜).
    피드가 비면(조회 실패 포함) 목록만 비우고 블록·링크는 유지한다 — load_feed() 가 빌드를 깨뜨리지 않는 것과 짝."""
    lis = []
    for p in posts:
        d = p["date"].isoformat() if p["date"] else ""
        date_html = f'<time datetime="{d}">{d}</time>' if d else ""
        lis.append(
            f'            <li><a class="post-link" href="{esc(p["url"])}" rel="noopener">{esc(p["title"])}</a>{date_html}</li>'
        )
    list_html = ("          <ul class=\"post-list\">\n" + "\n".join(lis) + "\n          </ul>\n") if lis else ""
    return (
        f'      <section class="blog-block" id="blog-{esc(b["id"])}">\n'
        f'        <div class="wrap">\n'
        f'          <h2 class="blog-title"><a href="{esc(b["url"])}" rel="noopener">'
        f'<span class="blog-emoji" aria-hidden="true">{esc(b.get("emoji", ""))}</span>{esc(b["title"])}<span class="blog-arrow" aria-hidden="true"> →</span></a></h2>\n'
        f'          <p class="blog-desc">{esc(b.get("desc", ""))}</p>\n'
        + list_html
        + f'        </div>\n'
        f'      </section>'
    )


def render_meta_desc(live: list[dict]) -> str:
    """검색 결과에 뜨는 문구 — 운영자 소개가 아니라 다루는 주제(#9). live 블로그 이름으로 만든다."""
    names = [re.sub(r"\s*블로그$", "", b["title"]) for b in live]  # "개발 블로그" → "개발"
    joined = " · ".join(names) if names else "주제별"
    return esc(f"{joined} 블로그의 최신 글 모음. 각 블로그의 새 글을 한곳에서 봅니다.")


def render_banner(banner: dict) -> str:
    """자기 제품 배너 — enabled 이고 url·title 이 있을 때만. 애드센스 광고와 구분되도록 라벨을 붙인다."""
    if not banner or not banner.get("enabled") or not banner.get("url") or not banner.get("title"):
        return ""
    return (
        f'      <section class="section promo" aria-label="{esc(banner.get("label", "직접 만든 것"))}">\n'
        f'        <div class="wrap">\n'
        f'          <a class="promo-card" href="{esc(banner["url"])}" rel="noopener">\n'
        f'            <span class="promo-label">{esc(banner.get("label", "직접 만든 것"))}</span>\n'
        f'            <span class="promo-title">{esc(banner["title"])}</span>\n'
        f'            <span class="promo-desc">{esc(banner.get("desc", ""))}</span>\n'
        f'          </a>\n'
        f'        </div>\n'
        f'      </section>'
    )


def _clean_blanks(out: str) -> str:
    # 빈 플레이스홀더가 남긴 빈 줄 정리
    return re.sub(r"\n[ \t]*\n(?=[ \t]*\n)", "\n", out)


def render_index(template: str, blogs: list[dict], feeds: dict[str, list[dict]], banner: dict,
                 year: int, head_extra: str = "") -> str:
    live = [b for b in blogs if b.get("status") == "live" and b.get("url")]
    blocks = "\n".join(render_blog_block(b, feeds.get(b["id"], [])) for b in live)
    out = template
    out = out.replace("{{HEAD_EXTRA}}", head_extra)
    out = out.replace("{{META_DESC}}", render_meta_desc(live))
    out = out.replace("{{BLOGS}}", blocks)
    out = out.replace("{{BANNER}}", render_banner(banner))
    out = out.replace("{{YEAR}}", str(year))
    return _clean_blanks(out)


def render_privacy(template: str, head_extra: str = "") -> str:
    """privacy 페이지도 head 슬롯을 주입한다 — 애드센스·인증은 두 페이지 모두에 있어야 한다(#3)."""
    return _clean_blanks(template.replace("{{HEAD_EXTRA}}", head_extra))


def load_json(name: str) -> dict:
    p = ROOT / "data" / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def build(out_dir: Path, limit: int, offline: bool) -> Path:
    blogs = json.loads((ROOT / "data" / "blogs.json").read_text(encoding="utf-8"))
    banner = load_json("banner.json")
    site = load_json("site.json")
    head_extra = render_head_extra(site)
    template = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
    privacy_tpl = (ROOT / "privacy" / "index.html").read_text(encoding="utf-8")

    feeds: dict[str, list[dict]] = {}
    for b in blogs:
        if b.get("status") == "live" and b.get("feed"):
            feeds[b["id"]] = load_feed(b["feed"], limit, offline)

    year = dt.datetime.now(dt.timezone(dt.timedelta(hours=9))).year
    page = render_index(template, blogs, feeds, banner, year, head_extra)

    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    (out_dir / "index.html").write_text(page, encoding="utf-8")
    # privacy 는 head 슬롯 주입 후 렌더 (STATIC 복사 아님)
    (out_dir / "privacy").mkdir(parents=True, exist_ok=True)
    (out_dir / "privacy" / "index.html").write_text(render_privacy(privacy_tpl, head_extra), encoding="utf-8")
    for name in STATIC:
        src = ROOT / name
        if not src.exists():
            continue
        if src.is_dir():
            shutil.copytree(src, out_dir / name)
        else:
            shutil.copy2(src, out_dir / name)
    # ads.txt 는 adsense_client 가 있을 때만 (없으면 파일 자체를 만들지 않는다 → 404, #3)
    ads = ads_txt(site)
    if ads:
        (out_dir / "ads.txt").write_text(ads, encoding="utf-8")
    log(f"[build] dist → {out_dir} (블로그 {len([b for b in blogs if b.get('status') == 'live'])}개, "
        f"최신 글 {sum(len(v) for v in feeds.values())}건, "
        f"head슬롯 {'있음' if head_extra else '없음'}, ads.txt {'생성' if ads else '없음'})")
    return out_dir


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "dist"))
    ap.add_argument("--limit", type=int, default=5, help="블로그당 최신 글 수 (허브 #9: 5)")
    ap.add_argument("--offline", action="store_true", help="피드 조회 없이 빌드")
    a = ap.parse_args()
    build(Path(a.out), a.limit, a.offline)
    return 0


if __name__ == "__main__":
    sys.exit(main())
