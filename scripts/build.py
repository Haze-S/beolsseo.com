#!/usr/bin/env python3
"""beolsseo.com 허브 빌드 (이슈 #1)

- data/blogs.json 의 status=live 블로그만 카드로 렌더링한다 (그 외 상태는 카드 자체를 만들지 않음).
- 각 live 블로그의 feed(Atom/RSS)를 **빌드 타임**에 읽어 최신 글 목록을 정적 HTML 로 넣는다.
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
STATIC = ["assets", "privacy", "robots.txt", "sitemap.xml", "CNAME", ".nojekyll"]
ATOM = "{http://www.w3.org/2005/Atom}"
SUMMARY_MAX = 110


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


# ---------- 렌더 ----------

def render_card(b: dict) -> str:
    return (
        f'            <a class="card" href="{esc(b["url"])}" rel="noopener">\n'
        f'              <span class="card-emoji" aria-hidden="true">{esc(b.get("emoji", ""))}</span>\n'
        f'              <span class="card-body">\n'
        f'                <span class="card-title">{esc(b["title"])}</span>\n'
        f'                <span class="card-desc">{esc(b.get("desc", ""))}</span>\n'
        f'              </span>\n'
        f'            </a>'
    )


def render_recent(blog: dict, posts: list[dict]) -> str:
    if not posts:
        return ""
    lis = []
    for p in posts:
        d = p["date"].isoformat() if p["date"] else ""
        date_html = f'<time datetime="{d}">{d}</time>' if d else ""
        summ = shorten(p["summary"]) if p["summary"] else ""
        summ_html = f'\n              <p class="post-desc">{esc(summ)}</p>' if summ else ""
        lis.append(
            f'            <li>\n'
            f'              <a class="post-link" href="{esc(p["url"])}" rel="noopener">{esc(p["title"])}</a>\n'
            f'              <p class="post-meta">{date_html}</p>{summ_html}\n'
            f'            </li>'
        )
    return (
        f'      <section class="section recent">\n'
        f'        <div class="wrap">\n'
        f'          <h2>{esc(blog["title"])} 최신 글</h2>\n'
        f'          <ul class="post-list">\n' + "\n".join(lis) + "\n"
        f'          </ul>\n'
        f'          <p class="more"><a href="{esc(blog["url"])}" rel="noopener">{esc(blog["title"])} 전체 글 보기 →</a></p>\n'
        f'        </div>\n'
        f'      </section>'
    )


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


def render_index(template: str, blogs: list[dict], feeds: dict[str, list[dict]], banner: dict, year: int) -> str:
    live = [b for b in blogs if b.get("status") == "live" and b.get("url")]
    cards = "\n".join(render_card(b) for b in live)
    recent = "\n".join(s for s in (render_recent(b, feeds.get(b["id"], [])) for b in live) if s)
    out = template
    out = out.replace("{{CARDS}}", cards)
    out = out.replace("{{RECENT}}", recent)
    out = out.replace("{{BANNER}}", render_banner(banner))
    out = out.replace("{{YEAR}}", str(year))
    # 빈 플레이스홀더 줄 정리
    return re.sub(r"\n[ \t]*\n(?=[ \t]*\n)", "\n", out)


def build(out_dir: Path, limit: int, offline: bool) -> Path:
    blogs = json.loads((ROOT / "data" / "blogs.json").read_text(encoding="utf-8"))
    banner_path = ROOT / "data" / "banner.json"
    banner = json.loads(banner_path.read_text(encoding="utf-8")) if banner_path.exists() else {}
    template = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")

    feeds: dict[str, list[dict]] = {}
    for b in blogs:
        if b.get("status") == "live" and b.get("feed"):
            feeds[b["id"]] = load_feed(b["feed"], limit, offline)

    year = dt.datetime.now(dt.timezone(dt.timedelta(hours=9))).year
    page = render_index(template, blogs, feeds, banner, year)

    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    (out_dir / "index.html").write_text(page, encoding="utf-8")
    for name in STATIC:
        src = ROOT / name
        if not src.exists():
            continue
        if src.is_dir():
            shutil.copytree(src, out_dir / name)
        else:
            shutil.copy2(src, out_dir / name)
    log(f"[build] dist → {out_dir} (블로그 {len([b for b in blogs if b.get('status') == 'live'])}개, "
        f"최신 글 {sum(len(v) for v in feeds.values())}건)")
    return out_dir


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "dist"))
    ap.add_argument("--limit", type=int, default=8, help="블로그당 최신 글 수 (5~10 권장)")
    ap.add_argument("--offline", action="store_true", help="피드 조회 없이 빌드")
    a = ap.parse_args()
    build(Path(a.out), a.limit, a.offline)
    return 0


if __name__ == "__main__":
    sys.exit(main())
