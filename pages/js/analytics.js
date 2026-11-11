/* Analytics page: adds accessible descriptions to the demo charts. */
document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".bar-chart").forEach((chart) => {
        chart.setAttribute("role", "img");
        chart.setAttribute("aria-label", "Illustrative weekly workflow activity bar chart");
    });

    const trend = document.querySelector(".line-chart");
    if (trend) {
        trend.setAttribute("role", "img");
        trend.setAttribute("aria-label", "Illustrative performance trend line chart");
    }
});
