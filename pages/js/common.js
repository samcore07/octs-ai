/**
 * Generative Clash - Common Sub-Page Utilities
 */

document.addEventListener("DOMContentLoaded", () => {
  initCommonState();
  initSidebarToggle();
});

function initCommonState() {
  const username = localStorage.getItem("generative_clash_username") || "Alex";
  const roleKey = localStorage.getItem("generative_clash_role") || null;

  const roleTitles = {
    writers: "Writers & Storytellers",
    musicians: "Musicians & Singers",
    creators: "Content Creators",
    designers: "Visual Artists & Designers"
  };

  // Sync avatar and name
  const topName = document.getElementById("topName");
  const avatar = document.getElementById("sidebarAvatar");
  if (topName) topName.textContent = username;
  if (avatar) avatar.textContent = username.charAt(0).toUpperCase() || "A";

  // Sync role badge
  const sidebarRoleBadge = document.getElementById("sidebarRoleIndicator");
  const sidebarRoleText = document.getElementById("sidebarRoleText");
  const topbarRoleBtn = document.getElementById("topbarRoleBtn");
  const topbarRoleName = document.getElementById("topbarRoleName");

  if (roleKey && roleTitles[roleKey]) {
    const title = roleTitles[roleKey];
    if (sidebarRoleBadge) sidebarRoleBadge.style.display = "flex";
    if (sidebarRoleText) sidebarRoleText.textContent = title;
    if (topbarRoleBtn) topbarRoleBtn.style.display = "inline-flex";
    if (topbarRoleName) topbarRoleName.textContent = title;
  }
}

function initSidebarToggle() {
  const toggleBtn = document.getElementById("sidebarToggleBtn");
  const sidebar = document.querySelector(".sidebar");
  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener("click", () => {
      sidebar.classList.toggle("collapsed");
    });
  }
}
