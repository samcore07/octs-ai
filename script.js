/**
 * Octs AI - AI Creative Harness
 * Frontend Controller & API Integration
 */

// Creative Professions Configuration
const ROLES_DATA = {
  writers: {
    id: "writers",
    title: "Writers & Storytellers",
    tagline: "Ideas, storytelling, research and writing assistance.",
    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 19l7-7 3 3-7 7-3-3z"></path><path d="M18 13l-1.5-7.5L2 2l3.5 14.5L13 18l5-5z"></path><path d="M2 2l7.586 7.586"></path><circle cx="11" cy="11" r="2"></circle></svg>`,
    description: "Multi-agent coordination for narrative arcs, lore continuity, dialogue tension, and research auditing.",
    agents: [
      { name: "Narrative Architect", role: "3-Act Structure & Pacing", model: "Gemini 3.5 Flash", status: "Active" },
      { name: "Lore & Continuity Keeper", role: "Canon & World Consistency", model: "Gemini 3.5 Flash", status: "Armed" },
      { name: "Prose Stylist", role: "Dialogue & Sensory Tone", model: "Gemini 3.5 Flash", status: "Active" },
      { name: "Research Scout", role: "Domain & Fact Auditing", model: "Gemini 3.5 Flash", status: "Standby" }
    ],
    prompts: [
      {
        category: "Structure & Conflict",
        title: "Resolve Plot Bottleneck",
        prompt: "Untangle a plot bottleneck where the protagonist's motivation conflicts with Chapter 4."
      },
      {
        category: "Dialogue & Subtext",
        title: "Sharpen Dialogue Tension",
        prompt: "Audit dialogue consistency between two estranged siblings in a high-stakes confrontation."
      },
      {
        category: "Pacing & Stakes",
        title: "3-Act Tension Arc",
        prompt: "Build a 3-act tension arc with rising stakes for a psychological thriller."
      },
      {
        category: "Atmosphere & World",
        title: "Sensory Environment Spec",
        prompt: "Generate sensory details and atmosphere for an abandoned retro-futuristic research lab."
      }
    ]
  },
  musicians: {
    id: "musicians",
    title: "Musicians & Singers",
    tagline: "Music creation, songwriting and creative experimentation.",
    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18V5l12-2v13"></path><circle cx="6" cy="18" r="3"></circle><circle cx="18" cy="16" r="3"></circle></svg>`,
    description: "Multi-agent coordination for lyric cadence, harmonic substitutions, arrangement dynamics, and sonic curation.",
    agents: [
      { name: "Lyricist & Meter Engine", role: "Rhyme Cadence & Syllabic Stress", model: "Gemini 3.5 Flash", status: "Active" },
      { name: "Harmonic Arranger", role: "Chord Progressions & Modal Shifts", model: "Gemini 3.5 Flash", status: "Armed" },
      { name: "Track Structure Architect", role: "Dynamic Arranging & Tension Drops", model: "Gemini 3.5 Flash", status: "Active" },
      { name: "Sonic Palette Curator", role: "Genre Cross-Pollination", model: "Gemini 3.5 Flash", status: "Standby" }
    ],
    prompts: [
      {
        category: "Lyric Cadence",
        title: "Neo-Soul Chorus Hook",
        prompt: "Write a punchy neo-soul chorus with internal rhymes and unexpected modal chords."
      },
      {
        category: "Modal Harmonics",
        title: "Fresh Progression Resolution",
        prompt: "Resolve a chord progression from Dm7 to G7 that feels fresh, poignant, and melancholic."
      },
      {
        category: "Track Dynamics",
        title: "Electronic Tension Arrangement",
        prompt: "Create an arrangement timeline for an indie electronic track with tension drops."
      },
      {
        category: "Metaphor Lab",
        title: "Temporal Disorientation Imagery",
        prompt: "Brainstorm lyrical metaphors for the feeling of sudden temporal disorientation."
      }
    ]
  },
  creators: {
    id: "creators",
    title: "Content Creators",
    tagline: "Content planning, scripting, publishing and audience growth.",
    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="23 7 16 12 23 17 23 7"></polygon><rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect></svg>`,
    description: "Multi-agent coordination for viral opening hooks, script momentum audits, and omni-channel transmuting.",
    agents: [
      { name: "Hook & Retention Architect", role: "First 3-Second Hooks & Pacing", model: "Gemini 3.5 Flash", status: "Active" },
      { name: "Multi-Platform Transmuter", role: "Longform to Shorts/Reels/X", model: "Gemini 3.5 Flash", status: "Armed" },
      { name: "Editorial Cadence Planner", role: "Batch Production Scheduling", model: "Gemini 3.5 Flash", status: "Active" },
      { name: "Audience Friction Auditor", role: "Drop-off Analysis & CTR Optimization", model: "Gemini 3.5 Flash", status: "Standby" }
    ],
    prompts: [
      {
        category: "Retention Hooks",
        title: "5 High-Stakes Opening Hooks",
        prompt: "Generate 5 high-retention opening hooks for a video dissecting modern architectural failures."
      },
      {
        category: "Format Transmutation",
        title: "Longform to Vertical Script",
        prompt: "Transform an 8-minute technical essay into a 45-second high-energy vertical script."
      },
      {
        category: "Editorial Matrix",
        title: "4-Week Creative Tech Strategy",
        prompt: "Build a 4-week thematic content matrix around design engineering and creative tech."
      },
      {
        category: "Pacing Audit",
        title: "Drop-Off & Retention Review",
        prompt: "Audit this video script outline for pacing lulls and drop-off risks around minute 2."
      }
    ]
  },
  designers: {
    id: "designers",
    title: "Visual Artists & Designers",
    tagline: "Design workflows, visual ideation and creative exploration.",
    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="M14.31 8l5.74 9.94M9.69 8h11.48M7.38 12l5.74-9.94M9.69 16L3.95 6.06M14.31 16H2.83m13.79-4l-5.74 9.94"></path></svg>`,
    description: "Multi-agent coordination for art direction briefs, Swiss design critiques, visual metaphors, and token hierarchies.",
    agents: [
      { name: "Concept Ideation Engine", role: "Metaphorical Moodboarding & Themes", model: "Gemini 3.5 Flash", status: "Active" },
      { name: "Visual System Auditor", role: "Grid Hierarchy & Typography Scales", model: "Gemini 3.5 Flash", status: "Armed" },
      { name: "Art Direction Critic", role: "Color Harmony & Balance Critique", model: "Gemini 3.5 Flash", status: "Active" },
      { name: "Creative Asset Organizer", role: "Design Token Taxonomies", model: "Gemini 3.5 Flash", status: "Standby" }
    ],
    prompts: [
      {
        category: "Art Direction",
        title: "Modernism + Brutalism Direction",
        prompt: "Develop an art direction brief combining Swiss modernism with brutalist architecture."
      },
      {
        category: "Identity Critique",
        title: "Sustainable Aerospace Audit",
        prompt: "Critique a brand identity system for a sustainable aerospace startup."
      },
      {
        category: "Visual Metaphors",
        title: "Invisible Precision Concepts",
        prompt: "Generate 4 visual metaphors for 'invisible precision engineering'."
      },
      {
        category: "Design System",
        title: "Dark Analytics Palette & Scale",
        prompt: "Create a palette and typography hierarchy guide for a dark-mode creative analytics app."
      }
    ]
  }
};

// Global App State
let currentRole = localStorage.getItem("octs_ai_role") || localStorage.getItem("generative_clash_role") || null;
let currentTab = "dashboard";
let currentUsername = localStorage.getItem("octs_ai_username") || localStorage.getItem("generative_clash_username") || "Alex";

// DOM Initializer
document.addEventListener("DOMContentLoaded", () => {
  initUsername();
  initSidebarNavigation();
  initRoleSelection();
  initChatExecution();
  initThemeToggle();
  initProjectSelector();
  renderCreativeHistory();
  
  // If user previously selected a role, render that workspace immediately
  if (currentRole && ROLES_DATA[currentRole]) {
    renderRoleWorkspace(currentRole);
  } else {
    showRolePicker();
  }

  // Check if an agent or workflow deployed an auto-prompt from another page
  const autoPrompt = sessionStorage.getItem("harness_auto_prompt");
  if (autoPrompt) {
    sessionStorage.removeItem("harness_auto_prompt");
    setTimeout(() => {
      insertAndExecute(autoPrompt);
    }, 300);
  }
});

// Theme Management (Light / Dark)
function initThemeToggle() {
  const toggleBtn = document.getElementById("themeToggleBtn");
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
}

function updateThemeButton(theme) {
  const toggleBtn = document.getElementById("themeToggleBtn");
  if (!toggleBtn) return;
  toggleBtn.setAttribute("title", theme === "dark" ? "Switch to Light Mode" : "Switch to Dark Mode");
  toggleBtn.setAttribute("aria-label", theme === "dark" ? "Switch to Light Mode" : "Switch to Dark Mode");
}

// 1. User Profile Management
function initUsername() {
  const usernameDisplay = document.getElementById("displayUsername");
  const topbarUserDisplay = document.getElementById("topName");
  const avatarElements = document.querySelectorAll(".user-avatar");
  const settingsInput = document.getElementById("usernameSettingInput");

  if (usernameDisplay) usernameDisplay.textContent = currentUsername;
  if (topbarUserDisplay) topbarUserDisplay.textContent = currentUsername;
  if (settingsInput) settingsInput.value = currentUsername;

  const initial = currentUsername.charAt(0).toUpperCase() || "A";
  avatarElements.forEach(el => el.textContent = initial);
}

function updateUsername(newName) {
  if (!newName || !newName.trim()) return;
  currentUsername = newName.trim();
  localStorage.setItem("octs_ai_username", currentUsername);
  localStorage.setItem("generative_clash_username", currentUsername);
  initUsername();
}

// 2. Navigation & Sidebar
function initSidebarNavigation() {
  const navItems = document.querySelectorAll(".nav-item[data-tab]");
  navItems.forEach(item => {
    item.addEventListener("click", (e) => {
      e.preventDefault();
      const tabId = item.getAttribute("data-tab");
      setTab(tabId);
    });
  });

  const sidebarToggle = document.getElementById("sidebarToggleBtn");
  const sidebar = document.querySelector(".sidebar");
  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener("click", () => {
      if (window.innerWidth <= 768) {
        sidebar.classList.toggle("mobile-open");
      } else {
        sidebar.classList.toggle("collapsed");
      }
    });

    // Close mobile sidebar on Escape or outside click
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

function setTab(tabId) {
  currentTab = tabId;

  // Update nav item active states
  document.querySelectorAll(".nav-item").forEach(item => {
    if (item.getAttribute("data-tab") === tabId) {
      item.classList.add("active");
    } else {
      item.classList.remove("active");
    }
  });

  // Update views
  document.querySelectorAll(".tab-view").forEach(view => {
    view.classList.remove("active");
  });

  const activeView = document.getElementById(`view-${tabId}`);
  if (activeView) {
    activeView.classList.add("active");
  }

  // Update Topbar Breadcrumb
  const breadcrumbCurrent = document.getElementById("breadcrumbCurrent");
  if (breadcrumbCurrent) {
    const tabLabels = {
      dashboard: "Dashboard",
      agents: "My Agents",
      workflows: "Workflows",
      efficiency: "Efficiency",
      success: "Success Rate",
      failures: "Failures & Recovery",
      help: "Help & Support",
      settings: "Settings"
    };
    breadcrumbCurrent.textContent = tabLabels[tabId] || "Dashboard";
  }
}

// 3. Role Selection & Personalization
function initRoleSelection() {
  document.querySelectorAll(".role-card").forEach(card => {
    card.addEventListener("click", () => {
      const roleKey = card.getAttribute("data-role");
      selectRole(roleKey);
    });
  });

  document.querySelectorAll(".domain-tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const roleKey = btn.getAttribute("data-role");
      selectRole(roleKey);
    });
  });

  const switchRoleBtn = document.getElementById("switchRoleBtn");
  if (switchRoleBtn) {
    switchRoleBtn.addEventListener("click", switchRole);
  }
}

function selectRole(roleKey) {
  if (!ROLES_DATA[roleKey]) return;
  currentRole = roleKey;
  localStorage.setItem("octs_ai_role", roleKey);
  localStorage.setItem("generative_clash_role", roleKey);
  renderRoleWorkspace(roleKey);
}

function switchRole() {
  currentRole = null;
  localStorage.removeItem("octs_ai_role");
  localStorage.removeItem("generative_clash_role");
  showRolePicker();
}

function showRolePicker() {
  const rolePicker = document.getElementById("rolePickerScreen");
  const roleWorkspace = document.getElementById("roleWorkspaceScreen");
  const sidebarRoleBadge = document.getElementById("sidebarRoleIndicator");
  const topbarRoleBtn = document.getElementById("topbarRoleBtn");

  if (rolePicker) rolePicker.style.display = "block";
  if (roleWorkspace) roleWorkspace.classList.remove("visible");
  if (sidebarRoleBadge) sidebarRoleBadge.style.display = "none";
  if (topbarRoleBtn) topbarRoleBtn.style.display = "none";

  // Deselect any card styling
  document.querySelectorAll(".role-card").forEach(c => c.classList.remove("selected"));

  // Ensure on Dashboard tab
  setTab("dashboard");
}

function renderRoleWorkspace(roleKey) {
  const data = ROLES_DATA[roleKey];
  if (!data) return;

  const rolePicker = document.getElementById("rolePickerScreen");
  const roleWorkspace = document.getElementById("roleWorkspaceScreen");
  const sidebarRoleBadge = document.getElementById("sidebarRoleIndicator");
  const sidebarRoleText = document.getElementById("sidebarRoleText");
  const topbarRoleBtn = document.getElementById("topbarRoleBtn");
  const topbarRoleName = document.getElementById("topbarRoleName");

  if (rolePicker) rolePicker.style.display = "none";
  if (roleWorkspace) roleWorkspace.classList.add("visible");
  
  if (sidebarRoleBadge) {
    sidebarRoleBadge.style.display = "flex";
    if (sidebarRoleText) sidebarRoleText.textContent = data.title;
  }

  if (topbarRoleBtn) {
    topbarRoleBtn.style.display = "inline-flex";
    if (topbarRoleName) topbarRoleName.textContent = data.title;
  }

  // Sync Domain Selector Bar
  document.querySelectorAll(".domain-tab-btn").forEach(btn => {
    if (btn.getAttribute("data-role") === roleKey) {
      btn.classList.add("active");
    } else {
      btn.classList.remove("active");
    }
  });

  // Update Workspace Header
  const titleEl = document.getElementById("workspaceRoleTitle");
  const descEl = document.getElementById("workspaceRoleDesc");
  if (titleEl) titleEl.textContent = data.title;
  if (descEl) descEl.textContent = data.description;

  // Render Active Agent Cohort (Selected Mode Active, Others in Standby)
  renderActiveCohort(roleKey);

  // Render Suggested Creative Directives (Interactive Cards)
  const promptsGrid = document.getElementById("suggestedPromptsGrid");
  if (promptsGrid && data.prompts) {
    promptsGrid.innerHTML = data.prompts.map((item, idx) => {
      const promptText = typeof item === "string" ? item : item.prompt;
      const title = typeof item === "string" ? item : (item.title || "Directive");
      const category = typeof item === "string" ? data.title.split(" ")[0] : (item.category || "Creative");
      return `
        <div class="directive-card" data-idx="${idx}">
          <div class="directive-card-top">
            <span class="directive-tag">${category}</span>
            <button type="button" class="directive-run-btn" title="Run directive immediately">
              <span>Run</span>
              <span class="run-icon">▶</span>
            </button>
          </div>
          <div class="directive-title">${title}</div>
          <div class="directive-prompt-preview">${promptText}</div>
        </div>
      `;
    }).join("");

    // Attach event listeners directly (safe from HTML attribute quote truncation)
    promptsGrid.querySelectorAll(".directive-card").forEach((card, idx) => {
      const item = data.prompts[idx];
      const promptText = typeof item === "string" ? item : item.prompt;

      card.addEventListener("click", () => {
        insertPrompt(promptText, card);
      });

      const runBtn = card.querySelector(".directive-run-btn");
      if (runBtn) {
        runBtn.addEventListener("click", (e) => {
          e.stopPropagation();
          runDirective(promptText);
        });
      }
    });
  }

  // Update Placeholder in Chatbox
  const chatInput = document.getElementById("chatInput");
  if (chatInput) {
    chatInput.placeholder = `Tell your AI harness what you're trying to create in ${data.title}...`;
  }
}

// Cohort & Active Specialist Definitions
const COHORT_DATA = {
  writers: {
    title: "Writers & Storytellers",
    agents: [
      { name: "Narrative Architect", role: "3-Act Beats & Stakes" },
      { name: "Lore & Continuity Keeper", role: "Canon & Timeline Paradoxes" },
      { name: "Prose Stylist & Dialogue Doctor", role: "Subtext & Sensory Polish" },
      { name: "Research & Fact Scout", role: "Historical & Technical Nuance" },
    ],
  },
  musicians: {
    title: "Musicians & Singers",
    agents: [
      { name: "Lyricist & Meter Engine", role: "Syllabic Cadence & Rhyme" },
      { name: "Harmonic Arranger", role: "Modal Interchange & Voicing" },
      { name: "Track Structure Architect", role: "Arrangement & Dynamic Peaks" },
      { name: "Sonic Palette Curator", role: "Genre Synthesis & Timbre" },
    ],
  },
  creators: {
    title: "Content Creators",
    agents: [
      { name: "Hook & Retention Architect", role: "First 3s Retention Hooks" },
      { name: "Multi-Platform Transmuter", role: "Vertical & Thread Repurposing" },
      { name: "Editorial Cadence Planner", role: "30-Day Batching Schedules" },
      { name: "Audience Friction Auditor", role: "Cognitive Load & CTA Audit" },
    ],
  },
  designers: {
    title: "Visual Artists & Designers",
    agents: [
      { name: "Concept Ideation Engine", role: "Cross-Disciplinary Moodboards" },
      { name: "Visual System Auditor", role: "Typographic Scale & Grids" },
      { name: "Art Direction Critic", role: "Negative Space & Focal Hierarchy" },
      { name: "Design Token & Palette Architect", role: "APCA Contrast & Semantic Scales" },
    ],
  },
};

function renderActiveCohort(roleKey) {
  const cohort = COHORT_DATA[roleKey] || COHORT_DATA.writers;
  const titleEl = document.getElementById("cohortDisciplineTitle");
  const subtextEl = document.getElementById("cohortSubtext");
  const pillsEl = document.getElementById("cohortAgentPills");

  if (titleEl) titleEl.textContent = cohort.title;
  if (subtextEl) subtextEl.textContent = `(4 Cohort Agents Active & Ready • 12 in Standby)`;
  if (pillsEl) {
    pillsEl.innerHTML = cohort.agents.map(ag => `
      <span class="cohort-mini-pill active" title="${ag.role}">
        <span class="dot"></span>
        ${ag.name}
      </span>
    `).join("");
  }
}

// 4. Prompt Helpers & Quick Execution
function insertPrompt(text, cardEl) {
  const chatInput = document.getElementById("chatInput");
  if (chatInput) {
    chatInput.value = text;
    chatInput.focus();
    chatInput.scrollIntoView({ behavior: "smooth", block: "center" });

    if (cardEl) {
      document.querySelectorAll(".directive-card").forEach(c => c.classList.remove("active-directive"));
      cardEl.classList.add("active-directive");
      setTimeout(() => cardEl.classList.remove("active-directive"), 1800);
    }
  }
}

function runDirective(text) {
  const chatInput = document.getElementById("chatInput");
  if (chatInput) {
    chatInput.value = text;
    chatInput.focus();
    submitTask();
  }
}

function insertAndExecute(text) {
  runDirective(text);
}

function clearPromptInput() {
  const chatInput = document.getElementById("chatInput");
  if (chatInput) {
    chatInput.value = "";
    chatInput.focus();
  }
}

// ============================================================================
// Creative History & Answer Archive System
// ============================================================================

function saveToCreativeHistory(prompt, reply, metadata = {}) {
  try {
    const raw = localStorage.getItem("octs_creative_history");
    const history = raw ? JSON.parse(raw) : [];

    const item = {
      id: "req_" + Date.now(),
      timestamp: new Date().toISOString(),
      prompt: prompt,
      reply: reply,
      role: currentRole || "writers",
      agent: metadata.agent || "Auto-Routed Lead",
      latency_ms: metadata.latency_ms || null,
      model: metadata.model || "Gemini 3.5 Flash",
      agent_pipeline: metadata.agent_pipeline || null,
    };

    history.unshift(item);
    if (history.length > 40) history.pop();

    localStorage.setItem("octs_creative_history", JSON.stringify(history));
    renderCreativeHistory();
  } catch (e) {
    console.error("Failed to save session history:", e);
  }
}

function renderCreativeHistory() {
  const container = document.getElementById("historyListGrid");
  const countBadge = document.getElementById("historyCountBadge");
  if (!container) return;

  try {
    const raw = localStorage.getItem("octs_creative_history");
    const history = raw ? JSON.parse(raw) : [];

    if (countBadge) {
      countBadge.textContent = `${history.length} Saved`;
    }

    if (!history.length) {
      container.innerHTML = `<div class="empty-history-hint">Executed requests and generated responses are saved and archived here for quick re-use.</div>`;
      return;
    }

    container.innerHTML = history.map(item => {
      const timeStr = new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      const agentName = formatAgentDisplayName(item.agent);
      return `
        <div class="history-item-card" data-id="${item.id}">
          <div class="history-item-header">
            <div style="display: flex; align-items: center; gap: 8px;">
              <span class="specialist-pill" style="font-size: 10px; padding: 1px 6px;">${agentName}</span>
              <span style="font-family: var(--font-mono); font-size: 10px; color: var(--text-muted);">${timeStr}</span>
            </div>
            ${item.latency_ms ? `<span style="font-family: var(--font-mono); font-size: 10px; color: var(--text-muted);">${item.latency_ms}ms</span>` : ""}
          </div>
          <div class="history-item-prompt">${escapeHtml(item.prompt)}</div>
          <div class="history-item-preview">${escapeHtml(item.reply)}</div>
          <div class="history-item-actions">
            <button type="button" class="restore-btn" onclick="restoreHistoryItem('${item.id}')">
              <span>Restore to Canvas</span>
              <span>↳</span>
            </button>
            <button type="button" class="copy-btn" onclick="copyHistoricalReply('${item.id}')" style="padding: 3px 8px; font-size: 10px;">
              <span>Copy Output</span>
            </button>
          </div>
        </div>
      `;
    }).join("");
  } catch (e) {
    console.error("Failed to render creative history:", e);
  }
}

function restoreHistoryItem(id) {
  try {
    const raw = localStorage.getItem("octs_creative_history");
    const history = raw ? JSON.parse(raw) : [];
    const found = history.find(item => item.id === id);
    if (!found) return;

    const chatInput = document.getElementById("chatInput");
    const outputDiv = document.getElementById("output");
    const agentBadge = document.getElementById("agentBadge");
    const latencyBadge = document.getElementById("latencyBadge");

    if (chatInput) chatInput.value = found.prompt;
    if (outputDiv) {
      outputDiv.classList.remove("empty-state");
      outputDiv.innerHTML = renderMarkdown(found.reply);
      outputDiv.scrollIntoView({ behavior: "smooth", block: "center" });
    }
    if (agentBadge) agentBadge.textContent = formatAgentDisplayName(found.agent);
    if (latencyBadge && found.latency_ms) latencyBadge.textContent = `${found.latency_ms}ms`;
    if (found.agent_pipeline) {
      renderOrchestrationTrace(found.agent_pipeline, found.latency_ms);
    }
  } catch (e) {
    console.error("Failed to restore history item:", e);
  }
}

function copyHistoricalReply(id) {
  try {
    const raw = localStorage.getItem("octs_creative_history");
    const history = raw ? JSON.parse(raw) : [];
    const found = history.find(item => item.id === id);
    if (found && found.reply) {
      navigator.clipboard.writeText(found.reply);
    }
  } catch (e) {
    console.error("Failed to copy history item:", e);
  }
}

function clearCreativeHistory() {
  localStorage.removeItem("octs_creative_history");
  renderCreativeHistory();
}

function escapeHtml(text) {
  if (!text) return "";
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// 5. Backend Execution & Copy Logic
function initChatExecution() {
  const sendBtn = document.getElementById("sendBtn");
  const chatInput = document.getElementById("chatInput");

  if (sendBtn) {
    sendBtn.addEventListener("click", submitTask);
  }

  if (chatInput) {
    chatInput.addEventListener("keydown", (e) => {
      // Submit on Enter without Shift, or Cmd/Ctrl + Enter
      if ((e.key === "Enter" && !e.shiftKey) || (e.key === "Enter" && (e.metaKey || e.ctrlKey))) {
        e.preventDefault();
        submitTask();
      }
    });
  }
}

function formatAgentDisplayName(personaId) {
  if (!personaId) return "Auto-Routed Lead";
  const nameMap = {
    narrative_architect: "Narrative Architect",
    lore_continuity_keeper: "Lore & Continuity Keeper",
    prose_stylist: "Prose Stylist",
    research_scout: "Research Scout",
    lyricist_meter_engine: "Lyricist & Meter Engine",
    harmonic_arranger: "Harmonic Arranger",
    track_structure_architect: "Track Structure Architect",
    sonic_palette_curator: "Sonic Palette Curator",
    hook_retention_architect: "Hook & Retention Architect",
    multi_platform_transmuter: "Multi-Platform Transmuter",
    editorial_cadence_planner: "Editorial Cadence Planner",
    audience_friction_auditor: "Audience Friction Auditor",
    concept_ideation_engine: "Concept Ideation Engine",
    visual_system_auditor: "Visual System Auditor",
    art_direction_critic: "Art Direction Critic",
    design_token_palette_architect: "Design Token Architect"
  };
  return nameMap[personaId] || personaId.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
}

function renderMarkdown(text) {
  if (!text) return "";
  let safe = text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  safe = safe.replace(/^### (.*$)/gim, '<h4 class="md-h4">$1</h4>');
  safe = safe.replace(/^## (.*$)/gim, '<h3 class="md-h3">$1</h3>');
  safe = safe.replace(/^# (.*$)/gim, '<h2 class="md-h2">$1</h2>');

  safe = safe.replace(/\*\*\*(.*?)\*\*\*/gim, '<strong><em>$1</em></strong>');
  safe = safe.replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>');
  safe = safe.replace(/\*(.*?)\*/gim, '<em>$1</em>');

  safe = safe.replace(/`([^`]+)`/gim, '<code class="md-code">$1</code>');
  safe = safe.replace(/^---$/gim, '<hr class="md-hr">');
  safe = safe.replace(/^\> (.*$)/gim, '<blockquote class="md-quote">$1</blockquote>');
  safe = safe.replace(/^[\*\-] (.*$)/gim, '<li class="md-li">$1</li>');
  safe = safe.replace(/\n/gim, '<br>');

  return safe;
}

function getModelPillClass(modelName) {
  if (!modelName) return "model-35";
  const m = modelName.toLowerCase();
  if (m.includes("3.8")) return "model-38";
  if (m.includes("3.6")) return "model-36";
  if (m.includes("3.1")) return "model-31";
  return "model-35";
}

function renderOrchestrationTrace(pipeline, latencyMs) {
  const container = document.getElementById("traceStepsContainer");
  if (!container) return;

  if (!pipeline || !Array.isArray(pipeline) || pipeline.length === 0) {
    container.innerHTML = `<div class="empty-trace-hint">No multi-agent trace available for this execution.</div>`;
    return;
  }

  container.innerHTML = pipeline.map((step, idx) => {
    const stepNum = idx + 1;
    const modelPillClass = getModelPillClass(step.model);
    const tokensText = step.tokens
      ? `${step.tokens.prompt || 0} in / ${step.tokens.completion || 0} out (${step.tokens.total || 0} tokens)`
      : "";
    const durText = step.duration_ms ? `${step.duration_ms}ms` : "";

    return `
      <div class="trace-step-card">
        <div class="trace-step-num-col">
          <div class="step-circle">${stepNum}</div>
          ${idx < pipeline.length - 1 ? '<div class="step-line"></div>' : ''}
        </div>
        <div class="trace-step-body">
          <div class="step-agent-header">
            <div class="step-agent-title-wrap">
              <span class="step-agent-name">${escapeHtml(step.agent_name || "Specialist Agent")}</span>
              <span class="step-agent-role">${escapeHtml(step.agent_role || "Agent")}</span>
            </div>
            <div class="step-model-pill ${modelPillClass}">
              <span>⚡</span>
              <span>${escapeHtml(step.model || "gemini-3.5-flash-lite")}</span>
            </div>
          </div>
          <div class="step-action-desc">${escapeHtml(step.action || "")}</div>
          <div class="step-meta-row">
            <span class="step-status-tag">● ${escapeHtml(step.status || "Completed").toUpperCase()}</span>
            <div class="step-metrics-badge">
              ${tokensText ? `<span>${tokensText}</span> • ` : ""}
              <span>${durText}</span>
            </div>
          </div>
        </div>
      </div>
    `;
  }).join("");
}

async function submitTask() {
  const chatInput = document.getElementById("chatInput") || document.getElementById("promptInput");
  const outputDiv = document.getElementById("output");
  const sendBtn = document.getElementById("sendBtn");
  const consoleStatus = document.getElementById("consoleStatusPill");
  const latencyBadge = document.getElementById("latencyBadge");
  const agentBadge = document.getElementById("agentBadge");
  const engineBadge = document.getElementById("engineBadge");
  const statusBadge = document.getElementById("statusBadge");
  const pipelineIndicator = document.getElementById("pipelineIndicator");
  const refinementItem = document.getElementById("refinementItem");
  const refinementBadge = document.getElementById("refinementBadge");
  const memoryItem = document.getElementById("memoryItem");
  const memoryBadge = document.getElementById("memoryBadge");
  const activeProjectSelect = document.getElementById("activeProjectSelect");
  const selectedProjectId = activeProjectSelect && activeProjectSelect.value ? activeProjectSelect.value : null;

  const userInput = chatInput ? chatInput.value.trim() : "";
  if (!userInput) return;

  // Visual Loading State
  if (sendBtn) sendBtn.disabled = true;
  if (outputDiv) {
    outputDiv.classList.remove("empty-state");
    outputDiv.textContent = "AI Creative Harness orchestrating agents...\nAnalyzing intent and formulating domain-specific execution plan...";
  }

  const traceContainer = document.getElementById("traceStepsContainer");
  if (traceContainer) {
    traceContainer.innerHTML = `
      <div class="empty-trace-hint" style="color: var(--accent); font-weight: 500;">
        ⚡ Multi-Agent Pipeline Activating: Coordinating specialists across Gemini free models (gemini-3.8-flash, gemini-3.5-flash-lite, gemini-3.6-flash, gemini-3.1-flash-lite)...
      </div>
    `;
  }
  if (consoleStatus) {
    consoleStatus.textContent = "● ORCHESTRATING (GEMINI)";
    consoleStatus.style.color = "#F59E0B";
    consoleStatus.style.background = "rgba(245, 158, 11, 0.15)";
    consoleStatus.style.borderColor = "rgba(245, 158, 11, 0.3)";
  }
  if (pipelineIndicator) {
    pipelineIndicator.innerHTML = `
      <span class="pipeline-step">Input</span> → 
      <span class="pipeline-step">Intent</span> → 
      <span class="pipeline-step active">Coordinating Agents</span> → 
      <span class="pipeline-step">Verifying</span>
    `;
  }

  const startTime = performance.now();

  try {
    const payload = {
      prompt: userInput,
      role: currentRole || null,
      project_id: selectedProjectId || undefined
    };

    const response = await fetch("/ask", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    });

    const elapsedMs = Math.round(performance.now() - startTime);

    if (!response.ok) {
      throw new Error(`Server returned status ${response.status}`);
    }

    const data = await response.json();
    const replyText = data.reply || "No response received from creative harness.";

    if (outputDiv) {
      outputDiv.innerHTML = renderMarkdown(replyText);
    }

    if (latencyBadge) {
      latencyBadge.textContent = `${data.latency_ms || elapsedMs}ms`;
    }

    if (engineBadge && data.model_used) {
      engineBadge.textContent = data.model_used;
    }

    if (agentBadge) {
      agentBadge.textContent = formatAgentDisplayName(data.agent_used);
    }

    if (refinementItem && refinementBadge) {
      if (data.recovery_triggered && data.refinement) {
        refinementItem.style.display = "flex";
        const delta = data.refinement.quality_delta;
        const attempts = data.refinement.recovery_attempts || 1;
        const reviewer = data.refinement.reviewer_persona_id ? ` via ${formatAgentDisplayName(data.refinement.reviewer_persona_id)}` : "";
        const deltaText = delta != null ? (delta >= 0 ? `+${delta.toFixed(1)} pts` : `${delta.toFixed(1)} pts`) : `Attempt ${attempts}`;
        refinementBadge.textContent = `Corrected (${deltaText}${reviewer})`;
        refinementBadge.style.color = "#60A5FA";
      } else {
        refinementItem.style.display = "none";
      }
    }

    if (memoryItem && memoryBadge) {
      if (data.memory && data.memory.enabled) {
        memoryItem.style.display = "flex";
        if (data.memory.memories_used > 0) {
          memoryBadge.textContent = `${data.memory.memories_used} active`;
          memoryBadge.style.color = "#A78BFA";
        } else if (data.memory.extraction_performed) {
          memoryBadge.textContent = `Extracted`;
          memoryBadge.style.color = "#34D399";
        } else {
          memoryBadge.textContent = `Online`;
          memoryBadge.style.color = "#9CA3AF";
        }
      } else {
        memoryItem.style.display = "none";
      }
    }

    if (data.needs_clarification) {
      if (consoleStatus) {
        consoleStatus.textContent = "● CLARIFICATION NEEDED";
        consoleStatus.style.color = "#F59E0B";
        consoleStatus.style.background = "rgba(245, 158, 11, 0.15)";
        consoleStatus.style.borderColor = "rgba(245, 158, 11, 0.3)";
      }
      if (statusBadge) {
        statusBadge.textContent = "Clarification Needed";
        statusBadge.style.color = "#F59E0B";
      }
      if (pipelineIndicator) {
        pipelineIndicator.innerHTML = `
          <span class="pipeline-step">Input</span> → 
          <span class="pipeline-step active">Clarification Requested</span>
        `;
      }
    } else if (data.recovery_triggered) {
      if (consoleStatus) {
        consoleStatus.textContent = "● REFINED & VERIFIED";
        consoleStatus.style.color = "#60A5FA";
        consoleStatus.style.background = "rgba(96, 165, 250, 0.15)";
        consoleStatus.style.borderColor = "rgba(96, 165, 250, 0.3)";
      }
      if (statusBadge) {
        statusBadge.textContent = "Refined / Verified";
        statusBadge.style.color = "#60A5FA";
      }
      if (pipelineIndicator) {
        pipelineIndicator.innerHTML = `
          <span class="pipeline-step">Input</span> → 
          <span class="pipeline-step">Draft</span> → 
          <span class="pipeline-step">Peer Critique</span> → 
          <span class="pipeline-step active">Autonomous Refinement ✓</span>
        `;
      }
    } else {
      if (consoleStatus) {
        consoleStatus.textContent = "● VERIFIED OUTPUT";
        consoleStatus.style.color = "#34D399";
        consoleStatus.style.background = "rgba(16, 185, 129, 0.15)";
        consoleStatus.style.borderColor = "rgba(16, 185, 129, 0.3)";
      }
      if (statusBadge) {
        statusBadge.textContent = "Active / Verified";
        statusBadge.style.color = "#34D399";
      }
      if (pipelineIndicator) {
        pipelineIndicator.innerHTML = `
          <span class="pipeline-step">Input</span> → 
          <span class="pipeline-step">Intent</span> → 
          <span class="pipeline-step">Coordinated</span> → 
          <span class="pipeline-step active">Output Verified ✓</span>
        `;
      }
    }

    // Render Multi-Agent Orchestration & Model Dispatch Trace
    if (data.agent_pipeline) {
      renderOrchestrationTrace(data.agent_pipeline, data.latency_ms || elapsedMs);
    }

    // Persist request and answer to session history archive
    saveToCreativeHistory(userInput, replyText, {
      agent: data.agent_used,
      latency_ms: data.latency_ms || elapsedMs,
      model: data.model_used,
      agent_pipeline: data.agent_pipeline,
    });

  } catch (error) {
    console.error("Execution error:", error);
    if (outputDiv) {
      outputDiv.textContent = `Error: Could not connect to backend harness (${error.message}).\nVerify that the Python backend server is running on http://127.0.0.1:8000.`;
    }
    if (consoleStatus) {
      consoleStatus.textContent = "● EXECUTION HALTED";
      consoleStatus.style.color = "#EF4444";
      consoleStatus.style.background = "rgba(239, 68, 68, 0.15)";
      consoleStatus.style.borderColor = "rgba(239, 68, 68, 0.3)";
    }
  } finally {
    if (sendBtn) sendBtn.disabled = false;
  }
}

// 6. Copy Response Function
function copyResponse() {
  const outputEl = document.getElementById("output");
  const copyBtn = document.getElementById("copyBtn");
  
  if (!outputEl) return;
  const text = outputEl.innerText.trim();
  
  if (!text || text.startsWith("Tell your AI harness") || text.startsWith("AI Creative Harness output will appear here")) {
    return;
  }

  navigator.clipboard.writeText(text).then(() => {
    if (!copyBtn) return;
    const originalContent = copyBtn.innerHTML;
    copyBtn.innerHTML = `<span>✓</span><span>Copied!</span>`;
    setTimeout(() => {
      copyBtn.innerHTML = originalContent;
    }, 2000);
  }).catch((err) => {
    console.error("Clipboard write error:", err);
  });
}

// 7. Project Context Initializer
async function initProjectSelector() {
  const activeProjectSelect = document.getElementById("activeProjectSelect");
  if (!activeProjectSelect) return;

  try {
    const res = await fetch("/api/memory/projects");
    if (!res.ok) return;
    const projects = await res.json();
    if (Array.isArray(projects) && projects.length > 0) {
      // Clear all except global
      activeProjectSelect.innerHTML = '<option value="">Global (No Project)</option>';
      projects.forEach((proj) => {
        const opt = document.createElement("option");
        opt.value = proj.project_id;
        opt.textContent = `${proj.name} (${proj.discipline || 'general'})`;
        activeProjectSelect.appendChild(opt);
      });
    }
  } catch (err) {
    console.debug("Projects API unavailable:", err);
  }
}

// Global API Exposure for Compatibility
window.submitTask = submitTask;
window.sendMessage = submitTask;
window.copyResponse = copyResponse;
window.selectRole = selectRole;
window.switchRole = switchRole;
window.setTab = setTab;
window.insertPrompt = insertPrompt;
window.insertAndExecute = insertAndExecute;
window.clearPromptInput = clearPromptInput;
window.updateUsername = updateUsername;
window.applyTheme = applyTheme;
window.initProjectSelector = initProjectSelector;
