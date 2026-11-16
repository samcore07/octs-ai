/**
 * Octs AI - Memory Hub Controller
 * Connects frontend UI to Phase 6 /api/memory and /api/memory/projects endpoints.
 */

let allMemories = [];
let allProjects = [];
let activeDisciplineFilter = "all";
let activeTypeFilter = "all";

document.addEventListener("DOMContentLoaded", () => {
  initThemeToggle();
  initSidebar();
  loadData();
  bindFilterEvents();
});

function initThemeToggle() {
  const btn = document.getElementById("themeToggleBtn");
  if (!btn) return;
  btn.addEventListener("click", () => {
    const isDark = document.documentElement.getAttribute("data-theme") === "dark";
    if (isDark) {
      document.documentElement.removeAttribute("data-theme");
      localStorage.setItem("octs_ai_theme", "light");
    } else {
      document.documentElement.setAttribute("data-theme", "dark");
      localStorage.setItem("octs_ai_theme", "dark");
    }
  });
}

function initSidebar() {
  const toggleBtn = document.getElementById("sidebarToggleBtn");
  const sidebar = document.querySelector(".sidebar");
  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener("click", () => {
      sidebar.classList.toggle("collapsed");
    });
  }
}

async function loadData() {
  try {
    const [memRes, projRes, sbRes] = await Promise.all([
      fetch("/api/memory?limit=100"),
      fetch("/api/memory/projects"),
      fetch("/api/supabase/status").catch(() => null),
    ]);

    if (memRes.ok) {
      allMemories = await memRes.json();
    }
    if (projRes.ok) {
      allProjects = await projRes.json();
    }

    if (sbRes && sbRes.ok) {
      const sbData = await sbRes.json();
      const badge = document.getElementById("memoryDatabaseBadge");
      if (badge) {
        if (sbData.configured) {
          badge.textContent = "Database: Supabase Cloud (Active)";
          badge.style.background = "rgba(16, 185, 129, 0.15)";
          badge.style.color = "#10B981";
          badge.style.borderColor = "rgba(16, 185, 129, 0.3)";
        } else {
          badge.textContent = "Database: Local SQLite (Active)";
          badge.style.background = "rgba(107, 114, 128, 0.15)";
          badge.style.color = "var(--text-secondary)";
          badge.style.borderColor = "var(--border)";
        }
      }
    }

    updateStats();
    renderMemories();
    renderProjects();
  } catch (err) {
    console.error("Failed to load memory data:", err);
  }
}

function updateStats() {
  const totalEl = document.getElementById("statTotalMemories");
  const projEl = document.getElementById("statActiveProjects");
  const constEl = document.getElementById("statConstraints");
  const prefEl = document.getElementById("statPreferences");

  if (totalEl) totalEl.textContent = allMemories.length;
  if (projEl) projEl.textContent = allProjects.filter(p => p.is_active).length;
  if (constEl) constEl.textContent = allMemories.filter(m => m.memory_type === "constraint").length;
  if (prefEl) prefEl.textContent = allMemories.filter(m => m.memory_type === "user_preference").length;
}

function bindFilterEvents() {
  const disciplinePills = document.querySelectorAll("[data-disc-filter]");
  disciplinePills.forEach(pill => {
    pill.addEventListener("click", () => {
      disciplinePills.forEach(p => p.classList.remove("active"));
      pill.classList.add("active");
      activeDisciplineFilter = pill.getAttribute("data-disc-filter");
      renderMemories();
    });
  });

  const searchInput = document.getElementById("memorySearchInput");
  if (searchInput) {
    searchInput.addEventListener("input", () => {
      renderMemories();
    });
  }
}

function renderMemories() {
  const container = document.getElementById("memoriesList");
  if (!container) return;

  const searchInput = document.getElementById("memorySearchInput");
  const query = searchInput ? searchInput.value.toLowerCase().trim() : "";

  const filtered = allMemories.filter(m => {
    if (activeDisciplineFilter !== "all") {
      if (m.discipline !== activeDisciplineFilter) return false;
    }
    if (query) {
      if (!m.content.toLowerCase().includes(query)) return false;
    }
    return true;
  });

  if (filtered.length === 0) {
    container.innerHTML = `
      <div style="background: var(--surface); border: 1px dashed var(--border); border-radius: var(--radius); padding: 36px; text-align: center; color: var(--text-muted); font-size: 13px;">
        No memory records found for the selected filter. Execute creative directives in the dashboard to build persistent craft memory.
      </div>
    `;
    return;
  }

  container.innerHTML = filtered.map(m => {
    const typeClass = `badge-${m.memory_type.replace('_', '-')}`;
    const discLabel = m.discipline ? m.discipline.toUpperCase() : "GENERAL";
    const dateStr = new Date(m.created_at).toLocaleDateString();

    return `
      <div class="memory-item-card" id="mem-card-${m.memory_id}">
        <div class="memory-card-topbar">
          <div class="memory-badge-row">
            <span class="badge-pill ${typeClass}">${m.memory_type.replace('_', ' ')}</span>
            <span class="badge-pill" style="background: var(--surface-alt); color: var(--text-secondary);">${m.scope}</span>
            <span class="badge-pill" style="background: var(--surface-alt); color: var(--accent);">${discLabel}</span>
            ${m.version > 1 ? `<span class="badge-pill" style="background: var(--warning-subtle); color: var(--warning);">v${m.version}</span>` : ''}
          </div>
          <button class="memory-action-btn" onclick="deleteMemory('${m.memory_id}')" title="Delete memory record">Delete</button>
        </div>
        <div class="memory-content-text">${escapeHtml(m.content)}</div>
        <div class="memory-meta-footer">
          <span>Confidence: ${(m.confidence * 100).toFixed(0)}% • Importance: ${(m.importance * 100).toFixed(0)}%</span>
          <span>Accessed: ${m.access_count}x • Recorded: ${dateStr}</span>
        </div>
      </div>
    `;
  }).join("");
}

function renderProjects() {
  const container = document.getElementById("projectsList");
  if (!container) return;

  if (allProjects.length === 0) {
    container.innerHTML = `
      <div style="padding: 20px; text-align: center; color: var(--text-muted); font-size: 13px;">
        No active projects established yet.
      </div>
    `;
    return;
  }

  container.innerHTML = allProjects.filter(p => p.is_active).map(p => `
    <div class="project-item-row" id="proj-row-${p.project_id}">
      <div>
        <div style="font-weight: 600; font-size: 14px; color: var(--text);">${escapeHtml(p.name)}</div>
        <div style="font-size: 12px; color: var(--text-secondary); margin-top: 2px;">
          ${escapeHtml(p.description || "No description")} • <span style="color: var(--accent);">${p.discipline || 'general'}</span>
        </div>
      </div>
      <div>
        <button class="memory-action-btn" onclick="deleteProject('${p.project_id}')" title="Deactivate project">Delete</button>
      </div>
    </div>
  `).join("");
}

async function deleteMemory(memoryId) {
  if (!confirm("Are you sure you want to remove this persistent memory?")) return;
  try {
    const res = await fetch(`/api/memory/${memoryId}`, { method: "DELETE" });
    if (res.ok) {
      allMemories = allMemories.filter(m => m.memory_id !== memoryId);
      updateStats();
      renderMemories();
    }
  } catch (err) {
    console.error("Failed to delete memory:", err);
  }
}

async function deleteProject(projectId) {
  if (!confirm("Are you sure you want to delete this project? Project-scoped memories will be archived.")) return;
  try {
    const res = await fetch(`/api/memory/projects/${projectId}`, { method: "DELETE" });
    if (res.ok) {
      allProjects = allProjects.filter(p => p.project_id !== projectId);
      updateStats();
      renderProjects();
    }
  } catch (err) {
    console.error("Failed to delete project:", err);
  }
}

async function createProjectPrompt() {
  const name = prompt("Enter project name:");
  if (!name || !name.trim()) return;
  const description = prompt("Enter project description (optional):") || "";
  const discipline = prompt("Enter discipline (writers, musicians, creators, designers):") || null;

  try {
    const res = await fetch("/api/memory/projects", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: name.trim(), description: description.trim(), primary_discipline: discipline }),
    });
    if (res.ok) {
      const created = await res.json();
      allProjects.unshift(created);
      updateStats();
      renderProjects();
    }
  } catch (err) {
    console.error("Failed to create project:", err);
  }
}

function escapeHtml(str) {
  if (!str) return "";
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

window.deleteMemory = deleteMemory;
window.deleteProject = deleteProject;
window.createProjectPrompt = createProjectPrompt;
