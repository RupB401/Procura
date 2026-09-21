/**
 * API Client — wraps fetch with base URL, auth headers, and error handling.
 */

const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8001/api/v1';

function getToken(): string | null {
  return localStorage.getItem('access_token');
}

interface RequestOptions extends RequestInit {
  skipAuth?: boolean;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { skipAuth = false, ...rest } = options;

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(rest.headers as Record<string, string> ?? {}),
  };

  if (!skipAuth) {
    const token = getToken();
    if (token) headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${BASE_URL}${path}`, { ...rest, headers });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: res.statusText || 'Unknown error' }));
    let message = res.statusText || 'An error occurred';
    if (typeof errorData.error?.message === 'string') {
      message = errorData.error.message;
    } else if (typeof errorData.detail === 'string') {
      message = errorData.detail;
    } else if (errorData.detail) {
      message = typeof errorData.detail === 'object' ? JSON.stringify(errorData.detail) : String(errorData.detail);
    } else if (errorData.message) {
      message = String(errorData.message);
    }
    throw new Error(message);
  }

  // 204 No Content — return empty
  if (res.status === 204) return {} as T;
  return res.json() as Promise<T>;
}

export const api = {
  getMe: <T>() => request<T>('/auth/me'),

  updateMe: <T>(data: { company_name?: string; password?: string }) =>
    request<T>('/auth/me', {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),

  resetPassword: <T>(data: any) =>
    request<T>('/auth/reset-password', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  get: <T>(path: string, opts?: RequestOptions) =>
    request<T>(path, { method: 'GET', ...opts }),

  post: <T>(path: string, body?: unknown, opts?: RequestOptions) =>
    request<T>(path, { method: 'POST', body: JSON.stringify(body), ...opts }),

  patch: <T>(path: string, body?: unknown, opts?: RequestOptions) =>
    request<T>(path, { method: 'PATCH', body: JSON.stringify(body), ...opts }),

  delete: <T>(path: string, opts?: RequestOptions) =>
    request<T>(path, { method: 'DELETE', ...opts }),
};
