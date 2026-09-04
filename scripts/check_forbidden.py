#!/usr/bin/env python3
"""빌드 결과(또는 소스 트리)에서 회사 정보 잔존 여부를 검사한다 (이슈 #1, 대표 지시 2026-09-03).

금지 문자열: 상호 "벌써아침", 사업자등록번호 "818-10-02994", 회사 사이트 "alreadymorning.com"
예외: 문의 이메일 blog@alreadymorning.com (mailto 포함)

검사 대상: .html .xml .txt .json .js .css .md 파일 전부. 발견 시 파일:줄 을 출력하고 exit 1.
사용: python3 scripts/check_forbidden.py dist
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

FORBIDDEN = ["벌써아침", "818-10-02994", "alreadymorning.com"]
ALLOWED_EMAIL = "blog@alreadymorning.com"
EXTS = {".html", ".xml", ".txt", ".json", ".js", ".css", ".md"}


def scan_text(text: str) -> list[tuple[int, str, str]]:
    """(줄번호, 금지어, 줄) 목록. 이메일 예외는 먼저 제거하고 검사한다."""
    hits = []
    for n, line in enumerate(text.splitlines(), 1):
        probe = line.replace(ALLOWED_EMAIL, "")
        for word in FORBIDDEN:
            if word in probe:
                hits.append((n, word, line.strip()))
    return hits


def scan_dir(root: Path) -> tuple[int, list[str]]:
    files = sorted(p for p in root.rglob("*") if p.is_file() and p.suffix in EXTS)
    out = []
    for p in files:
        for n, word, line in scan_text(p.read_text(encoding="utf-8", errors="replace")):
            out.append(f"{p.relative_to(root)}:{n}: [{word}] {line[:120]}")
    return len(files), out


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "dist")
    n_files, hits = scan_dir(root)
    print(f"검사 파일 {n_files}개 (대상: {root})")
    print(f"금지 문자열: {', '.join(FORBIDDEN)}  / 예외: {ALLOWED_EMAIL}")
    if hits:
        print(f"❌ 잔존 {len(hits)}건:")
        print("\n".join(hits))
        return 1
    print("✅ 잔존 0건")
    return 0


if __name__ == "__main__":
    sys.exit(main())
