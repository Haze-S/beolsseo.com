# alreadymorning.com

벌써아침 게임 포털. 순수 정적 HTML — 빌드 없음, GitHub Pages(main 브랜치 루트) 배포.

- `index.html` 게임 포털 · `dungeon.html` 던전 컴퍼니 시리즈
- `terms.html` 이용약관 · `privacy.html` 개인정보처리방침 · `404.html`
- 로컬 확인: `python3 -m http.server` 후 접속

## 도메인

`CNAME` 파일이 GitHub Pages 커스텀 도메인을 결정한다. 현재 `alreadymorning.com`.

- 2026-08-11에 `beolsseo.com` → `alreadymorning.com`으로 전환했다(던전 컴퍼니 #79).
  구 도메인은 외부에 노출된 URL이 없어 301 리다이렉트 없이 갈아탔다.
- DNS는 Cloudflare. apex는 GitHub Pages A 레코드 4개, `www`는 `haze-s.github.io` CNAME.
- 문의 메일 `contact@alreadymorning.com`은 Cloudflare Email Routing 포워딩이다.

> 레포 이름은 `beolsseo.com`으로 남아 있다(이름만이고 서비스 주소와 무관).
