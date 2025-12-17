document.addEventListener("DOMContentLoaded", () => {

  const buttons = document.querySelectorAll(".nav-btn");
  const tabs = document.querySelectorAll(".tab-content");

  let deleteTarget = null;
  let claimTarget = null;

  let logPage = 1;
  let totalLogPages = 1;

  let currentChat = null;

  
  buttons.forEach(btn => {
    btn.addEventListener("click", () => {
      buttons.forEach(b => b.classList.remove("active"));
      tabs.forEach(t => t.classList.remove("active"));

      btn.classList.add("active");
      document.getElementById(btn.dataset.tab).classList.add("active");

      if (btn.dataset.tab === "reportsTab") loadReports();
      if (btn.dataset.tab === "itemsTab") loadItems();
      if (btn.dataset.tab === "logsTab") loadLogs();
      if (btn.dataset.tab === "chatTab") loadAdminChats();
    });
  });

  function loadReports() {
    fetch("/admin/api/reports")
      .then(res => res.json())
      .then(data => {
        const body = document.getElementById("reportsTableBody");
        body.innerHTML = "";

        if (!data.reports || !data.reports.length) {
          body.innerHTML = `<tr><td colspan="5">No reports found</td></tr>`;
          return;
        }

        data.reports.forEach(r => {
          body.innerHTML += `
            <tr>
              <td>${r.type.toUpperCase()}</td>
              <td>${r.item_name}</td>
              <td>${r.location}</td>
              <td>${r.created_at}</td>
              <td>
                <a href="/item/${r.type}/${r.id}?from=admin" class="view-btn">View</a>
                ${r.status === "claimed" ? "" :
                  `<button class="claim-btn" data-id="${r.id}" data-type="${r.type}">Claim</button>`}
                <button class="delete-btn" data-id="${r.id}" data-type="${r.type}">Delete</button>
              </td>
            </tr>
          `;
        });
      });
  }

 
  function loadItems() {
    fetch("/admin/api/items")
      .then(res => res.json())
      .then(data => {
        const box = document.getElementById("itemsBox");
        box.innerHTML = "";

        if (!data.items || !data.items.length) {
          box.innerHTML = "<p>No archived items.</p>";
          return;
        }

        data.items.forEach(item => {
          box.innerHTML += `
            <div class="archive-row">
              <div class="archive-info">
                <strong>${item.item_name}</strong>
                <span class="archive-meta">${item.type.toUpperCase()} • ${item.location || "N/A"}</span>
              </div>

              <div class="archive-actions">
                <span class="archive-status ${item.status}">
                  ${item.status.toUpperCase()}
                </span>
                <a href="/item/${item.type}/${item.id}?from=admin" class="view-btn">View</a>
                <button class="reopen-btn" data-id="${item.id}" data-type="${item.type}">Reopen</button>
                <button class="perma-delete-btn" data-id="${item.id}" data-type="${item.type}">Delete</button>
              </div>
            </div>
          `;
        });
      });
  }


  function loadLogs() {
    const box = document.getElementById("logsBox");
    if (!box) return;

    box.innerHTML = "<p>Loading logs...</p>";

    const actor = document.getElementById("filterActor").value;
    const action = document.getElementById("filterAction").value;

    const params = new URLSearchParams({
      page: logPage,
      limit: 20
    });

    if (actor) params.append("actor", actor);
    if (action) params.append("action", action);

    fetch(`/admin/api/logs?${params.toString()}`)
      .then(res => res.json())
      .then(data => {
        box.innerHTML = "";
        totalLogPages = data.total_pages;

        if (!data.logs.length) {
          box.innerHTML = "<p>No logs found.</p>";
          return;
        }

        data.logs.forEach(log => {
          box.innerHTML += `
            <div class="log-row">
              <div class="log-header">
                <span class="log-action ${log.action}">
                  ${log.action.replaceAll("_", " ")}
                </span>
                <span class="log-actor ${log.actor.startsWith("user:") ? "user" : "admin"}">
                  ${log.actor.startsWith("user:") ? "USER" : "ADMIN"}
                </span>
                <span class="log-time">${log.created_at}</span>
              </div>
              <div class="log-description">${log.description}</div>
            </div>
          `;
        });

        document.getElementById("pageInfo").textContent =
          `Page ${logPage} of ${totalLogPages}`;
      });
  }

  document.getElementById("filterActor").onchange =
  document.getElementById("filterAction").onchange = () => {
    logPage = 1;
    loadLogs();
  };

  document.getElementById("prevPage").onclick = () => {
    if (logPage > 1) {
      logPage--;
      loadLogs();
    }
  };

  document.getElementById("nextPage").onclick = () => {
    if (logPage < totalLogPages) {
      logPage++;
      loadLogs();
    }
  };

  function loadAdminChats() {
    fetch("/admin/api/chats")
      .then(res => res.json())
      .then(data => {
        const list = document.getElementById("chatList");
        list.innerHTML = "";

        if (!data.chats.length) {
          list.textContent = "No conversations.";
          return;
        }

        data.chats.forEach(c => {
          const div = document.createElement("div");
          div.className = "chat-list-item";
          div.innerHTML = `
            <strong>User ${c.user_id}</strong>
            <small>${c.item_type.toUpperCase()} ITEM</small>
            <p>${c.last_message}</p>
            <span>${c.last_time}</span>
          `;
          div.onclick = () => openAdminChat(c);
          list.appendChild(div);
        });
      });
  }

  function openAdminChat(chat) {
    currentChat = chat;

    document.getElementById("chatHeader").textContent =
      `User ${chat.user_id} • ${chat.item_type.toUpperCase()} Item`;

    fetch(`/admin/api/chat/${chat.item_type}/${chat.item_id}/${chat.user_id}`)
      .then(res => res.json())
      .then(data => {
        const body = document.getElementById("chatBody");
        body.innerHTML = "";

        data.messages.forEach(m => {
          body.innerHTML += `
            <div class="chat-msg ${m.sender}">
              <span>${m.message}</span>
              <small>${m.created_at}</small>
            </div>
          `;
        });

        body.scrollTop = body.scrollHeight;
      });
  }

  document.getElementById("adminChatSend").onclick = () => {
    if (!currentChat) return;

    const input = document.getElementById("adminChatInput");
    const msg = input.value.trim();
    if (!msg) return;

    fetch("/admin/api/chat/send", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        item_id: currentChat.item_id,
        item_type: currentChat.item_type,
        user_id: currentChat.user_id,
        message: msg
      })
    }).then(() => {
      input.value = "";
      openAdminChat(currentChat);
    });
  };

 
  document.addEventListener("click", e => {

    const claimBtn = e.target.closest(".claim-btn");
    const deleteBtn = e.target.closest(".delete-btn");
    const reopenBtn = e.target.closest(".reopen-btn");
    const permaBtn  = e.target.closest(".perma-delete-btn");

    if (claimBtn) {
      claimTarget = claimBtn.dataset;
      document.getElementById("claimModal").classList.add("show");
    }

    if (deleteBtn) {
      deleteTarget = { ...deleteBtn.dataset, permanent: false };
      document.getElementById("confirmTitle").textContent = "Delete Report";
      document.getElementById("confirmText").textContent = "Delete this report?";
      document.getElementById("confirmModal").classList.add("show");
    }

    if (reopenBtn) {
      fetch(`/admin/api/item/reopen/${reopenBtn.dataset.type}/${reopenBtn.dataset.id}`, {
        method: "POST"
      }).then(loadItems);
    }

    if (permaBtn) {
      deleteTarget = { ...permaBtn.dataset, permanent: true };
      document.getElementById("confirmTitle").textContent = "Permanent Delete";
      document.getElementById("confirmText").textContent = "This cannot be undone.";
      document.getElementById("confirmModal").classList.add("show");
    }
  });

  document.getElementById("confirmClaim").onclick = () => {
    fetch(`/admin/api/report/claim/${claimTarget.type}/${claimTarget.id}`, {
      method: "POST"
    }).then(() => {
      document.getElementById("claimModal").classList.remove("show");
      loadReports();
    });
  };

  document.getElementById("confirmDelete").onclick = () => {
    const url = deleteTarget.permanent
      ? `/admin/api/item/permanent-delete/${deleteTarget.type}/${deleteTarget.id}`
      : `/admin/api/report/delete/${deleteTarget.type}/${deleteTarget.id}`;

    fetch(url, { method: "POST" })
      .then(() => {
        document.getElementById("confirmModal").classList.remove("show");
        loadReports();
        loadItems();
      });
  };

  document.getElementById("cancelDelete").onclick =
  document.getElementById("cancelClaim").onclick = () => {
    document.querySelectorAll(".delete-modal-overlay")
      .forEach(m => m.classList.remove("show"));
  };

  
  const backBtn = document.getElementById("backButton");
  const logoutModal = document.getElementById("logoutModal");

  if (backBtn && logoutModal) {
    backBtn.onclick = () => logoutModal.classList.add("show");

    document.getElementById("cancelLogout").onclick = () =>
      logoutModal.classList.remove("show");

    document.getElementById("confirmLogout").onclick = () =>
      window.location.href = "/login";
  }

  function renderMessage(msg) {
  const div = document.createElement("div");
  div.className = msg.sender_role === "admin"
    ? "chat-msg admin"
    : "chat-msg user";

  div.textContent = msg.message;
  return div;
}
  /* =======================
     INITIAL LOAD
  ======================= */
  loadReports();
});
