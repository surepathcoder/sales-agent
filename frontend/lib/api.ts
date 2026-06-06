import { API_URL } from './constants';

type RequestOptions = RequestInit & { token?: string };

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private getHeaders(token?: string): HeadersInit {
    const headers: HeadersInit = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('kijani_token');
      if (stored && !token) headers['Authorization'] = `Bearer ${stored}`;
    }
    return headers;
  }

  async request<T>(path: string, options: RequestOptions = {}): Promise<T> {
    const { token, ...init } = options;
    const res = await fetch(`${this.baseUrl}${path}`, {
      ...init,
      headers: { ...this.getHeaders(token), ...init.headers },
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail?.en || err.detail || 'Request failed');
    }
    return res.json();
  }

  get<T>(path: string, token?: string) {
    return this.request<T>(path, { method: 'GET', token });
  }

  post<T>(path: string, body?: unknown, token?: string) {
    return this.request<T>(path, {
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined,
      token,
    });
  }

  patch<T>(path: string, body: unknown, token?: string) {
    return this.request<T>(path, {
      method: 'PATCH',
      body: JSON.stringify(body),
      token,
    });
  }
}

export const api = new ApiClient(API_URL);
