document.addEventListener("DOMContentLoaded", () => {
  /* =========================
     ELEMENTS
  ========================= */
  const body = document.getElementById("chatBody");
  const input = document.getElementById("chatInput");
  const sendBtn = document.getElementById("chatSendButton");
  const imageBtn = document.getElementById("chatImageButton");
  const imageInput = document.getElementById("chatImageInput");

  const previewBox = document.getElementById("chatImagePreview");
  const previewImg = document.getElementById("chatPreviewImg");
  const removePreviewBtn = document.getElementById("removePreview");

  if (!body || !input || !sendBtn) {
    console.warn("❌ Chat elements missing");
    return;
  }

  const ITEM_ID = body.dataset.itemId;
  const ITEM_TYPE = body.dataset.itemType;

  if (!ITEM_ID || !ITEM_TYPE) {
    console.warn("❌ Missing item data attributes");
    return;
  }

  /* =========================
     IMAGE PICKER
  ========================= */
  if (imageBtn && imageInput) {
    imageBtn.addEventListener("click", () => imageInput.click());
  }

  imageInput.addEventListener("change", () => {
    const file = imageInput.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = e => {
      previewImg.src = e.target.result;
      previewBox.style.display = "flex";
    };
    reader.readAsDataURL(file);
  });

  removePreviewBtn?.addEventListener("click", () => {
    imageInput.value = "";
    previewImg.src = "";
    previewBox.style.display = "none";
  });

  /* =========================
     SEND MESSAGE
  ========================= */
  sendBtn.addEventListener("click", sendMessage);

  input.addEventListener("keydown", e => {
    if (e.key === "Enter") {
      e.preventDefault();
      sendMessage();
    }
  });

  function sendMessage() {
    const text = input.value.trim();
    const file = imageInput.files[0];

    if (!text && !file) return;

    const formData = new FormData();
    formData.append("item_id", ITEM_ID);
    formData.append("item_type", ITEM_TYPE);
    formData.append("message", text);
    if (file) formData.append("image", file);

    fetch("/api/chat/send", {
      method: "POST",
      body: formData
    })
      .then(res => res.json())
      .then(() => {
        input.value = "";
        imageInput.value = "";
        previewImg.src = "";
        previewBox.style.display = "none";
        loadMessages();
      })
      .catch(err => console.error("Send failed", err));
  }

  /* =========================
     LOAD MESSAGES
  ========================= */
  function loadMessages() {
    fetch(`/api/chat/messages/${ITEM_TYPE}/${ITEM_ID}`)
      .then(res => res.json())
      .then(data => {
        body.innerHTML = "";

        data.messages.forEach(m => {
          const div = document.createElement("div");
          div.className = "chat-msg";

          div.innerHTML = `
  <strong>${m.sender_name || "Unknown"}</strong>
  <small>${m.created_at}</small>

  ${m.message ? `<p>${m.message}</p>` : ""}

  ${
    m.image_url
      ? `<img src="${m.image_url}" class="chat-image">`
      : ""
  }

  ${
    m.can_delete
      ? `<button class="delete-msg" data-id="${m.id}">×</button>`
      : ""
  }
`;


          body.appendChild(div);
        });

        body.scrollTop = body.scrollHeight;
      })
      .catch(err => console.error("Load messages failed", err));
  }

  /* =========================
     DELETE MESSAGE
  ========================= */
  body.addEventListener("click", e => {
    if (!e.target.classList.contains("delete-msg")) return;

    fetch(`/api/chat/delete/${e.target.dataset.id}`, {
      method: "POST"
    })
      .then(() => loadMessages())
      .catch(err => console.error("Delete failed", err));
  });

  /* =========================
     INIT
  ========================= */
  loadMessages();
});
