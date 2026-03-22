const statusEl = document.getElementById("status");
const chatWindow = document.getElementById("chat-window");
const form = document.getElementById("chat-form");
const input = document.getElementById("message");
const sendBtn = document.getElementById("send");
const newChatBtn = document.getElementById("new-chat");
const messageTemplate = document.getElementById("message-template");

let conversationId = "";
let streaming = false;

const HHMM = () => new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });

function autoGrow() {
  input.style.height = "auto";
  input.style.height = `${Math.min(input.scrollHeight, 160)}px`;
}

function setStatus(text) {
  statusEl.textContent = text;
}

function addBubble(author, text, isMine) {
  const node = messageTemplate.content.firstElementChild.cloneNode(true);
  node.classList.add(isMine ? "me" : "bot");
  node.querySelector(".bubble-meta").textContent = `${author} · ${HHMM()}`;
  node.querySelector(".bubble").textContent = text;
  chatWindow.appendChild(node);
  chatWindow.scrollTop = chatWindow.scrollHeight;
  return node.querySelector(".bubble");
}

async function createConversation() {
  setStatus("Abrindo conversa...");

  const res = await fetch("/api/conversations", { method: "POST" });
  if (!res.ok) {
    throw new Error("Falha ao criar conversa");
  }

  const data = await res.json();
  conversationId = data.conversation_id;
  localStorage.setItem("conviva_conversation_id", conversationId);
  setStatus("Online");
}

async function resetConversation() {
  const oldConversation = conversationId || localStorage.getItem("conviva_conversation_id");

  if (oldConversation) {
    await fetch(`/api/conversations/${oldConversation}`, { method: "DELETE" });
  }

  conversationId = "";
  localStorage.removeItem("conviva_conversation_id");
  chatWindow.innerHTML = "";
  await createConversation();
}

async function streamResponse(message, targetBubble) {
  const res = await fetch("/api/messages", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      conversation_id: conversationId,
      message,
    }),
  });

  if (!res.ok || !res.body) {
    throw new Error("Falha no stream da resposta");
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder("utf-8");

  while (true) {
    const { done, value } = await reader.read();
    if (done) {
      break;
    }

    targetBubble.textContent += decoder.decode(value, { stream: true });
    chatWindow.scrollTop = chatWindow.scrollHeight;
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (streaming) {
    return;
  }

  const message = input.value.trim();
  if (!message) {
    return;
  }

  if (!conversationId) {
    await createConversation();
  }

  addBubble("Você", message, true);
  input.value = "";
  autoGrow();

  streaming = true;
  sendBtn.disabled = true;
  setStatus("Conviva está digitando...");

  const botBubble = addBubble("Conviva", "", false);

  try {
    await streamResponse(message, botBubble);
    if (!botBubble.textContent.trim()) {
      botBubble.textContent = "(sem resposta textual)";
    }
    setStatus("Online");
  } catch (error) {
    botBubble.textContent = "Erro ao receber resposta.";
    setStatus("Erro na conexão");
  } finally {
    streaming = false;
    sendBtn.disabled = false;
    input.focus();
  }
});

newChatBtn.addEventListener("click", async () => {
  if (streaming) {
    return;
  }

  try {
    await resetConversation();
    addBubble("Sistema", "Nova conversa iniciada.", false);
  } catch (_error) {
    setStatus("Erro ao reiniciar conversa");
  }
});

input.addEventListener("input", autoGrow);
input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});

(async function init() {
  try {
    localStorage.removeItem("conviva_conversation_id");
    await createConversation();

    addBubble("Sistema", "Conversa pronta. Envie uma mensagem para testar o stream.", false);
    input.focus();
  } catch (_error) {
    setStatus("Falha ao conectar");
    addBubble("Sistema", "Não foi possível conectar ao backend.", false);
  }
})();
