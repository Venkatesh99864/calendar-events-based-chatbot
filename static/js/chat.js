let conversationState = null;

const chatWindow = document.getElementById("chat-window");
const form = document.getElementById("chat-form");
const input = document.getElementById("user-input");

let typingElement = null;

/* Add message */
function addMessage(text, sender) {
  const div = document.createElement("div");
  div.classList.add("message", sender);

  // Preserve line breaks from backend
  div.innerHTML = text.replace(/\n/g, "<br>");

  chatWindow.appendChild(div);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

/* Show typing */
function showTyping() {
  if (typingElement) return;

  typingElement = document.createElement("div");
  typingElement.className = "message bot typing";
  typingElement.innerHTML =
    "typing" +
    '<span class="typing-dots">' +
    '<span class="typing-dot"></span>' +
    '<span class="typing-dot"></span>' +
    '<span class="typing-dot"></span>' +
    "</span>";

  chatWindow.appendChild(typingElement);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

/* Hide typing */
function hideTyping() {
  if (typingElement) {
    typingElement.remove();
    typingElement = null;
  }
}

/* Send message */
async function sendMessage(message) {
  const payload = {
    message,
    conversation_state: conversationState
  };

  showTyping();

  try {
    const res = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    hideTyping();

    conversationState = data.state;
    addMessage(data.reply, "bot");

  } catch (err) {
    hideTyping();
    addMessage("Sorry, there was an error contacting the server.", "bot");
  }
}

/* Form submit */
form.addEventListener("submit", (e) => {
  e.preventDefault();

  const text = input.value.trim();
  if (!text) return;

  addMessage(text, "user");
  input.value = "";
  sendMessage(text);
});

/* Initial greeting */
addMessage(
  "Namasthe 👋\nI am Madhav's assistant.\nHow can I help you?",
  "bot"
);
