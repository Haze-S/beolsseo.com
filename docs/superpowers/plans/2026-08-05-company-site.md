# 벌써아침 회사 사이트 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 벌써아침 회사 랜딩 + 프로젝트 소개 2페이지 + 기존 법적 문서 정비를 GitHub Pages(beolsseo.com)로 배포.

**Architecture:** 빌드 없는 순수 정적 HTML 5페이지가 `assets/style.css` 하나를 공유. 모든 페이지가 동일한 헤더/푸터 마크업을 복붙로 포함(템플릿 엔진 없음 — 페이지 5개 규모에서 YAGNI).

**Tech Stack:** HTML5, CSS3(공용 1파일), GitHub Pages, 가비아 DNS.

## Global Constraints

- 문의 이메일 표기: `contact@beolsseo.com`
- 프로젝트 상태 표기: 두 프로젝트 모두 "개발 중" 배지 — 출시 표기 금지
- 약관·개인정보처리방침 본문 법적 내용 수정 금지(이메일 기입, 헤더/푸터 추가만)
- 톤: 크림 배경 `#fdfcfa`, 잉크 `#2b2b33`, 딥퍼플 `#1a1226`(기존 약관 페이지 계승), 아침 그라데이션 히어로(라벤더→살구→오렌지)
- 반응형: 모바일 단일 컬럼, `max-width` 컨테이너 960px
- 외부 CDN·JS 없음(정적 순수 HTML/CSS)

---

### Task 1: 에셋 준비 + 공용 스타일

**Files:**
- Create: `assets/style.css`
- Create: `assets/img/` — dungeon-overtime/docs에서 `gameplay.png, title.png, levelup.png, orbit.png, shop.png, bossrush.png` 복사, idle-rpg/public/chars에서 `maou_desk.webp, maou_cheer.webp` 복사

**Interfaces:**
- Produces: CSS 클래스 — `.site-header`, `.site-nav`, `.hero`, `.badge`, `.card-grid`, `.card`, `.section`, `.shots`(스크린샷 그리드), `.site-footer`. 모든 페이지가 이 클래스만 사용.

- [ ] Step 1: 이미지 복사 (`cp` 8개 파일)
- [ ] Step 2: `assets/style.css` 작성 — CSS 변수(`--bg:#fdfcfa; --ink:#2b2b33; --deep:#1a1226; --sun:#e8833a; --dawn1:#c9b8e8; --dawn2:#ffd9a0; --dawn3:#ffb17a`), 헤더/푸터/히어로/카드/배지/스크린샷 그리드/반응형(@media 720px)
- [ ] Step 3: Commit

### Task 2: index.html (랜딩)

**Files:** Create: `index.html`

**Interfaces:**
- Consumes: Task 1 CSS 클래스, `assets/img/maou_desk.webp`, `title.png`
- Produces: 공용 헤더/푸터 마크업 패턴(다른 페이지가 복제):
  - 헤더 네비: `index.html`(벌써아침 로고) · `dungeon.html`(던전 컴퍼니) · `campaign.html`(campaign-hub)
  - 푸터: © 2026 벌써아침 · contact@beolsseo.com · `terms.html` · `privacy.html`

- [ ] Step 1: 작성 — 섹션: ① 히어로(아침 그라데이션, 카피 "밤새 던전을 지켰더니, 벌써 아침." + 서브카피 + maou_desk 이미지) ② 프로젝트 카드 2개(던전 컴퍼니 시리즈 → dungeon.html / campaign-hub → campaign.html, 각각 "개발 중" 배지) ③ 회사 소개(작은 팀, 게임·웹 플랫폼) ④ 문의(contact@beolsseo.com)
- [ ] Step 2: 로컬 서버로 렌더 확인
- [ ] Step 3: Commit

### Task 3: dungeon.html (던전 컴퍼니 시리즈)

**Files:** Create: `dungeon.html`

**Interfaces:** Consumes: Task 2 헤더/푸터 패턴, 스크린샷 6장, `maou_cheer.webp`

- [ ] Step 1: 작성 — ① 시리즈 소개(마왕성 세계관: 회사=마왕성, 야근·결재 드립) ② 본편 『던전 컴퍼니: 마왕성 키우기』(방치형 마왕성 경영 RPG, 모바일/웹, 개발 중) ③ 스핀오프 『마왕님 야근 사수』(데스크톱 아레나 서바이버, 정시 퇴근 목표, 개발 중) + 스크린샷 그리드 6장
- [ ] Step 2: 렌더 확인
- [ ] Step 3: Commit

### Task 4: campaign.html (campaign-hub)

**Files:** Create: `campaign.html`

**Interfaces:** Consumes: Task 2 헤더/푸터 패턴

- [ ] Step 1: 작성 — ① 개요(사전예약·쿠폰·이벤트를 캠페인 단위로 운영하는 마케팅 플랫폼) ② 기능 3카드(사전예약/쿠폰/이벤트 + 캠페인별 테마) ③ 대표 유스케이스(게임 마케팅 흐름: 사전예약→오픈 쿠폰→출석 이벤트) ④ 상태: 개발 중, 문의 유도
- [ ] Step 2: 렌더 확인
- [ ] Step 3: Commit

### Task 5: 약관 페이지 정비

**Files:** Modify: `privacy.html`(이메일 기입 L69, 헤더/푸터), `terms.html`(이메일 기입 L66, 헤더/푸터)

- [ ] Step 1: `[문의 이메일 기입 — 예: contact@beolsseo.com]` → `contact@beolsseo.com` 치환(양쪽)
- [ ] Step 2: 공용 헤더 추가 + 푸터를 공용 푸터로 교체, `assets/style.css` 링크(기존 인라인 스타일은 본문용으로 유지)
- [ ] Step 3: 렌더 확인 + Commit

### Task 6: 전체 QA + 배포

**Files:** Create: `CNAME`(내용: `beolsseo.com`), `README.md`, `.gitignore`

- [ ] Step 1: 로컬 서버(`python3 -m http.server`)로 5페이지 링크·이미지 404 없는지 curl 검증, browse 스킬로 시각 QA
- [ ] Step 2: CNAME·README 작성, commit
- [ ] Step 3: `git push -u origin main`
- [ ] Step 4: `gh repo edit --visibility public` → `gh api`로 Pages 활성화(main/root)
- [ ] Step 5: `https://haze-s.github.io/beolsseo.com/` 접근 확인
- [ ] Step 6: 사용자 안내 — 가비아 DNS(A 레코드 4개 185.199.108~111.153, www CNAME haze-s.github.io) + 이메일 포워딩
