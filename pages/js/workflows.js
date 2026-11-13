/**
 * Generative Clash - Workflows Controller
 */

function runWorkflow(workflowName, initialPrompt) {
  sessionStorage.setItem("harness_auto_prompt", initialPrompt);
  window.location.href = "../index.html";
}

window.runWorkflow = runWorkflow;
