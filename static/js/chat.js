const chatForm = document.getElementById("chatForm");
const chatWindow = document.getElementById("chatWindow");
const messageInput = document.getElementById("messageInput");
const sendBtn = document.getElementById("sendBtn");
const clearBtn = document.getElementById("clearBtn");

const modeSelect = document.getElementById("modeSelect");
const providerSelect = document.getElementById("providerSelect");
const backendSelect = document.getElementById("backendSelect");
const maxStepsInput = document.getElementById("maxStepsInput");
const modelInput = document.getElementById("modelInput");
const reasoningModal = document.getElementById("reasoningModal");
const closeReasoningBtn = document.getElementById("closeReasoningBtn");
const reasoningContent = document.getElementById("reasoningContent");

function appendMessage(text, role = "assistant") {
  const div = document.createElement("div");
  div.className = `message ${role}`;
  div.textContent = text;
  chatWindow.appendChild(div);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

function appendMeta(text) {
  appendMessage(text, "meta");
}

function formatReasoning(reasoning) {
  if (!Array.isArray(reasoning) || reasoning.length === 0) {
    return "No loop reasoning available for this response.";
  }

  return reasoning
    .map((item, index) => {
      const lines = [];
      lines.push(`Loop ${item.step ?? index + 1}`);
      if (item.status) {
        lines.push(`status: ${item.status}`);
      }
      if (item.llm_output) {
        lines.push(`llm_output:\n${item.llm_output}`);
      }
      if (item.tool) {
        lines.push(`tool: ${item.tool}`);
      }
      if (item.args !== undefined) {
        lines.push(`args: ${JSON.stringify(item.args, null, 2)}`);
      }
      if (item.observation) {
        lines.push(`observation:\n${item.observation}`);
      }
      if (item.parse_error) {
        lines.push(`parse_error: ${item.parse_error}`);
      }
      if (item.final_answer) {
        lines.push(`final_answer: ${item.final_answer}`);
      }
      return lines.join("\n");
    })
    .join("\n\n------------------------------\n\n");
}

function showReasoning(reasoning) {
  reasoningContent.textContent = formatReasoning(reasoning);
  reasoningModal.classList.remove("hidden");
}

function hideReasoning() {
  reasoningModal.classList.add("hidden");
}

function appendAssistantWithReasoning(answer, reasoning) {
  const wrap = document.createElement("div");
  wrap.className = "assistant-wrap";

  const message = document.createElement("div");
  message.className = "message assistant";
  message.textContent = answer || "(empty response)";
  wrap.appendChild(message);

  chatWindow.appendChild(wrap);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

appendMeta("Connected. Ask about products, coupons, shipping, or total cost.");

clearBtn.addEventListener("click", () => {
  chatWindow.innerHTML = "";
  appendMeta("Chat cleared.");
});

closeReasoningBtn.addEventListener("click", hideReasoning);
reasoningModal.addEventListener("click", (event) => {
  if (event.target === reasoningModal) {
    hideReasoning();
  }
});

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const message = messageInput.value.trim();
  if (!message) {
    return;
  }

  appendMessage(message, "user");
  messageInput.value = "";

  const payload = {
    message,
    mode: modeSelect.value,
    provider: providerSelect.value,
    backend: backendSelect.value,
    max_steps: Number(maxStepsInput.value || 6),
    model: modelInput.value.trim(),
  };

  sendBtn.disabled = true;
  sendBtn.textContent = "Sending...";

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || "Request failed");
    }

    const data = await response.json();
    appendAssistantWithReasoning(data.answer, data.reasoning || []);
  } catch (error) {
    appendMessage(`Error: ${error.message}`, "assistant");
  } finally {
    sendBtn.disabled = false;
    sendBtn.textContent = "Send";
    messageInput.focus();
  }
});
