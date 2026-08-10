const AdminApp = (() => {
  const navItems = [
    { key: "dashboard", label: "Dashboard", icon: "bi-speedometer2", href: "/admin" },
    { key: "students", label: "Students", icon: "bi-people", href: "/admin/students" },
    { key: "courses", label: "Courses", icon: "bi-journal-bookmark", href: "/admin/courses" },
    { key: "attendance", label: "Attendance", icon: "bi-calendar-check", disabled: true },
    { key: "fees", label: "Fees", icon: "bi-cash-coin", disabled: true },
    { key: "reports", label: "Reports", icon: "bi-bar-chart", disabled: true },
  ];

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

  function statusBadge(value, activeValue = "active") {
    const normalizedValue = String(value).toLowerCase();
    const isActive = normalizedValue === String(activeValue).toLowerCase() || value === true;
    const label = isActive ? "Active" : "Inactive";
    const cssClass = isActive ? "status-active" : "status-inactive";
    return `<span class="status-badge ${cssClass}">${label}</span>`;
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

  function initLayout() {
    renderSidebar();
    renderTopbar();
    bindSidebarToggle();
  }

  function renderSidebar() {
    const sidebar = document.querySelector("#sidebar");
    if (!sidebar) {
      return;
    }

    const activePage = document.body.dataset.page || "dashboard";
    const links = navItems.map((item) => {
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

    const title = document.body.dataset.title || "Dashboard";
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
      <div class="admin-chip">
        <span class="avatar-dot"><i class="bi bi-person"></i></span>
        <span>Admin</span>
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

  document.addEventListener("DOMContentLoaded", initLayout);

  return {
    apiRequest,
    clearAlert,
    escapeHtml,
    formatDate,
    setButtonLoading,
    showAlert,
    statusBadge,
  };
})();
