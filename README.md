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
- `assets/css/style.css` — 디자인은 **blog-dev #15 디자인 시스템과 동기화**한다(허브 #6). 파일 맨 위 `[동기화 블록]`(`:root` 변수·다크 팔레트·폰트 폴백 보정)은
  blog-dev `assets/css/main.css` 의 같은 블록과 **동일하게 유지**하고, 블로그 쪽이 바뀌면 그대로 복사해 온다. 허브 고유 규칙은 그 아래에만 쓴다.
  웹폰트는 Pretendard Variable 1종(`templates/index.html`·`privacy/index.html` 의 `<link>`), 외부 CSS/JS 프레임워크 없음.
- `scripts/favicon.py` — `data/site.json` `favicon`(bg/fg/glyph) 값으로 `favicon.ico`·`assets/favicon.svg`·`assets/apple-touch-icon.png` 생성(blog-dev 와 같은 도형 규칙, 허브 글리프 `H`).
  변경 시 `python3 scripts/favicon.py --force` 로 재생성해 커밋한다(빌드는 파일을 복사만 함).

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
