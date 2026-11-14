/**
 * Octs AI - Settings Controller
 */

document.addEventListener("DOMContentLoaded", () => {
  loadCurrentSettings();
});

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
