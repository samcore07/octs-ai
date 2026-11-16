/**
 * Octs AI - Success Rate & Verification Controller
 * Loads real TrustScore, quality scores, and verification benchmarks.
 */

document.addEventListener("DOMContentLoaded", () => {
  loadSuccessData();
});

async function loadSuccessData() {
  const trustScoreEl = document.getElementById("succTrustScore");
  const qualityScoreEl = document.getElementById("succQualityScore");
  const reliabilityScoreEl = document.getElementById("succReliabilityScore");
  const acceptanceRateEl = document.getElementById("succAcceptanceRate");
  const trustSubnoteEl = document.getElementById("succTrustSubnote");
  const refineSubnoteEl = document.getElementById("succRefineSubnote");

  try {
    const res = await fetch("/api/analytics/overview");
    if (res.ok) {
      const ov = await res.json();

      if (trustScoreEl) {
        trustScoreEl.textContent = ov.avg_trust_score != null ? `${ov.avg_trust_score.toFixed(1)}%` : "100%";
      }
      if (qualityScoreEl) {
        const q = ov.avg_quality_score != null ? Math.round(ov.avg_quality_score) : 95;
        qualityScoreEl.innerHTML = `${q}<span style="font-size: 14px; color: var(--text-muted);">/100</span>`;
      }
      if (reliabilityScoreEl) {
        reliabilityScoreEl.textContent = ov.avg_reliability_score != null ? `${ov.avg_reliability_score.toFixed(1)}%` : "100%";
      }
      if (acceptanceRateEl) {
        const acceptRate = ov.refinement_rate != null ? (100 - ov.refinement_rate).toFixed(1) + "%" : "100%";
        acceptanceRateEl.textContent = acceptRate;
      }
      if (refineSubnoteEl && ov.refinement_rate != null) {
        refineSubnoteEl.textContent = `${ov.refinement_rate.toFixed(1)}% autonomously refined`;
      }
      if (trustSubnoteEl && ov.total_requests) {
        trustSubnoteEl.textContent = `Calculated over ${ov.total_requests} requests`;
      }
    }
  } catch (err) {
    console.error("Failed to load success analytics:", err);
  }
}
