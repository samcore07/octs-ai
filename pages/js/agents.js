/**
 * Octs AI - Agents Controller
 * Manages discipline cohort activation, active vs standby status, and live persona analytics.
 * In OCTS AI, agents are NOT manually deployed individually; choosing a mode activates
 * its 4 specialized cohort agents, leaving other discipline agents on standby.
 */

const DISCIPLINE_NAMES = {
  writers: "Writers & Storytellers",
  musicians: "Musicians & Singers",
  creators: "Content Creators",
  designers: "Visual Artists & Designers",
};

document.addEventListener("DOMContentLoaded", () => {
  initFilterPills();
  restoreActiveCohortMode();
  loadAgentAnalytics();
});

function initFilterPills() {
  const pills = document.querySelectorAll(".filter-pill");
  const cards = document.querySelectorAll(".agent-roster-card");

  pills.forEach(pill => {
    pill.addEventListener("click", () => {
      pills.forEach(p => p.classList.remove("active"));
      pill.classList.add("active");

      const category = pill.getAttribute("data-category");

      if (category !== "all") {
        setActiveCohort(category);
      }

      cards.forEach(card => {
        const cardCategory = card.getAttribute("data-category");
        if (category === "all" || cardCategory === category) {
          card.style.display = "flex";
        } else {
          card.style.display = "none";
        }
      });
    });
  });
}

function setActiveCohort(discipline) {
  if (!discipline || discipline === "all") return;

  // Persist active discipline
  localStorage.setItem("octs_ai_role", discipline);
  localStorage.setItem("generative_clash_role", discipline);

  // Update banner text
  const titleEl = document.getElementById("activeModeTitle");
  const subtextEl = document.getElementById("activeModeSubtext");
  const niceName = DISCIPLINE_NAMES[discipline] || discipline;

  if (titleEl) titleEl.textContent = niceName;
  if (subtextEl) subtextEl.textContent = `(4 Cohort Agents Active & Ready • Other 12 Agents on Standby)`;

  // Update card statuses across the grid
  document.querySelectorAll(".agent-roster-card").forEach(card => {
    const cardCategory = card.getAttribute("data-category");
    const statusIndicator = card.querySelector(".agent-status-indicator");
    const cohortTag = card.querySelector(".cohort-status-tag");

    if (cardCategory === discipline) {
      if (statusIndicator) {
        statusIndicator.className = "agent-status-indicator";
        statusIndicator.textContent = "● Active";
      }
      if (cohortTag) {
        cohortTag.className = "cohort-status-tag active";
        cohortTag.textContent = "Cohort Active";
      }
    } else {
      if (statusIndicator) {
        statusIndicator.className = "agent-status-indicator standby";
        statusIndicator.textContent = "● Standby";
      }
      if (cohortTag) {
        cohortTag.className = "cohort-status-tag standby";
        cohortTag.textContent = "Standby";
      }
    }
  });
}

function restoreActiveCohortMode() {
  const savedRole = localStorage.getItem("octs_ai_role") || localStorage.getItem("generative_clash_role") || "writers";
  setActiveCohort(savedRole);

  const matchingPill = document.querySelector(`.filter-pill[data-category="${savedRole}"]`);
  if (matchingPill) {
    matchingPill.click();
  }
}

async function loadAgentAnalytics() {
  try {
    const res = await fetch("/api/analytics/personas");
    if (!res.ok) return;
    const personas = await res.json();
    if (!Array.isArray(personas)) return;

    const personaMap = {};
    personas.forEach(p => {
      personaMap[p.persona_id] = p;
    });

    document.querySelectorAll(".agent-roster-card").forEach(card => {
      const title = card.querySelector("h3") ? card.querySelector("h3").textContent.trim() : "";
      const personaKey = title.toLowerCase().replace(/[^a-z0-9]+/g, "_");

      const data = personaMap[personaKey];
      if (data && data.request_count > 0) {
        const metaSpan = card.querySelector(".agent-meta-row span");
        if (metaSpan) {
          metaSpan.textContent = `Handled: ${data.request_count} tasks • ${Math.round(data.avg_latency_ms)}ms`;
        }
      }
    });
  } catch (e) {
    console.debug("Agent analytics load error:", e);
  }
}
