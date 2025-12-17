let activeItemType = null;
let activeItemId = null;

function openChat(itemType, itemId, title = "Chat") {
    activeItemType = itemType;
    activeItemId = itemId;

    document.getElementById("chatHeaderTitle").innerText = title;
    document.getElementById("globalChatWindow").classList.remove("hidden");

    loadChatMessages();
}

function loadChatMessages() {
    if (!activeItemId) return;

    fetch(`/api/chat/messages/${activeItemType}/${activeItemId}`)
        .then(res => res.json())
        .then(data => {
            const body = document.getElementById("globalChatBody");
            body.innerHTML = "";

            data.messages.forEach(msg => {
                const wrap = document.createElement("div");
                wrap.classList.add("chat-message");
                wrap.classList.add(msg.from_me ? "chat-me" : "chat-other");

                wrap.innerHTML = `
                    <div class="chat-meta">
                        ${msg.sender_name} (${msg.sender_id_number}) • ${msg.created_at}
                    </div>
                    ${msg.text || ""}
                    ${msg.image_url ? `<img src="${msg.image_url}" class="chat-image">` : ""}
                `;

                body.appendChild(wrap);
            });

            body.scrollTop = body.scrollHeight;
        });
}

document.getElementById("globalChatSend").addEventListener("click", () => {
    const text = document.getElementById("globalChatInput").value.trim();
    const image = document.getElementById("globalChatImage").files[0];

    const fd = new FormData();
    fd.append("item_type", activeItemType);
    fd.append("item_id", activeItemId);
    fd.append("message", text);
    if (image) fd.append("image", image);

    fetch("/api/chat/send", { method: "POST", body: fd })
        .then(res => res.json())
        .then(() => {
            document.getElementById("globalChatInput").value = "";
            document.getElementById("globalChatImage").value = "";
            loadChatMessages();
        });
});

document.getElementById("globalChatImageBtn").addEventListener("click", () =>
    document.getElementById("globalChatImage").click()
);

document.getElementById("globalCloseChat").addEventListener("click", () =>
    document.getElementById("globalChatWindow").classList.add("hidden")
);
