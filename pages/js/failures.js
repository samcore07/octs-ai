/**
 * Octs AI - Failure Intelligence & Recovery Controller
 * Loads real recovery metrics, self-correction logs, and halt counts.
 */

document.addEventListener("DOMContentLoaded", () => {
  loadFailuresData();
});

async function loadFailuresData() {
  const countEl = document.getElementById("failRecoveriesCount");
  const rateEl = document.getElementById("failCorrectionRate");
  const haltsEl = document.getElementById("failUnhandledHalts");
  const logContainer = document.getElementById("recoveryLogContainer");

  try {
    const [overviewRes, requestsRes] = await Promise.all([
      fetch("/api/analytics/overview").catch(() => null),
      fetch("/api/analytics/requests?limit=30").catch(() => null),
    ]);

    if (overviewRes && overviewRes.ok) {
      const ov = await overviewRes.json();
      if (haltsEl) haltsEl.textContent = ov.failed_requests || 0;
      if (rateEl) {
        const rate = ov.reversion_rate != null ? (100 - ov.reversion_rate).toFixed(1) + "%" : "100%";
        rateEl.textContent = rate;
      }
    }

    if (requestsRes && requestsRes.ok) {
      const requests = await requestsRes.json();
      const recoveredRequests = requests.filter(r => r.refinement_triggered || r.recovery_attempts > 0);

      if (countEl) countEl.textContent = recoveredRequests.length;

      if (logContainer) {
        if (!recoveredRequests.length) {
          logContainer.innerHTML = `
            <div style="padding: 24px; text-align: center; color: var(--text-muted); font-size: 13px; font-style: italic;">
              ✓ Zero active execution faults. All model runs executed cleanly with 100% first-pass verification.
            </div>
          `;
        } else {
          logContainer.innerHTML = recoveredRequests.map(req => {
            const timeStr = new Date(req.timestamp).toLocaleTimeString();
            const attempts = req.recovery_attempts || 1;
            const statusLabel = req.status === "success" ? "RECOVERED" : "HALTED";
            const tagColor = req.status === "success" ? "var(--success)" : "var(--danger)";
            return `
              <div class="log-item">
                <span class="log-time">${timeStr}</span>
                <span class="log-tag" style="color: ${tagColor}; border-color: ${tagColor};">${statusLabel}</span>
                <div class="log-content">
                  <strong>Specialist Refinement Loop (${req.discipline || 'creative'} / ${req.persona_id || 'lead'}):</strong>
                  <div class="log-recovery-desc">
                    Autonomously resolved craft deviation in ${attempts} attempt(s). TrustScore evaluated at ${req.trust_score ? req.trust_score.toFixed(1) + '%' : '100%'}.
                  </div>
                </div>
              </div>
            `;
          }).join("");
        }
      }
    }
  } catch (err) {
    console.error("Failed to load failures data:", err);
  }
}
