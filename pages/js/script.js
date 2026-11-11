// DOM Element IDs from index.html:
// - Chat box textarea: "chatInput"
// - Send button: "sendBtn"
// - Output display: "output"
// - Copy button: "copyBtn"

// 1. Copy Output Function
function copyResponse() {
  const outputEl = document.getElementById("output");
  const outputText = outputEl ? outputEl.innerText.trim() : "";
  
  if (!outputText || outputText === "Response will appear here...") {
    return;
  }

  navigator.clipboard.writeText(outputText).then(() => {
    const copyBtn = document.getElementById("copyBtn");
    if (!copyBtn) return;

    const originalContent = copyBtn.innerHTML;
    copyBtn.innerText = "Copied!";

    setTimeout(() => {
      copyBtn.innerHTML = originalContent;
    }, 2000);
  }).catch((err) => {
    console.error("Clipboard copy failed:", err);
  });
}

// 2. Submit Task / Chat to Backend
async function submitTask() {
  const chatInput = document.getElementById("chatInput") || document.getElementById("promptInput");
  const outputDiv = document.getElementById("output");
  const sendBtn = document.getElementById("sendBtn");

  const question = chatInput ? chatInput.value.trim() : "";
  if (!question) return;

  // Show loading indicator
  if (outputDiv) outputDiv.textContent = "Loading...";
  if (sendBtn) sendBtn.disabled = true;

  try {
    const response = await fetch("/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt: question })
    });

    if (!response.ok) {
      throw new Error(`Server returned ${response.status}`);
    }

    const data = await response.json();
    if (outputDiv) {
      outputDiv.textContent = data.reply;
    }
  } catch (error) {
    if (outputDiv) {
      outputDiv.textContent = "Error: Could not connect to backend. (" + error.message + ")";
    }
  } finally {
    if (sendBtn) sendBtn.disabled = false;
    if (chatInput) chatInput.value = "";
  }
}

// Keep sendMessage as an alias for backwards compatibility
const sendMessage = submitTask;

// Expose functions globally for inline onclick attributes
window.copyResponse = copyResponse;
window.submitTask = submitTask;
window.sendMessage = sendMessage;

// 3. Event Listeners initialization
document.addEventListener("DOMContentLoaded", () => {
  const chatInput = document.getElementById("chatInput") || document.getElementById("promptInput");
  const sendBtn = document.getElementById("sendBtn");

  if (sendBtn) {
    sendBtn.addEventListener("click", submitTask);
  }

  if (chatInput) {
    chatInput.addEventListener("keydown", (event) => {
      // Submit on Enter (without Shift)
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        submitTask();
      }
    });
  }
});
