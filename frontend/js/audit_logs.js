let auditLogs = [];
let auditModal;
let auditPageData = null;
let auditState = {
  page: 1,
  pageSize: 10,
  search: "",
  user: "",
  action: "",
  entityType: "",
  startDate: "",
  endDate: "",
};

document.addEventListener("DOMContentLoaded", () => {
  auditModal = new bootstrap.Modal(document.querySelector("#auditLogModal"));
  const currentUser = AdminApp.getCurrentUser();

  if (currentUser?.role !== "admin") {
    document.querySelector("#audit-table-body").innerHTML = `
      <tr>
        <td colspan="6" class="text-center text-muted py-4">Admin access required.</td>
      </tr>
    `;
    AdminApp.showAlert("#audit-alert", "Admin access required.", "danger");
    return;
  }

  bindFilters();
  document.querySelector("#audit-table-body")?.addEventListener("click", handleAuditAction);
  loadUsers();
  loadAuditLogs();
});

function bindFilters() {
  document.querySelector("#audit-search")?.addEventListener("input", AdminApp.debounce(() => {
    auditState.search = document.querySelector("#audit-search").value.trim();
    auditState.page = 1;
    loadAuditLogs();
  }));
  document.querySelector("#audit-user-filter")?.addEventListener("change", () => {
    auditState.user = document.querySelector("#audit-user-filter").value;
    auditState.page = 1;
    loadAuditLogs();
  });
  document.querySelector("#audit-action-filter")?.addEventListener("input", AdminApp.debounce(() => {
    auditState.action = document.querySelector("#audit-action-filter").value.trim();
    auditState.page = 1;
    loadAuditLogs();
  }));
  document.querySelector("#audit-entity-filter")?.addEventListener("input", AdminApp.debounce(() => {
    auditState.entityType = document.querySelector("#audit-entity-filter").value.trim();
    auditState.page = 1;
    loadAuditLogs();
  }));
  document.querySelector("#audit-start-date")?.addEventListener("change", () => {
    auditState.startDate = document.querySelector("#audit-start-date").value;
    auditState.page = 1;
    loadAuditLogs();
  });
  document.querySelector("#audit-end-date")?.addEventListener("change", () => {
    auditState.endDate = document.querySelector("#audit-end-date").value;
    auditState.page = 1;
    loadAuditLogs();
  });
  document.querySelector("#audit-page-size")?.addEventListener("change", () => {
    auditState.pageSize = Number(document.querySelector("#audit-page-size").value);
    auditState.page = 1;
    loadAuditLogs();
  });
}

async function loadUsers() {
  try {
    const response = await AdminApp.authFetch("/users?page_size=100");
    const users = AdminApp.getItems(response);
    const select = document.querySelector("#audit-user-filter");
    select.innerHTML = '<option value="">All users</option>' +
      users.map((user) => `
        <option value="${user.id}">${AdminApp.escapeHtml(user.name)} (${AdminApp.escapeHtml(user.email)})</option>
      `).join("");
  } catch (error) {
    AdminApp.showAlert("#audit-alert", error.message, "danger");
  }
}

async function loadAuditLogs() {
  const tableBody = document.querySelector("#audit-table-body");
  tableBody.innerHTML = `
    <tr>
      <td colspan="6" class="text-center text-muted py-4">Loading...</td>
    </tr>
  `;

  try {
    const query = AdminApp.buildQueryString({
      user: auditState.user,
      action: auditState.action,
      entity_type: auditState.entityType,
      start_date: auditState.startDate,
      end_date: auditState.endDate,
      search: auditState.search,
      page: auditState.page,
      page_size: auditState.pageSize,
    });
    const response = await AdminApp.authFetch(`/audit-logs${query}`);
    auditLogs = AdminApp.getItems(response);
    auditPageData = response;
    renderAuditLogs();
    renderAuditPagination();
  } catch (error) {
    tableBody.innerHTML = `
      <tr>
        <td colspan="6" class="text-center text-danger py-4">Unable to load audit logs.</td>
      </tr>
    `;
    AdminApp.showAlert("#audit-alert", error.message, "danger");
  }
}

function renderAuditLogs() {
  const tableBody = document.querySelector("#audit-table-body");

  if (auditLogs.length === 0) {
    tableBody.innerHTML = `
      <tr>
        <td colspan="6" class="text-center text-muted py-4">No audit logs match the selected filters.</td>
      </tr>
    `;
    return;
  }

  tableBody.innerHTML = auditLogs.map((log) => `
    <tr>
      <td>${AdminApp.escapeHtml(formatDateTime(log.created_at))}</td>
      <td>${AdminApp.escapeHtml(formatUser(log))}</td>
      <td>${AdminApp.escapeHtml(log.action)}</td>
      <td>${AdminApp.escapeHtml(formatEntity(log))}</td>
      <td>${AdminApp.escapeHtml(log.description)}</td>
      <td class="text-end">
        <button class="btn btn-sm btn-action-view" type="button" data-action="view" data-id="${log.id}" aria-label="View audit log">
          <i class="bi bi-eye"></i> View
        </button>
      </td>
    </tr>
  `).join("");
}

function renderAuditPagination() {
  AdminApp.renderPagination("#audit-pagination", auditPageData, (page) => {
    auditState.page = page;
    loadAuditLogs();
  });
}

function handleAuditAction(event) {
  const button = event.target.closest("button[data-action='view']");
  if (!button) {
    return;
  }
  const log = auditLogs.find((item) => item.id === Number(button.dataset.id));
  if (!log) {
    AdminApp.showAlert("#audit-alert", "Audit log not found.", "danger");
    return;
  }
  showAuditLog(log);
}

function showAuditLog(log) {
  document.querySelector("#audit-log-detail").innerHTML = `
    <dl class="row mb-0">
      <dt class="col-sm-4">User</dt>
      <dd class="col-sm-8">${AdminApp.escapeHtml(formatUser(log))}</dd>
      <dt class="col-sm-4">Action</dt>
      <dd class="col-sm-8">${AdminApp.escapeHtml(log.action)}</dd>
      <dt class="col-sm-4">Entity</dt>
      <dd class="col-sm-8">${AdminApp.escapeHtml(formatEntity(log))}</dd>
      <dt class="col-sm-4">Timestamp</dt>
      <dd class="col-sm-8">${AdminApp.escapeHtml(formatDateTime(log.created_at))}</dd>
      <dt class="col-sm-4">Description</dt>
      <dd class="col-sm-8">${AdminApp.escapeHtml(log.description)}</dd>
      <dt class="col-sm-4">IP Address</dt>
      <dd class="col-sm-8">${AdminApp.escapeHtml(log.ip_address || "")}</dd>
      <dt class="col-sm-4">Metadata</dt>
      <dd class="col-sm-8"><pre class="mb-0">${AdminApp.escapeHtml(formatMetadata(log.metadata_json))}</pre></dd>
    </dl>
  `;
  auditModal.show();
}

function formatUser(log) {
  if (log.user_name || log.user_email) {
    return `${log.user_name || "User"}${log.user_email ? ` (${log.user_email})` : ""}`;
  }
  return log.user_id ? `User #${log.user_id}` : "System";
}

function formatEntity(log) {
  return log.entity_id ? `${log.entity_type} #${log.entity_id}` : log.entity_type;
}

function formatMetadata(metadata) {
  if (!metadata) {
    return "";
  }
  return JSON.stringify(metadata, null, 2);
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
