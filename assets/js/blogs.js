// 블로그 목록 데이터 — 새 블로그가 생기면 아래 배열에 "한 줄"만 추가하면 카드가 늘어난다.
//   status: "live" = 링크 활성(클릭 이동) / "soon" = 준비 중 배지만(링크 없음 — 깨진 링크 금지)
// ⚠️ 개인정보(주소·생년월일 등)는 절대 넣지 않는다.
const BLOGS = [
  {
    title: "개발 블로그",
    desc: "개발 기록과 기술 노트를 남기는 공간.",
    url: "https://dev.beolsseo.com",
    emoji: "💻",
    status: "live",
  },
  {
    title: "생활정보 블로그",
    desc: "일상에 쓸모 있는 생활 정보.",
    url: "",
    emoji: "🏠",
    status: "soon",
  },
];

// 카드 렌더 — 데이터 배열만 보고 그린다. HTML 은 손대지 않는다.
function renderBlogs(mountId) {
  const mount = document.getElementById(mountId);
  if (!mount) return;
  mount.innerHTML = BLOGS.map((b) => {
    const safe = (s) =>
      String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
      }[c]));
    const inner = `
      <span class="card-emoji" aria-hidden="true">${safe(b.emoji)}</span>
      <span class="card-body">
        <span class="card-title">${safe(b.title)}${
      b.status === "soon" ? '<span class="badge">준비 중</span>' : ""
    }</span>
        <span class="card-desc">${safe(b.desc)}</span>
      </span>`;
    // live 만 링크(a). soon 은 링크 없는 div — 깨진 링크를 만들지 않는다.
    if (b.status === "live" && b.url) {
      return `<a class="card" href="${safe(b.url)}" rel="noopener">${inner}</a>`;
    }
    return `<div class="card card--soon" aria-disabled="true">${inner}</div>`;
  }).join("");
}

document.addEventListener("DOMContentLoaded", () => renderBlogs("blog-list"));
