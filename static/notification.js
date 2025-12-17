document.addEventListener("DOMContentLoaded", function () {
  const toggleBtn = document.getElementById("notificationToggleButton");
  const notifWin  = document.getElementById("notificationWindow");
  const closeBtn  = document.getElementById("closeNotifButton");
  const notifBody = document.getElementById("notificationBody");
  const badge     = document.getElementById("notifBadge");

  if (!toggleBtn || !notifWin || !notifBody) return;

 
  toggleBtn.addEventListener("click", function () {
    const isOpen = notifWin.classList.toggle("show");
    if (isOpen) loadNotifications();
  });

  if (closeBtn) {
    closeBtn.addEventListener("click", function () {
      notifWin.classList.remove("show");
    });
  }

  
  function loadNotifications() {
    fetch("/api/notifications")
      .then(res => res.json())
      .then(data => {
        notifBody.innerHTML = "";

        if (!data.notifications || data.notifications.length === 0) {
          notifBody.innerHTML =
            `<div class="notif-message">No notifications</div>`;
          return;
        }

        data.notifications.forEach(n => {
          const div = document.createElement("div");
          div.className = "notif-message";
          if (!n.is_read) div.classList.add("unread");

          div.innerHTML = `
            <div class="notif-title">${n.title || "Notification"}</div>
            <div class="notif-text">${n.body || ""}</div>
            <div class="notif-time">${n.created_at}</div>
            <button class="notif-delete">✕</button>
          `;

          div.addEventListener("click", () => {
            fetch(`/api/notifications/mark_read/${n.id}`, { method: "POST" })
              .then(() => {
                loadNotifBadge();
                if (n.link) window.location.href = n.link;
              });
          });

          div.querySelector(".notif-delete").addEventListener("click", e => {
            e.stopPropagation();
            fetch(`/api/notifications/delete/${n.id}`, { method: "POST" })
              .then(() => {
                div.remove();
                loadNotifBadge();
              });
          });

          notifBody.appendChild(div);
        });
      })
      .catch(() => {
        notifBody.innerHTML =
          `<div class="notif-message">Failed to load notifications</div>`;
      });
  }

 
  function loadNotifBadge() {
    fetch("/api/notifications/unread_count")
      .then(res => res.json())
      .then(data => {
        if (!badge) return;

        if (data.count > 0) {
          badge.style.display = "inline-block";
          badge.textContent = "!";
        } else {
          badge.style.display = "none";
        }
      });
  }

  loadNotifBadge();
});
