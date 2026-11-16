/**
 * Octs AI - Efficiency Telemetry Controller
 * Loads real operational latency, throughput, and system health benchmarks.
 */

document.addEventListener("DOMContentLoaded", () => {
  loadEfficiencyData();
});

async function loadEfficiencyData() {
  const avgLatencyEl = document.getElementById("effAvgLatency");
  const totalRequestsEl = document.getElementById("effTotalRequests");
  const successRateEl = document.getElementById("effSuccessRate");
  const healthScoreEl = document.getElementById("effHealthScore");
  const engineNameEl = document.getElementById("effEngineName");
  const latencySubnote = document.getElementById("effLatencySubnote");
  const volumeSubnote = document.getElementById("effVolumeSubnote");

  try {
    const [overviewRes, healthRes] = await Promise.all([
      fetch("/api/analytics/overview").catch(() => null),
      fetch("/api/health").catch(() => null),
    ]);

    if (overviewRes && overviewRes.ok) {
      const ov = await overviewRes.json();
      if (avgLatencyEl) {
        avgLatencyEl.textContent = ov.avg_latency_ms ? `${Math.round(ov.avg_latency_ms)}ms` : "--";
      }
      if (totalRequestsEl) {
        totalRequestsEl.textContent = ov.total_requests || 0;
      }
      if (volumeSubnote) {
        volumeSubnote.textContent = `${ov.successful_requests || 0} successful / ${ov.failed_requests || 0} failed`;
      }
      if (successRateEl) {
        const rate = ov.total_requests > 0
          ? ((ov.successful_requests / ov.total_requests) * 100).toFixed(1) + "%"
          : "100%";
        successRateEl.textContent = rate;
      }
      if (latencySubnote && ov.avg_latency_ms) {
        latencySubnote.textContent = ov.avg_latency_ms < 1000 ? "⚡ High-throughput execution" : "Standard model latency";
      }
    }

    if (healthRes && healthRes.ok) {
      const h = await healthRes.json();
      if (healthScoreEl) {
        healthScoreEl.textContent = h.status === "ok" ? "Operational" : "Degraded";
        healthScoreEl.style.color = h.status === "ok" ? "var(--success)" : "var(--warning)";
      }
      if (engineNameEl && h.model_name) {
        engineNameEl.textContent = `${h.model_name} API`;
      }
    }
  } catch (err) {
    console.error("Failed to load efficiency data:", err);
  }

  animateChartBars();
}

function animateChartBars() {
  const bars = document.querySelectorAll(".chart-bar");
  bars.forEach(bar => {
    const targetHeight = bar.style.height || "50%";
    bar.style.height = "0%";
    setTimeout(() => {
      bar.style.height = targetHeight;
    }, 120);
  });
}
