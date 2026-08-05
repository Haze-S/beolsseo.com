# 벌써아침 회사 사이트 설계

날짜: 2026-08-05 · 상태: 승인됨

## 목적

벌써아침(beolsseo.com)의 공식 회사 사이트. 회사 브랜드를 소개하고, 두 프로젝트 축(던전 컴퍼니 시리즈, campaign-hub)을 알리고, 기존 법적 문서(이용약관·개인정보처리방침)를 호스팅한다.

## 결정 사항

- **도메인 전략**: beolsseo.com 하나로 서브도메인 확장 (`dg.beolsseo.com` 등). 플랫폼 전용 도메인은 공개 출시 직전에 결정.
- **호스팅**: GitHub Pages (`Haze-S/beolsseo.com`, main 브랜치 루트) + `CNAME` 파일. 레포는 public 전환 필요(무료 Pages 조건).
- **기술**: 순수 정적 HTML + 공용 CSS(`assets/style.css`). 빌드 없음.
- **문의 이메일**: `contact@beolsseo.com` — 가비아 도메인에 포워딩 설정(배포 후 사용자가 DNS 작업 시 함께).
- **프로젝트 구성**: "던전 컴퍼니 시리즈"(마왕성 키우기 본편 + 마왕님 야근 사수 스핀오프)를 하나의 게임 IP로 통합 소개 + campaign-hub 플랫폼 별도.

## 페이지 구성 (5페이지)

```
index.html      랜딩 — 히어로(브랜드 서사) + 프로젝트 2개 카드 + 회사 소개 + 문의
dungeon.html    던전 컴퍼니 시리즈 — 본편(마왕성 키우기) + 스핀오프(마왕님 야근 사수) 소개, 실제 스크린샷
campaign.html   campaign-hub — 사전예약·쿠폰·이벤트 캠페인 플랫폼 소개
privacy.html    (기존) 문의 이메일 기입 + 공용 헤더/푸터 적용
terms.html      (기존) 동일
assets/         style.css + 게임 스크린샷(dungeon-overtime/docs 선별) + 마왕 아트(idle-rpg public/chars, 사용 허락됨)
```

## 디자인

- **톤**: 아침 햇살. 크림 배경(`#fdfcfa`, 기존 약관 페이지 계승) + 새벽→아침 그라데이션(살구·오렌지·연보라) 히어로.
- **서사**: "밤새 던전(야근)을 지키다 맞는 아침" — 회사명과 게임 세계관(마왕님 야근)을 잇는 카피.
- **공용 헤더**: 로고(벌써아침) + 네비(게임/플랫폼/약관). **공용 푸터**: © 벌써아침 · contact@beolsseo.com · 약관·개인정보 링크.
- 모바일 반응형(단일 컬럼 스택). 폰트: 시스템 한글 스택(Apple SD Gothic Neo / Noto Sans KR).

## 콘텐츠 원칙

- 두 프로젝트 모두 미출시 → "개발 중 / 출시 예정" 배지. 거짓 출시 표기 금지.
- 약관·개인정보처리방침 본문은 수정하지 않음(법적 문서). 이메일 플레이스홀더 기입과 헤더/푸터 통일만. 시행일 플레이스홀더는 유지.

## 배포 절차

1. git 레포 초기화 → GitHub push (`Haze-S/beolsseo.com`)
2. 레포 public 전환 → GitHub Pages 활성화(main, root) → `CNAME` = beolsseo.com
3. 사용자 DNS 작업(가비아): A 레코드 4개(GitHub Pages IP) + www CNAME + 이메일 포워딩

## 범위 밖 (YAGNI)

- 블로그/뉴스, 다국어(영문), 폼 제출 백엔드, 분석 스크립트, 게임 다운로드 배포.
