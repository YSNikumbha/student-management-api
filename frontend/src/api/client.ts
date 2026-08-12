export type ApiErrorPayload = {
  detail?: unknown;
  message?: string;
};

export class ApiError extends Error {
  status: number;
  payload: ApiErrorPayload | string | null;

  constructor(status: number, payload: ApiErrorPayload | string | null, fallback = "Request failed") {
    const detail =
      typeof payload === "object" && payload !== null && "detail" in payload
        ? payload.detail
        : typeof payload === "object" && payload !== null && "message" in payload
          ? payload.message
          : payload;
    super(typeof detail === "string" ? detail : fallback);
    this.name = "ApiError";
    this.status = status;
    this.payload = payload;
  }
}

function defaultApiBaseUrl(): string {
  if (typeof window !== "undefined" && window.location.port !== "5173") {
    return window.location.origin;
  }
  return "http://127.0.0.1:8000";
}

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") || defaultApiBaseUrl();

const TOKEN_KEY = "sms_access_token";
const USER_KEY = "sms_current_user";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearSession(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export function setStoredUser(user: unknown): void {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function getStoredUser<T>(): T | null {
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as T;
  } catch {
    return null;
  }
}

function buildHeaders(body: BodyInit | null | undefined, extra?: HeadersInit): Headers {
  const headers = new Headers(extra);
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (body !== undefined && !(body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  return headers;
}

async function parseError(response: Response): Promise<ApiErrorPayload | string | null> {
  const contentType = response.headers.get("Content-Type") || "";
  if (contentType.includes("application/json")) {
    return (await response.json()) as ApiErrorPayload;
  }
  const text = await response.text();
  return text || null;
}

export async function apiRequest<T>(
  path: string,
  options: RequestInit & { json?: unknown } = {},
): Promise<T> {
  const body = options.json !== undefined ? JSON.stringify(options.json) : options.body;
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    body,
    headers: buildHeaders(body, options.headers),
  });

  if (response.status === 401) {
    clearSession();
    window.dispatchEvent(new CustomEvent("sms:unauthorized"));
  }

  if (!response.ok) {
    throw new ApiError(response.status, await parseError(response), response.statusText);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const contentType = response.headers.get("Content-Type") || "";
  if (!contentType.includes("application/json")) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

function filenameFromDisposition(disposition: string | null, fallback: string): string {
  if (!disposition) return fallback;
  const utf8 = disposition.match(/filename\*=UTF-8''([^;]+)/i);
  if (utf8?.[1]) return decodeURIComponent(utf8[1]);
  const plain = disposition.match(/filename="?([^";]+)"?/i);
  return plain?.[1] || fallback;
}

export async function downloadAuthenticatedFile(path: string, fallbackName: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: buildHeaders(undefined),
  });

  if (!response.ok) {
    throw new ApiError(response.status, await parseError(response), response.statusText);
  }

  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filenameFromDisposition(response.headers.get("Content-Disposition"), fallbackName);
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}
