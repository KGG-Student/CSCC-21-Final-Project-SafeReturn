document.addEventListener("DOMContentLoaded", () => {

  const backBtn = document.getElementById("homeBackButton");
  const logoutModal = document.getElementById("logoutModal");

  if (!backBtn || !logoutModal) return;

  backBtn.onclick = () => {
    logoutModal.classList.add("show");
  };

  document.getElementById("cancelLogout").onclick = () => {
    logoutModal.classList.remove("show");
  };

  document.getElementById("confirmLogout").onclick = () => {
    window.location.href = "/login";
  };
});
