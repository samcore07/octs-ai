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
    description: "Your AI harness coordinates narrative architects, lore continuity auditors, prose refiners, and fact scouts to unblock your writing and elevate story craft.",
    agents: [
      { name: "Narrative Architect", role: "3-Act Structure & Pacing", model: "Gemini 3.5 Flash", status: "Active" },
      { name: "Lore & Continuity Keeper", role: "Canon & World Consistency", model: "Gemini 3.5 Flash", status: "Armed" },
      { name: "Prose Stylist", role: "Dialogue & Sensory Tone", model: "Gemini 3.5 Flash", status: "Active" },
      { name: "Research Scout", role: "Domain & Fact Auditing", model: "Gemini 3.5 Flash", status: "Standby" }
    ],
    prompts: [
      "Untangle a plot bottleneck where the protagonist's motivation conflicts with Chapter 4.",
      "Audit dialogue consistency between two estranged siblings in a high-stakes confrontation.",
      "Build a 3-act tension arc with rising stakes for a psychological thriller.",
      "Generate sensory details and atmosphere for an abandoned retro-futuristic research lab."
    ],
    toolkit: [
      {
        title: "Writer's Block Breaker",
        desc: "Break through stagnation by exploring 3 unconventional plot twists and pivot scenes.",
        prompt: "I am facing writer's block at a transition point in my story. Generate 3 compelling, unexpected ways to push the narrative forward with high emotional stakes."
      },
      {
        title: "Dialogue Doctor",
        desc: "Sharpen character exchanges to remove exposition and amplify subtext.",
        prompt: "Sharpen this dialogue exchange to remove flat exposition, amplify subtext, and ensure distinct character voices."
      },
      {
        title: "World & Lore Continuity Audit",
        desc: "Scan narrative elements for contradictions, timeline inconsistencies, and magic system gaps.",
        prompt: "Audit this scene outline for lore consistency, timeline paradoxes, and unearned character choices."
      }
    ]
  },
  musicians: {
    id: "musicians",
    title: "Musicians & Singers",
    tagline: "Music creation, songwriting and creative experimentation.",
    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18V5l12-2v13"></path><circle cx="6" cy="18" r="3"></circle><circle cx="18" cy="16" r="3"></circle></svg>`,
    description: "Your AI harness coordinates lyric meter engines, harmonic arrangers, vocal hook designers, and sonic palette curators to craft captivating songs and break creative blocks.",
    agents: [
      { name: "Lyricist & Meter Engine", role: "Rhyme Cadence & Syllabic Stress", model: "Gemini 3.5 Flash", status: "Active" },
      { name: "Harmonic Arranger", role: "Chord Progressions & Modal Shifts", model: "Gemini 3.5 Flash", status: "Armed" },
      { name: "Track Structure Architect", role: "Dynamic Arranging & Tension Drops", model: "Gemini 3.5 Flash", status: "Active" },
      { name: "Sonic Palette Curator", role: "Genre Cross-Pollination", model: "Gemini 3.5 Flash", status: "Standby" }
    ],
    prompts: [
      "Write a punchy neo-soul chorus with internal rhymes and unexpected modal chords.",
      "Resolve a chord progression from Dm7 to G7 that feels fresh, poignant, and melancholic.",
      "Create an arrangement timeline for an indie electronic track with tension drops.",
      "Brainstorm lyrical metaphors for the feeling of sudden temporal disorientation."
    ],
    toolkit: [
      {
        title: "Chorus Hook Workshop",
        desc: "Develop 3 infectious, high-contrast vocal hooks with phonetic cadence maps.",
        prompt: "Write 3 distinct chorus hook options for an energetic indie-pop track, focusing on vowel resonance and rhythmic syncopation."
      },
      {
        title: "Modal Chord Substitution",
        desc: "Transform predictable 4-chord progressions into sophisticated harmonic journeys.",
        prompt: "Take a standard I-V-vi-IV progression and provide 3 jazz/neo-soul chord substitution variants with voice leading."
      },
      {
        title: "Bridge Breakthrough Lab",
        desc: "Design an emotionally transcendent bridge that revitalizes the track before the final chorus.",
        prompt: "Construct a song bridge that shifts modulation and dynamic texture to deliver an emotional peak before the final chorus."
      }
    ]
  },
  creators: {
    id: "creators",
    title: "Content Creators",
    tagline: "Content planning, scripting, publishing and audience growth.",
    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="23 7 16 12 23 17 23 7"></polygon><rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect></svg>`,
    description: "Your AI harness coordinates viral hook architects, cross-platform transmuters, editorial cadence planners, and audience retention auditors to maximize reach and consistency.",
    agents: [
      { name: "Hook & Retention Architect", role: "First 3-Second Hooks & Pacing", model: "Gemini 3.5 Flash", status: "Active" },
      { name: "Multi-Platform Transmuter", role: "Longform to Shorts/Reels/X", model: "Gemini 3.5 Flash", status: "Armed" },
      { name: "Editorial Cadence Planner", role: "Batch Production Scheduling", model: "Gemini 3.5 Flash", status: "Active" },
      { name: "Audience Friction Auditor", role: "Drop-off Analysis & CTR Optimization", model: "Gemini 3.5 Flash", status: "Standby" }
    ],
    prompts: [
      "Generate 5 high-retention opening hooks for a video dissecting modern architectural failures.",
      "Transform an 8-minute technical essay into a 45-second high-energy vertical script.",
      "Build a 4-week thematic content matrix around design engineering and creative tech.",
      "Audit this video script outline for pacing lulls and drop-off risks around minute 2."
    ],
    toolkit: [
      {
        title: "Viral Hook Matrix",
        desc: "Test 5 hook formulas (Curiosity Gap, High-Stakes Thesis, Story Open-Loop, Counter-Intuitive Truth).",
        prompt: "Generate 5 high-retention video opening hooks using distinct psychological formulas: Curiosity Gap, Counter-Intuitive Truth, and Story Open-Loop."
      },
      {
        title: "Script Pacing & Retention Audit",
        desc: "Audit script sections for momentum dips, dead air, and cognitive friction.",
        prompt: "Audit this script outline for 60-second video pacing. Flag where audience attention might drop and provide tighter line edits."
      },
      {
        title: "Omni-Channel Repurposing Engine",
        desc: "Transmute a single core concept into a LinkedIn breakdown, X thread, and 2 short video concepts.",
        prompt: "Convert this core video concept into: 1 actionable 7-post X thread, and 2 distinct 45-second vertical script ideas."
      }
    ]
  },
  designers: {
    id: "designers",
    title: "Visual Artists & Designers",
    tagline: "Design workflows, visual ideation and creative exploration.",
    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="M14.31 8l5.74 9.94M9.69 8h11.48M7.38 12l5.74-9.94M9.69 16L3.95 6.06M14.31 16H2.83m13.79-4l-5.74 9.94"></path></svg>`,
    description: "Your AI harness coordinates concept ideation engines, visual system auditors, art direction critics, and asset workflow organizers for impeccable aesthetics.",
    agents: [
      { name: "Concept Ideation Engine", role: "Metaphorical Moodboarding & Themes", model: "Gemini 3.5 Flash", status: "Active" },
      { name: "Visual System Auditor", role: "Grid Hierarchy & Typography Scales", model: "Gemini 3.5 Flash", status: "Armed" },
      { name: "Art Direction Critic", role: "Color Harmony & Balance Critique", model: "Gemini 3.5 Flash", status: "Active" },
      { name: "Creative Asset Organizer", role: "Design Token Taxonomies", model: "Gemini 3.5 Flash", status: "Standby" }
    ],
    prompts: [
      "Develop an art direction brief combining Swiss modernism with brutalist architecture.",
      "Critique a brand identity system for a sustainable aerospace startup.",
      "Generate 4 visual metaphors for 'invisible precision engineering'.",
      "Create a palette and typography hierarchy guide for a dark-mode creative analytics app."
    ],
    toolkit: [
      {
        title: "Art Direction Brief Synthesizer",
        desc: "Generate a holistic creative direction spec including lighting, framing, palette, and typography.",
        prompt: "Draft a comprehensive art direction brief for an editorial brand, specifying color palette (hex), typography pairings, visual metaphors, and layout rules."
      },
      {
        title: "Design Critique Simulator",
        desc: "Get an uncompromising Swiss-style critique on layout balance, visual hierarchy, and contrast.",
        prompt: "Act as an experienced Design Director. Provide a thorough critique on the hierarchy, white space balance, and typography rhythm of this concept."
      },
      {
        title: "Design Token & Palette Architect",
        desc: "Generate harmonious light and dark color scales with semantic token assignments.",
        prompt: "Create an accessible color palette featuring primary, accent, and semantic status colors with contrast ratios and token naming conventions."
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

  // Update Workspace Header
  const titleEl = document.getElementById("workspaceRoleTitle");
  const descEl = document.getElementById("workspaceRoleDesc");
  if (titleEl) titleEl.textContent = `Welcome to your ${data.title} workspace.`;
  if (descEl) descEl.textContent = data.description;

  // Render Coordination Agents List
  const agentsListEl = document.getElementById("coordinationAgentsList");
  if (agentsListEl) {
    agentsListEl.innerHTML = data.agents.map(ag => `
      <div class="agent-chip" title="${ag.role} (${ag.model})">
        <span class="dot"></span>
        <span>${ag.name}</span>
      </div>
    `).join("");
  }

  // Render Suggested Prompts
  const promptsGrid = document.getElementById("suggestedPromptsGrid");
  if (promptsGrid) {
    promptsGrid.innerHTML = data.prompts.map(promptText => `
      <div class="prompt-chip" onclick="insertPrompt(${JSON.stringify(promptText)})">
        <span class="prompt-icon">↳</span>
        <span>${promptText}</span>
      </div>
    `).join("");
  }

  // Render Role-Specific Toolkit Cards
  const toolkitGrid = document.getElementById("roleToolkitGrid");
  if (toolkitGrid) {
    toolkitGrid.innerHTML = data.toolkit.map(item => `
      <div class="toolkit-card" onclick="insertAndExecute(${JSON.stringify(item.prompt)})">
        <div class="toolkit-icon-row">
          <div class="toolkit-icon-badge">⚡</div>
          <span class="challenge-tag">Auto-Harness</span>
        </div>
        <h4>${item.title}</h4>
        <p>${item.desc}</p>
        <span class="toolkit-action">Deploy Agent Blueprint →</span>
      </div>
    `).join("");
  }

  // Update Placeholder in Chatbox
  const chatInput = document.getElementById("chatInput");
  if (chatInput) {
    chatInput.placeholder = `Tell your AI harness what you're trying to create in ${data.title}...`;
  }
}

// 4. Prompt Helpers
function insertPrompt(text) {
  const chatInput = document.getElementById("chatInput");
  if (chatInput) {
    chatInput.value = text;
    chatInput.focus();
  }
}

function insertAndExecute(text) {
  const chatInput = document.getElementById("chatInput");
  if (chatInput) {
    chatInput.value = text;
    submitTask();
  }
}

function clearPromptInput() {
  const chatInput = document.getElementById("chatInput");
  if (chatInput) {
    chatInput.value = "";
    chatInput.focus();
  }
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

  const userInput = chatInput ? chatInput.value.trim() : "";
  if (!userInput) return;

  // Visual Loading State
  if (sendBtn) sendBtn.disabled = true;
  if (outputDiv) {
    outputDiv.classList.remove("empty-state");
    outputDiv.textContent = "AI Creative Harness orchestrating agents...\nAnalyzing intent and formulating domain-specific execution plan...";
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
      role: currentRole || null
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
