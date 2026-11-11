/* Agent page interactions. The switches currently control the UI only. */
document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".agent-card .toggle").forEach((toggle) => {
        toggle.addEventListener("change", () => {
            toggle.setAttribute("aria-checked", String(toggle.checked));
        });
        toggle.setAttribute("role", "switch");
        toggle.setAttribute("aria-checked", String(toggle.checked));
    });
});
