document.addEventListener("DOMContentLoaded", function () {
  const chatToggleButton = document.getElementById("chatToggleButton");
  const chatSenderButton = document.getElementById("chatSenderButton");
  const chatWindow       = document.getElementById("chatWindow");
  const closeChatButton  = document.getElementById("closeChatButton");
  const chatBody         = document.getElementById("chatBody");
  const chatInput        = document.getElementById("chatInput");
  const chatSendButton   = document.getElementById("chatSendButton");
  const chatImageButton  = document.getElementById("chatImageButton");
  const chatImageInput   = document.getElementById("chatImageInput");

  const body     = document.body;
  const itemType = body.dataset.itemType;
  const itemId   = body.dataset.itemId;

  function openChat() {
    chatWindow.style.display = "block";
    loadChat();
    markChatRead();
  }

  function closeChat() {
    chatWindow.style.display = "none";
  }

  chatToggleButton?.addEventListener("click", () => {
    chatWindow.style.display === "block" ? closeChat() : openChat();
  });

  chatSenderButton?.addEventListener("click", openChat);
  closeChatButton?.addEventListener("click", closeChat);

  chatImageButton?.addEventListener("click", () => chatImageInput.click());

  chatSendButton?.addEventListener("click", sendMessage);
  chatInput?.addEventListener("keydown", e => {
    if (e.key === "Enter") {
      e.preventDefault();
      sendMessage();
    }
  });

  function loadChat() {
    fetch(`/api/chat/messages/${itemType}/${itemId}`)
      .then(res => res.json())
      .then(data => {
        chatBody.innerHTML = "";

        data.messages.forEach(msg => {
          const div = document.createElement("div");
          div.className = "chat-message " + (msg.from_me ? "from-me" : "from-them");

          div.innerHTML = `
            <div class="chat-meta">
              ${msg.sender_name} (${msg.sender_id_number}) • ${msg.created_at}
              ${msg.from_me ? `<button class="chat-delete" data-id="${msg.id}">✖</button>` : ""}
            </div>
            ${msg.text ? `<div class="chat-text">${msg.text}</div>` : ""}
            ${msg.image_url ? `<img class="chat-image" src="${msg.image_url}">` : ""}
          `;

          chatBody.appendChild(div);
        });

        chatBody.scrollTop = chatBody.scrollHeight;

        // attach delete handlers
        document.querySelectorAll(".chat-delete").forEach(btn => {
          btn.addEventListener("click", () => deleteMessage(btn.dataset.id));
        });
      });
  }

  function sendMessage() {
    const text = chatInput.value.trim();
    const file = chatImageInput.files[0];
    if (!text && !file) return;

    const formData = new FormData();
    formData.append("item_type", itemType);
    formData.append("item_id", itemId);
    formData.append("message", text);
    if (file) formData.append("image", file);

    fetch("/api/chat/send", { method: "POST", body: formData })
      .then(res => res.json())
      .then(data => {
        if (data.status === "ok") {
          chatInput.value = "";
          chatImageInput.value = "";
          loadChat();
        }
      });
  }

  function deleteMessage(messageId) {
    if (!confirm("Delete this message?")) return;

    fetch(`/api/chat/delete/${messageId}`, { method: "POST" })
      .then(() => loadChat());
  }

  function markChatRead() {
    fetch(`/api/chat/mark_read/${itemType}/${itemId}`, { method: "POST" });
  }
});
