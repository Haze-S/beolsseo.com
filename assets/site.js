// 스크롤 리빌 — 모션 축소 설정 시 비활성
//
// 주의: .reveal 은 opacity:0 으로 시작한다. 즉 이 스크립트가 클래스를 붙인 뒤
// IntersectionObserver 가 어떤 이유로든 해제하지 못하면 **본문이 보이지 않는다**.
// 크롤러·심사 도구처럼 JS는 실행하지만 스크롤하지 않는 환경이 실제로 있어서,
// 아래 안전장치로 일정 시간 후 무조건 해제한다(콘텐츠 가시성 > 애니메이션).
// 심사 대상 페이지(dungeon.html)는 이 스크립트를 아예 넣지 않는다.
(function () {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  var els = document.querySelectorAll('.card, .section-head, .feature-text, .feature-art, .shots figure, .contact-band .container');
  if (!('IntersectionObserver' in window) || !els.length) return;
  els.forEach(function (e) { e.classList.add('reveal'); });

  function revealAll() {
    els.forEach(function (e) { e.classList.add('in'); });
  }

  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (en) {
      if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); }
    });
  }, { threshold: 0.12 });
  els.forEach(function (e) { io.observe(e); });

  // 안전장치: 1.5초 뒤 남은 요소를 전부 보이게 한다.
  setTimeout(revealAll, 1500);
  // 탭이 백그라운드로 렌더되는 경우(스크롤 이벤트 없음)도 대비
  if (document.visibilityState !== 'visible') revealAll();
})();
