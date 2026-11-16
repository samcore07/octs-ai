/**
 * Octs AI - Agents Controller
 * Manages category filtering, agent deployments, and live persona analytics.
 */

document.addEventListener("DOMContentLoaded", () => {
  initFilterPills();
  highlightCurrentRoleAgents();
  loadAgentAnalytics();
});

function initFilterPills() {
  const pills = document.querySelectorAll(".filter-pill");
  const cards = document.querySelectorAll(".agent-roster-card");

  pills.forEach(pill => {
    pill.addEventListener("click", () => {
      pills.forEach(p => p.classList.remove("active"));
      pill.classList.add("active");

      const filterCategory = pill.getAttribute("data-category");

      cards.forEach(card => {
        const cardCategory = card.getAttribute("data-category");
        if (filterCategory === "all" || cardCategory === filterCategory) {
          card.style.display = "flex";
        } else {
          card.style.display = "none";
        }
      });
    });
  });
}

function highlightCurrentRoleAgents() {
  const savedRole = localStorage.getItem("octs_ai_role") || localStorage.getItem("generative_clash_role");
  if (!savedRole) return;

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

function deployAgent(agentName, promptTemplate) {
  sessionStorage.setItem("harness_auto_prompt", promptTemplate);
  window.location.href = "../index.html";
}

window.deployAgent = deployAgent;
