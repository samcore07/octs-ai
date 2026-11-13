/**
 * Generative Clash - Agents Controller
 */

document.addEventListener("DOMContentLoaded", () => {
  initFilterPills();
  highlightCurrentRoleAgents();
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
  const savedRole = localStorage.getItem("generative_clash_role");
  if (!savedRole) return;

  const matchingPill = document.querySelector(`.filter-pill[data-category="${savedRole}"]`);
  if (matchingPill) {
    matchingPill.click();
  }
}

function deployAgent(agentName, promptTemplate) {
  sessionStorage.setItem("harness_auto_prompt", promptTemplate);
  window.location.href = "../index.html";
}

window.deployAgent = deployAgent;
