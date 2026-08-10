document.addEventListener("DOMContentLoaded", () => {
  if (AdminApp.isAuthenticated()) {
    window.location.href = "/admin";
    return;
  }

  document.querySelector("#login-form").addEventListener("submit", login);
});

async function login(event) {
  event.preventDefault();

  const loginButton = document.querySelector("#login-button");
  const payload = {
    email: document.querySelector("#login-email").value.trim(),
    password: document.querySelector("#login-password").value,
  };

  AdminApp.clearAlert("#login-alert");
  AdminApp.setButtonLoading(loginButton, true, "Logging in...");

  try {
    const response = await AdminApp.apiRequest("/auth/login", {
      method: "POST",
      body: payload,
    });

    AdminApp.saveAuthSession(response.access_token, response.user);

    const params = new URLSearchParams(window.location.search);
    const next = params.get("next");
    window.location.href = next && next.startsWith("/admin") ? next : "/admin";
  } catch (error) {
    AdminApp.showAlert("#login-alert", error.message, "danger");
  } finally {
    AdminApp.setButtonLoading(loginButton, false);
  }
}
