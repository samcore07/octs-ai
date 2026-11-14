/**
 * Octs AI - Common Sub-Page Utilities
 */

document.addEventListener("DOMContentLoaded", () => {
  initCommonState();
  initSidebarToggle();
  initThemeToggle();
});

function initThemeToggle() {
  const toggleBtn = document.getElementById("themeToggleBtn");
  
  // Sync state from documentElement (already set by anti-FOUC head script)
  const currentTheme = document.documentElement.getAttribute("data-theme") === "dark" ? "dark" : "light";
  updateThemeButton(currentTheme);

  if (toggleBtn) {
    toggleBtn.addEventListener("click", () => {
      const isDark = document.documentElement.getAttribute("data-theme") === "dark";
      const nextTheme = isDark ? "light" : "dark";
      applyTheme(nextTheme);
    });
  }

  // Cross-tab theme synchronization
  window.addEventListener("storage", (e) => {
    if (e.key === "octs_ai_theme") {
      const newTheme = e.newValue || "light";
      applyTheme(newTheme, false);
    }
  });
}

function applyTheme(theme, save = true) {
  if (theme === "dark") {
    document.documentElement.setAttribute("data-theme", "dark");
  } else {
    document.documentElement.removeAttribute("data-theme");
  }
  if (save) {
    localStorage.setItem("octs_ai_theme", theme);
  }
  updateThemeButton(theme);

  // If on settings page, keep select in sync
  const themeSelect = document.getElementById("settingsThemeSelect");
  if (themeSelect && themeSelect.value !== theme) {
    themeSelect.value = theme;
  }
}

function updateThemeButton(theme) {
  const toggleBtn = document.getElementById("themeToggleBtn");
  if (!toggleBtn) return;
  toggleBtn.setAttribute("title", theme === "dark" ? "Switch to Light Mode" : "Switch to Dark Mode");
  toggleBtn.setAttribute("aria-label", theme === "dark" ? "Switch to Light Mode" : "Switch to Dark Mode");
}

function initCommonState() {
  const username = localStorage.getItem("octs_ai_username") || localStorage.getItem("generative_clash_username") || "Alex";
  const roleKey = localStorage.getItem("octs_ai_role") || localStorage.getItem("generative_clash_role") || null;

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
      if (window.innerWidth <= 768) {
        sidebar.classList.toggle("mobile-open");
      } else {
        sidebar.classList.toggle("collapsed");
      }
    });

    // Close mobile sidebar when clicking main content or pressing Escape
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && sidebar.classList.contains("mobile-open")) {
        sidebar.classList.remove("mobile-open");
      }
    });

    const main = document.querySelector(".main-viewport");
    if (main) {
      main.addEventListener("click", () => {
        if (sidebar.classList.contains("mobile-open")) {
          sidebar.classList.remove("mobile-open");
        }
      });
    }
  }
}

window.applyTheme = applyTheme;
window.initCommonState = initCommonState;
