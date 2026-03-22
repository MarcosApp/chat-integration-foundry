const messages = document.getElementById("messages");
const form = document.getElementById("chatForm");
const input = document.getElementById("messageInput");
const sendButton = document.getElementById("sendButton");
const resetButton = document.getElementById("resetButton");
const { assistantLabel, userLabel, pendingMessage, showWelcome, welcome } =
  window.chatConfig;

function appendMessage(role, text) {
  const article = document.createElement("article");
  article.className = `message ${role}`;

  const meta = document.createElement("div");
  meta.className = "message-meta";
  meta.textContent = role === "user" ? userLabel : assistantLabel;

  const bubble = document.createElement("div");
  bubble.className = "message-bubble";
  bubble.textContent = text;

  article.append(meta, bubble);
  messages.appendChild(article);
  messages.scrollTop = messages.scrollHeight;
}

function appendMessages(role, items) {
  items.forEach((text) => appendMessage(role, text));
}

function autosize() {
  input.style.height = "auto";
  input.style.height = `${Math.min(input.scrollHeight, 180)}px`;
}

async function submitMessage(message) {
  appendMessage("user", message);
  const typing = appendMessage("assistant", pendingMessage);
  sendButton.disabled = true;
  input.disabled = true;

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Falha ao enviar mensagem.");
    }

    messages.lastElementChild?.remove();
    const replies = Array.isArray(data.replies) ? data.replies : [];
    if (replies.length > 0) {
      appendMessages("assistant", replies);
    } else {
      appendMessage("assistant", data.reply || "");
    }
  } catch (error) {
    const currentTyping = messages.lastElementChild?.querySelector(".message-bubble");
    if (currentTyping) {
      currentTyping.textContent = error.message;
    }
  } finally {
    sendButton.disabled = false;
    input.disabled = false;
    input.focus();
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = input.value.trim();
  if (!message) {
    return;
  }

  input.value = "";
  autosize();
  await submitMessage(message);
});

input.addEventListener("input", autosize);

input.addEventListener("keydown", async (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});

resetButton.addEventListener("click", async () => {
  await fetch("/api/reset", { method: "POST" });
  messages.innerHTML = "";
  if (showWelcome && welcome) {
    appendMessage("assistant", welcome);
  }
  input.focus();
});
