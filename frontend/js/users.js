let users = [];
let currentUser = null;
let userModal;
let userViewModal;
let passwordResetModal;
let userPageData = null;
let userState = {
  page: 1,
  pageSize: 10,
  search: "",
  role: "",
  isActive: "",
};

document.addEventListener("DOMContentLoaded", () => {
  currentUser = AdminApp.getCurrentUser();
  userModal = new bootstrap.Modal(document.querySelector("#userModal"));
  userViewModal = new bootstrap.Modal(document.querySelector("#userViewModal"));
  passwordResetModal = new bootstrap.Modal(document.querySelector("#passwordResetModal"));

  if (currentUser?.role !== "admin") {
    document.querySelector("#open-add-user")?.classList.add("d-none");
    document.querySelector("#users-table-body").innerHTML = `
      <tr>
        <td colspan="7" class="text-center text-muted py-4">Admin access required.</td>
      </tr>
    `;
    AdminApp.showAlert("#users-alert", "Admin access required.", "danger");
    return;
  }

  document.querySelector("#open-add-user")?.addEventListener("click", prepareAddUser);
  document.querySelector("#user-form")?.addEventListener("submit", saveUser);
  document.querySelector("#password-reset-form")?.addEventListener("submit", resetPassword);
  document.querySelector("#users-table-body")?.addEventListener("click", handleUserAction);
  document.querySelector("#user-search")?.addEventListener("input", AdminApp.debounce(() => {
    userState.search = document.querySelector("#user-search").value.trim();
    userState.page = 1;
    loadUsers();
  }));
  document.querySelector("#user-role-filter")?.addEventListener("change", () => {
    userState.role = document.querySelector("#user-role-filter").value;
    userState.page = 1;
    loadUsers();
  });
  document.querySelector("#user-active-filter")?.addEventListener("change", () => {
    userState.isActive = document.querySelector("#user-active-filter").value;
    userState.page = 1;
    loadUsers();
  });
  document.querySelector("#user-page-size")?.addEventListener("change", () => {
    userState.pageSize = Number(document.querySelector("#user-page-size").value);
    userState.page = 1;
    loadUsers();
  });

  loadUsers();
});

async function loadUsers() {
  const tableBody = document.querySelector("#users-table-body");
  tableBody.innerHTML = `
    <tr>
      <td colspan="7" class="text-center text-muted py-4">Loading...</td>
    </tr>
  `;

  try {
    const query = AdminApp.buildQueryString({
      search: userState.search,
      role: userState.role,
      is_active: userState.isActive,
      page: userState.page,
      page_size: userState.pageSize,
    });
    const response = await AdminApp.authFetch(`/users${query}`);
    users = AdminApp.getItems(response);
    userPageData = response;
    renderUsers();
    renderUserPagination();
  } catch (error) {
    tableBody.innerHTML = `
      <tr>
        <td colspan="7" class="text-center text-danger py-4">Unable to load users.</td>
      </tr>
    `;
    AdminApp.showAlert("#users-alert", error.message, "danger");
  }
}

function renderUsers() {
  const tableBody = document.querySelector("#users-table-body");

  if (users.length === 0) {
    tableBody.innerHTML = `
      <tr>
        <td colspan="7" class="text-center text-muted py-4">No users match the selected filters.</td>
      </tr>
    `;
    return;
  }

  tableBody.innerHTML = users.map((user) => {
    const selfAction = user.id === currentUser.id;
    const statusButton = selfAction
      ? ""
      : user.is_active
        ? `
          <button class="btn btn-sm btn-outline-warning btn-icon" type="button" data-action="deactivate" data-id="${user.id}" aria-label="Deactivate user">
            <i class="bi bi-person-x"></i>
          </button>
        `
        : `
          <button class="btn btn-sm btn-outline-success btn-icon" type="button" data-action="activate" data-id="${user.id}" aria-label="Activate user">
            <i class="bi bi-person-check"></i>
          </button>
        `;

    return `
      <tr>
        <td>${AdminApp.escapeHtml(user.name)}</td>
        <td>${AdminApp.escapeHtml(user.email)}</td>
        <td>${AdminApp.escapeHtml(formatRole(user.role))}</td>
        <td>${AdminApp.statusBadge(user.is_active)}</td>
        <td>${AdminApp.escapeHtml(formatDateTime(user.last_login_at))}</td>
        <td>${AdminApp.escapeHtml(formatDateTime(user.created_at))}</td>
        <td class="text-end">
          <span class="action-buttons">
            <button class="btn btn-sm btn-action-view" type="button" data-action="view" data-id="${user.id}" aria-label="View user">
              <i class="bi bi-eye"></i> View
            </button>
            <button class="btn btn-sm btn-action-edit" type="button" data-action="edit" data-id="${user.id}" aria-label="Edit user">
              <i class="bi bi-pencil"></i> Edit
            </button>
            <button class="btn btn-sm btn-outline-secondary btn-icon" type="button" data-action="reset-password" data-id="${user.id}" aria-label="Reset password">
              <i class="bi bi-key"></i>
            </button>
            ${statusButton}
          </span>
        </td>
      </tr>
    `;
  }).join("");
}

function renderUserPagination() {
  AdminApp.renderPagination("#users-pagination", userPageData, (page) => {
    userState.page = page;
    loadUsers();
  });
}

function prepareAddUser() {
  document.querySelector("#user-form").reset();
  document.querySelector("#user-id").value = "";
  document.querySelector("#userModalTitle").textContent = "Add User";
  document.querySelector("#user-password-field").classList.remove("d-none");
  document.querySelector("#user-active-field").classList.add("d-none");
  document.querySelector("#user-role").value = "teacher";
  AdminApp.clearAlert("#user-form-alert");
}

function prepareEditUser(userId) {
  const user = users.find((item) => item.id === userId);
  if (!user) {
    AdminApp.showAlert("#users-alert", "User not found.", "danger");
    return;
  }

  document.querySelector("#user-form").reset();
  document.querySelector("#user-id").value = user.id;
  document.querySelector("#userModalTitle").textContent = "Edit User";
  document.querySelector("#user-name").value = user.name;
  document.querySelector("#user-email").value = user.email;
  document.querySelector("#user-role").value = user.role;
  document.querySelector("#user-active").value = String(user.is_active);
  document.querySelector("#user-password").value = "";
  document.querySelector("#user-password-field").classList.add("d-none");
  document.querySelector("#user-active-field").classList.remove("d-none");
  AdminApp.clearAlert("#user-form-alert");
  userModal.show();
}

async function saveUser(event) {
  event.preventDefault();

  const form = document.querySelector("#user-form");
  const saveButton = document.querySelector("#save-user");
  const userId = document.querySelector("#user-id").value;
  const nameInput = document.querySelector("#user-name");
  const emailInput = document.querySelector("#user-email");
  const passwordInput = document.querySelector("#user-password");

  AdminApp.clearFormErrors(form);

  const nameError = validateUserName(nameInput.value);
  const emailError = AdminApp.validateEmail(emailInput.value);
  const passwordError = userId ? null : validatePassword(passwordInput.value);

  let hasError = false;
  if (nameError) {
    AdminApp.showFieldError(nameInput, nameError);
    hasError = true;
  }
  if (emailError) {
    AdminApp.showFieldError(emailInput, emailError);
    hasError = true;
  }
  if (passwordError) {
    AdminApp.showFieldError(passwordInput, passwordError);
    hasError = true;
  }
  if (hasError) {
    AdminApp.focusFirstInvalidField(form);
    return;
  }

  const payload = {
    name: nameInput.value.trim(),
    email: emailInput.value.trim().toLowerCase(),
    role: document.querySelector("#user-role").value,
  };

  if (userId) {
    payload.is_active = document.querySelector("#user-active").value === "true";
  } else {
    payload.password = passwordInput.value;
  }

  AdminApp.setButtonLoading(saveButton, true);
  try {
    const url = userId ? `/users/${userId}` : "/users";
    const method = userId ? "PUT" : "POST";
    await AdminApp.authFetch(url, { method, body: payload });
    userModal.hide();
    AdminApp.showAlert("#users-alert", userId ? "User updated successfully." : "User created successfully.", "success");
    await loadUsers();
  } catch (error) {
    AdminApp.showAlert("#user-form-alert", error.message, "danger");
  } finally {
    AdminApp.setButtonLoading(saveButton, false);
  }
}

async function handleUserAction(event) {
  const button = event.target.closest("button[data-action]");
  if (!button) {
    return;
  }

  const userId = Number(button.dataset.id);
  const action = button.dataset.action;

  if (action === "view") {
    showUserDetails(userId);
    return;
  }

  if (action === "edit") {
    prepareEditUser(userId);
    return;
  }

  if (action === "reset-password") {
    preparePasswordReset(userId);
    return;
  }

  if (action === "deactivate" || action === "activate") {
    await updateUserActiveStatus(userId, action === "activate");
  }
}

function showUserDetails(userId) {
  const user = users.find((item) => item.id === userId);
  if (!user) {
    AdminApp.showAlert("#users-alert", "User not found.", "danger");
    return;
  }

  document.querySelector("#user-view-content").innerHTML = `
    <dl class="row mb-0">
      <dt class="col-sm-4">Name</dt>
      <dd class="col-sm-8">${AdminApp.escapeHtml(user.name)}</dd>
      <dt class="col-sm-4">Email</dt>
      <dd class="col-sm-8">${AdminApp.escapeHtml(user.email)}</dd>
      <dt class="col-sm-4">Role</dt>
      <dd class="col-sm-8">${AdminApp.escapeHtml(formatRole(user.role))}</dd>
      <dt class="col-sm-4">Status</dt>
      <dd class="col-sm-8">${AdminApp.statusBadge(user.is_active)}</dd>
      <dt class="col-sm-4">Last Login</dt>
      <dd class="col-sm-8">${AdminApp.escapeHtml(formatDateTime(user.last_login_at))}</dd>
      <dt class="col-sm-4">Created</dt>
      <dd class="col-sm-8">${AdminApp.escapeHtml(formatDateTime(user.created_at))}</dd>
    </dl>
  `;
  userViewModal.show();
}

function preparePasswordReset(userId) {
  const user = users.find((item) => item.id === userId);
  if (!user) {
    AdminApp.showAlert("#users-alert", "User not found.", "danger");
    return;
  }

  document.querySelector("#password-reset-form").reset();
  document.querySelector("#password-reset-user-id").value = user.id;
  document.querySelector("#passwordResetModalTitle").textContent = `Reset Password - ${user.name}`;
  AdminApp.clearAlert("#password-reset-alert");
  passwordResetModal.show();
}

async function resetPassword(event) {
  event.preventDefault();

  const form = document.querySelector("#password-reset-form");
  const saveButton = document.querySelector("#save-password-reset");
  const userId = document.querySelector("#password-reset-user-id").value;
  const passwordInput = document.querySelector("#password-reset-value");
  const passwordError = validatePassword(passwordInput.value);

  AdminApp.clearFormErrors(form);
  if (passwordError) {
    AdminApp.showFieldError(passwordInput, passwordError);
    AdminApp.focusFirstInvalidField(form);
    return;
  }

  AdminApp.setButtonLoading(saveButton, true, "Resetting...");
  try {
    await AdminApp.authFetch(`/users/${userId}/reset-password`, {
      method: "POST",
      body: { new_password: passwordInput.value },
    });
    passwordResetModal.hide();
    AdminApp.showAlert("#users-alert", "Password reset successfully.", "success");
  } catch (error) {
    AdminApp.showAlert("#password-reset-alert", error.message, "danger");
  } finally {
    AdminApp.setButtonLoading(saveButton, false);
  }
}

async function updateUserActiveStatus(userId, isActive) {
  const action = isActive ? "activate" : "deactivate";
  const confirmed = await AdminApp.confirmAction({
    title: isActive ? "Activate User" : "Deactivate User",
    message: isActive
      ? "Activate this user account?"
      : "Deactivate this user account? The user will not be able to log in.",
    confirmLabel: isActive ? "Activate" : "Deactivate",
    danger: !isActive,
  });

  if (!confirmed) {
    return;
  }

  try {
    await AdminApp.authFetch(`/users/${userId}/${action}`, { method: "PATCH" });
    AdminApp.showToast("success", isActive ? "User activated." : "User deactivated.");
    await loadUsers();
  } catch (error) {
    AdminApp.showAlert("#users-alert", error.message, "danger");
  }
}

function validatePassword(value) {
  if (!value || value.length < 8) {
    return "Password must be at least 8 characters.";
  }
  if (value.length > 128) {
    return "Password must be 128 characters or fewer.";
  }
  if (!/[A-Za-z]/.test(value) || !/\d/.test(value)) {
    return "Password must include at least one letter and one number.";
  }
  return null;
}

function validateUserName(value) {
  const trimmed = (value || "").trim();
  if (!trimmed) {
    return "Name is required.";
  }
  if (trimmed.length < 2 || trimmed.length > 150) {
    return "Name must be between 2 and 150 characters.";
  }
  return null;
}

function formatRole(role) {
  const labels = {
    admin: "Admin",
    teacher: "Teacher",
    accountant: "Accountant",
    staff: "Staff (Legacy)",
  };
  return labels[role] || role;
}

function formatDateTime(value) {
  if (!value) {
    return "";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return String(value);
  }
  return date.toLocaleString();
}
