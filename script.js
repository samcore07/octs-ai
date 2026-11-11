const promptInput = document.getElementById("promptInput");
const sendBtn = document.getElementById("sendBtn");
const outputDiv = document.getElementById("output");

async function sendMessage() {
  const question = promptInput.value.trim();
  if (!question) return;

  // Show loading state
  outputDiv.textContent = "Loading...";
  sendBtn.disabled = true;

  try {
    // Send the textbox text to your backend API
    const response = await fetch("/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt: question })
    });

    const data = await response.json();
    outputDiv.textContent = data.reply;
  } catch (error) {
    outputDiv.textContent = "Error: Could not connect to backend. (" + error.message + ")";
  } finally {
    sendBtn.disabled = false;
    promptInput.value = "";
  }
}

// Trigger on button click
sendBtn.addEventListener("click", sendMessage);

// Trigger when pressing Enter inside the textbox
promptInput.addEventListener("keypress", (event) => {
  if (event.key === "Enter") {
    sendMessage();
  }
});
