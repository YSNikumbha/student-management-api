const AdminApp = (() => {
  const TOKEN_KEY = "student_management_token";
  const USER_KEY = "student_management_user";
  const ALL_ROLES = ["admin", "teacher", "accountant", "staff"];

  const navItems = [
    { key: "dashboard", label: "Dashboard", icon: "bi-speedometer2", href: "/admin", roles: ALL_ROLES },
    { key: "students", label: "Students", icon: "bi-people", href: "/admin/students", roles: ALL_ROLES },
    { key: "courses", label: "Courses", icon: "bi-journal-bookmark", href: "/admin/courses", roles: ALL_ROLES },
    { key: "attendance", label: "Attendance", icon: "bi-calendar-check", href: "/admin/attendance", roles: ["admin", "teacher", "staff"] },
    { key: "fees", label: "Fees", icon: "bi-cash-coin", href: "/admin/fees", roles: ["admin", "accountant", "staff"] },
    { key: "reports", label: "Reports", icon: "bi-bar-chart", href: "/admin/reports", roles: ALL_ROLES },
    { key: "users", label: "Users", icon: "bi-person-gear", href: "/admin/users", roles: ["admin"] },
    { key: "audit-logs", label: "Audit Logs", icon: "bi-clipboard-data", href: "/admin/audit-logs", roles: ["admin"] },
  ];

  // ============================================
  // UTILITIES
  // ============================================
  
  function escapeHtml(value) {
    if (value === null || value === undefined) {
      return "";
    }

    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function formatDate(value) {
    if (!value) {
      return "";
    }

    return String(value).slice(0, 10);
  }

  function formatCurrency(value) {
    const amount = Number(value || 0);
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(Number.isFinite(amount) ? amount : 0);
  }

  function debounce(callback, delay = 400) {
    let timeoutId;

    return (...args) => {
      window.clearTimeout(timeoutId);
      timeoutId = window.setTimeout(() => callback(...args), delay);
    };
  }

  // ============================================
  // VALIDATION HELPERS
  // ============================================

  function trimValue(value) {
    if (typeof value !== "string") {
      return value === null || value === undefined ? "" : String(value).trim();
    }
    return value.trim();
  }

  function validateRequired(value, fieldName = "This field") {
    const trimmed = trimValue(value);
    if (!trimmed) {
      return `${fieldName} is required.`;
    }
    return null;
  }

  function validateName(value, fieldName = "Name") {
    const trimmed = trimValue(value);
    if (!trimmed) {
      return `${fieldName} is required.`;
    }
    if (trimmed.length < 2 || trimmed.length > 100) {
      return `${fieldName} must be between 2 and 100 characters.`;
    }
    const namePattern = /^[\p{L}\p{M}\s'-]+$/u;
    if (!namePattern.test(trimmed)) {
      return `${fieldName} contains invalid characters.`;
    }
    return null;
  }

  function validateEmail(value) {
    const trimmed = trimValue(value);
    if (!trimmed) {
      return "Email is required.";
    }
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailPattern.test(trimmed)) {
      return "Please enter a valid email address.";
    }
    if (trimmed.length > 255) {
      return "Email must be less than 255 characters.";
    }
    return null;
  }

  function validatePhone(value) {
    const trimmed = trimValue(value);
    if (!trimmed) {
      return null;
    }
    const normalized = trimmed.replace(/[^\d+]/g, "");
    const hasPlus = normalized.startsWith("+");
    const digits = normalized.replace(/\+/g, "");
    
    if (digits.length < 10 || digits.length > 15) {
      return "Phone must be 10 to 15 digits.";
    }
    if (hasPlus && !normalized.match(/^\+[\d]{10,15}$/)) {
      return "Phone format is invalid. Use +1234567890 or 1234567890.";
    }
    if (!hasPlus && digits.length < 10) {
      return "Phone must be at least 10 digits.";
    }
    return null;
  }

  function validatePositiveInteger(value, fieldName = "Value") {
    const trimmed = trimValue(value);
    if (!trimmed) {
      return `${fieldName} is required.`;
    }
    const num = Number(trimmed);
    if (!Number.isInteger(num) || num <= 0) {
      return `${fieldName} must be a positive integer.`;
    }
    return null;
  }

  function validatePositiveDecimal(value, fieldName = "Value") {
    const trimmed = trimValue(value);
    if (!trimmed) {
      return `${fieldName} is required.`;
    }
    const num = Number(trimmed);
    if (!Number.isFinite(num) || num <= 0) {
      return `${fieldName} must be a positive number.`;
    }
    return null;
  }

  function validateDateNotFuture(value, fieldName = "Date") {
    const trimmed = trimValue(value);
    if (!trimmed) {
      return null;
    }
    const date = new Date(trimmed);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    if (isNaN(date.getTime())) {
      return `${fieldName} is not a valid date.`;
    }
    if (date > today) {
      return `${fieldName} cannot be in the future.`;
    }
    return null;
  }

  function validateDateRange(startDate, endDate, fieldName = "Date") {
    const start = trimValue(startDate);
    const end = trimValue(endDate);
    
    if (!start || !end) {
      return null;
    }
    
    const startDt = new Date(start);
    const endDt = new Date(end);
    
    if (isNaN(startDt.getTime()) || isNaN(endDt.getTime())) {
      return `${fieldName} range contains invalid dates.`;
    }
    
    if (startDt > endDt) {
      return `Start ${fieldName.toLowerCase()} must be before end ${fieldName.toLowerCase()}.`;
    }
    return null;
  }

  function validateStudentCode(value) {
    const trimmed = trimValue(value);
    if (!trimmed) {
      return "Student code is required.";
    }
    if (trimmed.length < 2 || trimmed.length > 50) {
      return "Student code must be between 2 and 50 characters.";
    }
    const codePattern = /^[A-Za-z0-9\-_]+$/;
    if (!codePattern.test(trimmed)) {
      return "Student code can only contain letters, numbers, hyphens, and underscores.";
    }
    return null;
  }

  // ============================================
  // INLINE VALIDATION UI
  // ============================================

  function showFieldError(input, message) {
    if (!input) {
      return;
    }

    clearFieldError(input);

    input.classList.add("is-invalid");
    input.setAttribute("aria-invalid", "true");

    const errorElement = document.createElement("div");
    errorElement.className = "field-error";
    errorElement.textContent = message;
    errorElement.setAttribute("role", "alert");

    const parent = input.parentElement;
    if (parent) {
      parent.appendChild(errorElement);
    }
  }

  function clearFieldError(input) {
    if (!input) {
      return;
    }

    input.classList.remove("is-invalid");
    input.removeAttribute("aria-invalid");

    const parent = input.parentElement;
    if (parent) {
      const errorElement = parent.querySelector(".field-error");
      if (errorElement) {
        errorElement.remove();
      }
    }
  }

  function clearFormErrors(form) {
    if (!form) {
      return;
    }

    form.querySelectorAll(".is-invalid").forEach((input) => {
      clearFieldError(input);
    });

    form.querySelectorAll(".field-error, .validation-message").forEach((el) => {
      el.remove();
    });
  }

  function focusFirstInvalidField(form) {
    if (!form) {
      return;
    }

    const firstInvalid = form.querySelector(".is-invalid");
    if (firstInvalid) {
      firstInvalid.focus();
      return true;
    }
    return false;
  }

  // ============================================
  // LOADING BUTTON HELPER
  // ============================================

  function setButtonLoading(button, isLoading, loadingText = "Saving...") {
    if (!button) {
      return;
    }

    if (isLoading) {
      button.dataset.originalHtml = button.innerHTML;
      button.disabled = true;
      button.innerHTML = `
        <span class="spinner-border spinner-border-sm me-2" aria-hidden="true"></span>
        ${escapeHtml(loadingText)}
      `;
      return;
    }

    button.disabled = false;
    if (button.dataset.originalHtml) {
      button.innerHTML = button.dataset.originalHtml;
      delete button.dataset.originalHtml;
    }
  }

  // ============================================
  // API & AUTH
  // ============================================

  function getItems(response) {
    if (Array.isArray(response)) {
      return response;
    }

    return response?.items || [];
  }

  function buildQueryString(params) {
    const query = new URLSearchParams();

    Object.entries(params).forEach(([key, value]) => {
      if (value !== null && value !== undefined && value !== "") {
        query.set(key, value);
      }
    });

    const queryString = query.toString();
    return queryString ? `?${queryString}` : "";
  }

  async function apiRequest(url, options = {}) {
    const fetchOptions = {
      ...options,
      headers: {
        Accept: "application/json",
        ...(options.headers || {}),
      },
    };

    if (fetchOptions.body && typeof fetchOptions.body !== "string") {
      fetchOptions.headers["Content-Type"] = "application/json";
      fetchOptions.body = JSON.stringify(fetchOptions.body);
    }

    const response = await fetch(url, fetchOptions);
    return handleResponse(response);
  }

  async function authFetch(url, options = {}) {
    const token = getToken();
    if (!token) {
      redirectToLogin();
      throw new Error("Please log in to continue.");
    }

    try {
      return await apiRequest(url, {
        ...options,
        headers: {
          ...(options.headers || {}),
          Authorization: `Bearer ${token}`,
        },
      });
    } catch (error) {
      if (error.status === 401) {
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(USER_KEY);
        redirectToLogin();
      }

      if (error.status === 403) {
        error.message = "You do not have permission to perform this action.";
      }

      throw error;
    }
  }

  async function downloadAuthenticatedFile(url, fallbackFilename = "download") {
    const token = getToken();
    if (!token) {
      redirectToLogin();
      throw new Error("Please log in to continue.");
    }

    const response = await fetch(url, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      const contentType = response.headers.get("content-type") || "";
      let errorData;
      if (contentType.includes("application/json")) {
        errorData = await response.json();
      } else {
        errorData = { detail: await response.text() };
      }
      const error = new Error(extractErrorMessage(errorData, response.status));
      error.status = response.status;
      throw error;
    }

    const blob = await response.blob();
    const contentDisposition = response.headers.get("content-disposition") || "";
    const filenameMatch = contentDisposition.match(/filename\*?=(?:UTF-8'')?"?([^";]+)"?/i);
    const filename = filenameMatch
      ? decodeURIComponent(filenameMatch[1])
      : fallbackFilename;
    const objectUrl = URL.createObjectURL(blob);
    const link = document.createElement("a");

    try {
      link.href = objectUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
    } finally {
      link.remove();
      URL.revokeObjectURL(objectUrl);
    }

    return { filename, blob };
  }

  async function handleResponse(response) {
    if (response.status === 204) {
      if (!response.ok) {
        throw buildApiError(response, null);
      }
      return null;
    }

    const contentType = response.headers.get("content-type") || "";
    const data = contentType.includes("application/json")
      ? await response.json()
      : await response.text();

    if (!response.ok) {
      throw buildApiError(response, data);
    }

    return data;
  }

  function buildApiError(response, data) {
    const error = new Error(extractErrorMessage(data, response.status));
    error.status = response.status;
    error.data = data;
    return error;
  }

  function extractErrorMessage(data, status) {
    if (data && typeof data === "object" && "detail" in data) {
      if (Array.isArray(data.detail)) {
        return data.detail
          .map((item) => {
            const location = Array.isArray(item.loc) ? item.loc.join(".") : "field";
            return `${location}: ${item.msg}`;
          })
          .join(" ");
      }

      return String(data.detail);
    }

    if (typeof data === "string" && data.trim()) {
      return data;
    }

    if (status === 404) {
      return "Resource not found.";
    }

    if (status === 409) {
      return "This request conflicts with existing data.";
    }

    if (status === 422) {
      return "Please check the form values.";
    }

    return "Unexpected server error.";
  }

  // ============================================
  // UI HELPERS
  // ============================================

  function showAlert(target, message, type = "success") {
    const element = typeof target === "string" ? document.querySelector(target) : target;
    if (!element) {
      return;
    }

    element.innerHTML = `
      <div class="alert alert-${type} alert-dismissible fade show" role="alert">
        ${escapeHtml(message)}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
      </div>
    `;
  }

  function clearAlert(target) {
    const element = typeof target === "string" ? document.querySelector(target) : target;
    if (element) {
      element.innerHTML = "";
    }
  }

  function showToast(type, message, duration = 3000) {
    const toastContainer = document.querySelector("#toast-container") || createToastContainer();
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    toast.setAttribute("role", "alert");
    toast.setAttribute("aria-live", "polite");
    toast.innerHTML = `
      <div class="toast-icon">
        <i class="bi ${getToastIcon(type)}" aria-hidden="true"></i>
      </div>
      <div class="toast-message">${escapeHtml(message)}</div>
      <button type="button" class="toast-close" aria-label="Close notification">
        <i class="bi bi-x" aria-hidden="true"></i>
      </button>
    `;

    toastContainer.appendChild(toast);
    requestAnimationFrame(() => toast.classList.add("show"));

    const close = () => {
      toast.classList.remove("show");
      setTimeout(() => toast.remove(), 300);
    };

    toast.querySelector(".toast-close").addEventListener("click", close);
    setTimeout(close, duration);
  }

  function createToastContainer() {
    const container = document.createElement("div");
    container.id = "toast-container";
    container.setAttribute("aria-live", "polite");
    container.setAttribute("aria-atomic", "true");
    document.body.appendChild(container);
    return container;
  }

  function getToastIcon(type) {
    const icons = {
      success: "bi-check-circle-fill",
      error: "bi-x-circle-fill",
      warning: "bi-exclamation-triangle-fill",
      info: "bi-info-circle-fill",
    };
    return icons[type] || icons.info;
  }

  function confirmAction({ title = "Confirm action", message, confirmLabel = "Confirm", cancelLabel = "Cancel", danger = false } = {}) {
    return new Promise((resolve) => {
      const backdrop = document.createElement("div");
      backdrop.className = "confirm-modal-backdrop";
      document.body.appendChild(backdrop);

      const modal = document.createElement("div");
      modal.className = "confirm-modal";
      modal.setAttribute("role", "dialog");
      modal.setAttribute("aria-modal", "true");
      modal.setAttribute("aria-labelledby", "confirm-modal-title");
      modal.innerHTML = `
        <div class="confirm-modal-header">
          <h3 class="confirm-modal-title" id="confirm-modal-title">${escapeHtml(title)}</h3>
        </div>
        <div class="confirm-modal-body">
          <p class="mb-0">${escapeHtml(message)}</p>
        </div>
        <div class="confirm-modal-footer">
          <button type="button" class="btn btn-secondary-app" id="confirm-cancel-button">${escapeHtml(cancelLabel)}</button>
          <button type="button" class="btn ${danger ? "btn-danger-app" : "btn-primary-app"}" id="confirm-action-button">
            ${escapeHtml(confirmLabel)}
          </button>
        </div>
      `;

      document.body.appendChild(modal);
      document.body.style.overflow = "hidden";

      const cleanup = () => {
        backdrop.remove();
        modal.remove();
        document.body.style.overflow = "";
      };

      const handleCancel = () => {
        cleanup();
        resolve(false);
      };

      const handleConfirm = () => {
        cleanup();
        resolve(true);
      };

      document.getElementById("confirm-cancel-button").addEventListener("click", handleCancel);
      document.getElementById("confirm-action-button").addEventListener("click", handleConfirm);
      
      backdrop.addEventListener("click", handleCancel);

      const handleKeydown = (event) => {
        if (event.key === "Escape") {
          handleCancel();
        }
      };
      
      document.addEventListener("keydown", handleKeydown);
      
      modal._cleanup = () => {
        document.removeEventListener("keydown", handleKeydown);
        cleanup();
      };

      setTimeout(() => {
        document.getElementById("confirm-action-button").focus();
      }, 0);
    });
  }

  // ============================================
  // BADGES
  // ============================================

  function statusBadge(value, activeValue = "active") {
    const normalizedValue = String(value).toLowerCase();
    const isActive = normalizedValue === String(activeValue).toLowerCase() || value === true;
    const label = isActive ? "Active" : "Inactive";
    const cssClass = isActive ? "status-active" : "status-inactive";
    return `<span class="status-badge ${cssClass}">${label}</span>`;
  }

  function attendanceBadge(value) {
    const normalizedValue = String(value).toLowerCase();
    const cssClassByStatus = {
      present: "status-active",
      absent: "status-inactive",
      late: "status-pending",
    };
    const label = normalizedValue.charAt(0).toUpperCase() + normalizedValue.slice(1);
    const cssClass = cssClassByStatus[normalizedValue] || "status-pending";
    return `<span class="status-badge ${cssClass}">${escapeHtml(label)}</span>`;
  }

  function feeStatusBadge(value) {
    const normalizedValue = String(value).toLowerCase();
    const cssClassByStatus = {
      paid: "status-active",
      overdue: "status-inactive",
      partial: "status-pending",
      unpaid: "status-neutral",
    };
    const label = normalizedValue.charAt(0).toUpperCase() + normalizedValue.slice(1);
    const cssClass = cssClassByStatus[normalizedValue] || "status-neutral";
    return `<span class="status-badge ${cssClass}">${escapeHtml(label)}</span>`;
  }

  // ============================================
  // AUTH
  // ============================================

  function getToken() {
    return localStorage.getItem(TOKEN_KEY);
  }

  function getCurrentUser() {
    const storedUser = localStorage.getItem(USER_KEY);
    if (!storedUser) {
      return null;
    }

    try {
      return JSON.parse(storedUser);
    } catch {
      localStorage.removeItem(USER_KEY);
      return null;
    }
  }

  function hasAnyRole(...roles) {
    const user = getCurrentUser();
    return Boolean(user && roles.includes(user.role));
  }

  function isAuthenticated() {
    return Boolean(getToken() && getCurrentUser());
  }

  function saveAuthSession(token, user) {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  }

  function logout() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    window.location.href = "/login";
  }

  function redirectToLogin() {
    const next = window.location.pathname.startsWith("/admin")
      ? `?next=${encodeURIComponent(window.location.pathname)}`
      : "";
    window.location.href = `/login${next}`;
  }

  function requireLoginForAdminPages() {
    if (document.body.dataset.publicPage === "true") {
      return;
    }

    if (window.location.pathname.startsWith("/admin") && !isAuthenticated()) {
      redirectToLogin();
    }
  }

  // ============================================
  // PAGINATION
  // ============================================

  function renderPagination(target, pageData, onPageChange) {
    const element = typeof target === "string" ? document.querySelector(target) : target;
    if (!element || !pageData) {
      return;
    }

    const page = Number(pageData.page || 1);
    const totalPages = Number(pageData.total_pages || 0);
    const totalItems = Number(pageData.total_items || 0);
    const hasPages = totalPages > 0;
    const previousPage = Math.max(1, page - 1);
    const nextPage = page + 1;

    element.innerHTML = `
      <div class="pagination-bar">
        <div class="pagination-summary">
          ${hasPages ? `Page ${page} of ${totalPages}` : "No pages"}
          <span>${totalItems} record${totalItems === 1 ? "" : "s"}</span>
        </div>
        <div class="pagination-actions">
          <button class="btn btn-outline-secondary btn-sm" type="button" data-page="${previousPage}" ${page <= 1 ? "disabled" : ""}>
            Previous
          </button>
          <button class="btn btn-outline-secondary btn-sm" type="button" data-page="${nextPage}" ${!hasPages || page >= totalPages ? "disabled" : ""}>
            Next
          </button>
        </div>
      </div>
    `;

    element.querySelectorAll("button[data-page]").forEach((button) => {
      button.addEventListener("click", () => {
        onPageChange(Number(button.dataset.page));
      });
    });
  }

  // ============================================
  // LAYOUT
  // ============================================

  function initLayout() {
    requireLoginForAdminPages();
    renderSidebar();
    renderTopbar();
    bindSidebarToggle();
    bindLogout();
  }

  function renderSidebar() {
    const sidebar = document.querySelector("#sidebar");
    if (!sidebar) {
      return;
    }

    const activePage = document.body.dataset.page || "dashboard";
    const user = getCurrentUser();
    const visibleItems = navItems.filter((item) => {
      if (!item.roles || item.roles.length === 0) {
        return true;
      }
      return Boolean(user && item.roles.includes(user.role));
    });
    const links = visibleItems.map((item) => {
      const isActive = item.key === activePage;
      const classes = ["sidebar-link", isActive ? "active" : "", item.disabled ? "disabled" : ""]
        .filter(Boolean)
        .join(" ");
      const href = item.disabled ? "#" : item.href;
      const comingSoon = item.disabled ? '<span class="coming-soon">Coming Soon</span>' : "";
      const ariaDisabled = item.disabled ? ' aria-disabled="true"' : "";

      return `
        <a class="${classes}" href="${href}"${ariaDisabled}>
          <span class="sidebar-link-main">
            <i class="bi ${item.icon}"></i>
            <span>${escapeHtml(item.label)}</span>
          </span>
          ${comingSoon}
        </a>
      `;
    }).join("");

    sidebar.innerHTML = `
      <div class="brand-block">
        <span class="brand-mark"><i class="bi bi-mortarboard-fill"></i></span>
        <div>
          <p class="brand-title">Student Management System</p>
          <p class="brand-subtitle">Admin Dashboard</p>
        </div>
      </div>
      <div class="nav-section-label">Main</div>
      <nav class="sidebar-nav" aria-label="Admin navigation">
        ${links}
      </nav>
    `;

    sidebar.querySelectorAll(".sidebar-link.disabled").forEach((link) => {
      link.addEventListener("click", (event) => event.preventDefault());
    });
  }

  function renderTopbar() {
    const topbar = document.querySelector("#topbar");
    if (!topbar) {
      return;
    }

    const user = getCurrentUser();
    const title = document.body.dataset.title || "Dashboard";
    const name = user ? user.name : "Admin";
    const role = user ? user.role : "";
    topbar.innerHTML = `
      <div class="d-flex align-items-center gap-3">
        <button id="sidebar-toggle" class="btn btn-outline-secondary btn-icon mobile-menu-button" type="button" aria-label="Open navigation">
          <i class="bi bi-list"></i>
        </button>
        <div>
          <p class="topbar-title">${escapeHtml(title)}</p>
          <p class="topbar-project">Student Management System</p>
        </div>
      </div>
      <div class="topbar-user">
        <div class="admin-chip">
          <span class="avatar-dot"><i class="bi bi-person"></i></span>
          <span>${escapeHtml(name)}</span>
          <small>${escapeHtml(role)}</small>
        </div>
        <button id="logout-button" class="btn btn-outline-secondary btn-sm" type="button">
          <i class="bi bi-box-arrow-right"></i>
          Logout
        </button>
      </div>
    `;
  }

  function bindSidebarToggle() {
    const toggle = document.querySelector("#sidebar-toggle");
    const backdrop = document.querySelector("#sidebar-backdrop");

    if (toggle) {
      toggle.addEventListener("click", () => {
        document.body.classList.toggle("sidebar-open");
      });
    }

    if (backdrop) {
      backdrop.addEventListener("click", () => {
        document.body.classList.remove("sidebar-open");
      });
    }
  }

  function bindLogout() {
    const logoutButton = document.querySelector("#logout-button");
    if (logoutButton) {
      logoutButton.addEventListener("click", logout);
    }
  }

  document.addEventListener("DOMContentLoaded", initLayout);

  return {
    apiRequest,
    attendanceBadge,
    authFetch,
    buildQueryString,
    clearAlert,
    clearFieldError,
    clearFormErrors,
    confirmAction,
    debounce,
    downloadAuthenticatedFile,
    escapeHtml,
    feeStatusBadge,
    focusFirstInvalidField,
    formatCurrency,
    formatDate,
    getCurrentUser,
    hasAnyRole,
    getItems,
    getToken,
    isAuthenticated,
    logout,
    renderPagination,
    saveAuthSession,
    setButtonLoading,
    showAlert,
    showFieldError,
    showToast,
    statusBadge,
    trimValue,
    validateDateNotFuture,
    validateDateRange,
    validateEmail,
    validateName,
    validatePhone,
    validatePositiveDecimal,
    validatePositiveInteger,
    validateRequired,
    validateStudentCode,
  };
})();
