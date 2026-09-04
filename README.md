# beolsseo.com — Haze의 블로그 허브

`beolsseo.com` 루트 허브 페이지. 개인 개발자가 운영하는 주제별 블로그(dev.beolsseo.com 등)의 입구.

## 구조

- `data/blogs.json` — 블로그 카드·피드 목록. **블로그 추가 = 객체 한 줄 추가.**
  `status: "live"` 인 항목만 카드로 노출한다. 그 외 상태는 카드도 만들지 않는다(빈 링크·"준비 중" 카드 금지 — 애드센스 심사 감점).
- `data/banner.json` — 자기 제품 홍보 배너 슬롯(최대 1개). `enabled: false` 면 렌더링하지 않는다.
- `templates/index.html` — 허브 페이지 템플릿. `scripts/build.py` 가 채운다.
- `scripts/build.py` — **빌드 타임**에 각 live 블로그의 피드(Atom/RSS)를 읽어 최신 글을 정적 HTML 로 렌더링 → `dist/`.
  피드 조회 실패 시 빌드를 깨뜨리지 않고 해당 블로그의 글 목록만 비운다(카드 링크는 유지).
- `scripts/check_forbidden.py` — 빌드 결과에 회사 정보(상호·사업자등록번호·회사 사이트 링크)가 남아 있으면 빌드를 실패시킨다.
  문의 이메일 `blog@alreadymorning.com` 만 예외.
- `privacy/` — 개인정보처리방침(운영자 표기 + 연락 이메일만).

## 배포

GitHub Actions(`.github/workflows/pages.yml`)가 `dist/` 를 GitHub Pages 에 배포한다.
`main` push · 매일 1회(KST 07:17) · 수동 실행(`workflow_dispatch`) · `repository_dispatch: hub-rebuild` 로 다시 빌드한다.

## 로컬

```
python3 scripts/build.py            # dist/ 생성 (피드 실제 조회)
python3 scripts/build.py --offline  # 피드 조회 없이 빌드
python3 scripts/check_forbidden.py dist
python3 -m unittest discover -s scripts -p 'test_*.py' -v
```
