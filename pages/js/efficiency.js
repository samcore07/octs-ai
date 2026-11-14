/**
 * Octs AI - Efficiency Telemetry Controller
 */

document.addEventListener("DOMContentLoaded", () => {
  animateChartBars();
});

function animateChartBars() {
  const bars = document.querySelectorAll(".chart-bar");
  bars.forEach(bar => {
    const targetHeight = bar.style.height;
    bar.style.height = "0%";
    setTimeout(() => {
      bar.style.height = targetHeight;
    }, 100);
  });
}
