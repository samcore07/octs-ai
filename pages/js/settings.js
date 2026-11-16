/**
 * Octs AI - Settings Controller
 */

document.addEventListener("DOMContentLoaded", () => {
  loadCurrentSettings();
  checkSupabaseStatus();
});

async function checkSupabaseStatus() {
  const badge = document.getElementById("supabaseStatusBadge");
  if (!badge) return;

  try {
    const res = await fetch("/api/supabase/status");
    if (res.ok) {
      const data = await res.json();
      if (data.configured) {
        badge.textContent = "Supabase Cloud";
        badge.style.background = "rgba(16, 185, 129, 0.15)";
        badge.style.color = "#10B981";
        badge.style.borderColor = "rgba(16, 185, 129, 0.3)";
      } else {
        badge.textContent = "Local SQLite (Default)";
        badge.style.background = "rgba(107, 114, 128, 0.15)";
        badge.style.color = "var(--text-secondary)";
        badge.style.borderColor = "var(--border)";
      }
    }
  } catch (e) {
    badge.textContent = "Offline";
  }
}

async function testSupabaseConnection() {
  const btn = document.getElementById("testSupabaseBtn");
  const resultEl = document.getElementById("supabasePingResult");
  const detailsBox = document.getElementById("supabaseDetailsBox");

  if (btn) btn.disabled = true;
  if (resultEl) resultEl.textContent = "Testing database connection...";

  try {
    const res = await fetch("/api/supabase/test", { method: "POST" });
    const data = await res.json();

    if (data.status === "connected") {
      resultEl.textContent = `✓ Connected to Supabase Cloud (${data.latency_ms}ms)`;
      resultEl.style.color = "var(--success)";
    } else if (data.status === "not_configured") {
      resultEl.textContent = "○ Local SQLite active (SUPABASE_URL and SUPABASE_KEY not in .env)";
      resultEl.style.color = "var(--text-secondary)";
    } else {
      resultEl.textContent = `⚠ ${data.message || data.status}`;
      resultEl.style.color = "var(--warning)";
    }

    if (detailsBox) {
      detailsBox.style.display = "block";
      detailsBox.innerHTML = `
        <div><strong>Status:</strong> ${data.status}</div>
        <div><strong>Storage Mode:</strong> ${data.mode}</div>
        ${data.url ? `<div><strong>Supabase Host:</strong> ${data.url}</div>` : ""}
        ${data.latency_ms !== null && data.latency_ms !== undefined ? `<div><strong>Latency:</strong> ${data.latency_ms}ms</div>` : ""}
        ${data.tables && Object.keys(data.tables).length ? `<div><strong>Tables Verified:</strong> ${JSON.stringify(data.tables)}</div>` : ""}
      `;
    }
  } catch (err) {
    if (resultEl) {
      resultEl.textContent = `✗ Test error: ${err.message}`;
      resultEl.style.color = "var(--danger)";
    }
  } finally {
    if (btn) btn.disabled = false;
  }
}

function loadCurrentSettings() {
  const usernameInput = document.getElementById("settingsUsername");
  const roleSelect = document.getElementById("settingsRoleSelect");
  const themeSelect = document.getElementById("settingsThemeSelect");

  const currentUsername = localStorage.getItem("octs_ai_username") || localStorage.getItem("generative_clash_username") || "Alex";
  const currentRole = localStorage.getItem("octs_ai_role") || localStorage.getItem("generative_clash_role") || "writers";
  const currentTheme = localStorage.getItem("octs_ai_theme") || "light";

  if (usernameInput) usernameInput.value = currentUsername;
  if (roleSelect && currentRole) roleSelect.value = currentRole;
  if (themeSelect) themeSelect.value = currentTheme;
}

function saveSettings() {
  const usernameInput = document.getElementById("settingsUsername");
  const roleSelect = document.getElementById("settingsRoleSelect");
  const themeSelect = document.getElementById("settingsThemeSelect");
  const feedback = document.getElementById("saveFeedback");

  if (usernameInput && usernameInput.value.trim()) {
    const val = usernameInput.value.trim();
    localStorage.setItem("octs_ai_username", val);
    localStorage.setItem("generative_clash_username", val);
  }

  if (roleSelect && roleSelect.value) {
    localStorage.setItem("octs_ai_role", roleSelect.value);
    localStorage.setItem("generative_clash_role", roleSelect.value);
  }

  if (themeSelect && themeSelect.value) {
    if (window.applyTheme) {
      window.applyTheme(themeSelect.value);
    } else {
      localStorage.setItem("octs_ai_theme", themeSelect.value);
      if (themeSelect.value === "dark") {
        document.documentElement.setAttribute("data-theme", "dark");
      } else {
        document.documentElement.removeAttribute("data-theme");
      }
    }
  }

  if (feedback) {
    feedback.style.display = "block";
    setTimeout(() => {
      feedback.style.display = "none";
    }, 2500);
  }

  // Refresh common header state
  if (window.initCommonState) {
    window.initCommonState();
  }
}

async function testBackendPing() {
  const testBtn = document.getElementById("testPingBtn");
  const pingResult = document.getElementById("pingResult");

  if (testBtn) testBtn.disabled = true;
  if (pingResult) pingResult.textContent = "Pinging FastAPI /ask endpoint...";

  const startTime = performance.now();
  try {
    const res = await fetch("/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt: "Diagnostics ping test." })
    });

    const elapsed = Math.round(performance.now() - startTime);

    if (res.ok) {
      if (pingResult) {
        pingResult.textContent = `✓ 200 OK — Backend & Gemini operational (${elapsed}ms).`;
        pingResult.style.color = "var(--success)";
      }
    } else {
      throw new Error(`Status ${res.status}`);
    }
  } catch (err) {
    if (pingResult) {
      pingResult.textContent = `✗ Connection error: ${err.message}. Ensure python server.py is running.`;
      pingResult.style.color = "var(--danger)";
    }
  } finally {
    if (testBtn) testBtn.disabled = false;
  }
}

function resetRoleChoice() {
  localStorage.removeItem("octs_ai_role");
  localStorage.removeItem("generative_clash_role");
  window.location.href = "../index.html";
}

window.saveSettings = saveSettings;
window.testBackendPing = testBackendPing;
window.resetRoleChoice = resetRoleChoice;
