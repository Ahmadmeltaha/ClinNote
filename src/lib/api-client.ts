export interface AuthUser {
  id: string;
  email: string;
  displayName: string;
  avatarColor: string;
}

export class ApiError extends Error {
  readonly status: number;
  readonly data: unknown;

  constructor(status: number, data: unknown) {
    super(`API request failed with status ${status}`);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

const BASE_URL =
  (typeof process !== 'undefined' && process.env?.NEXT_PUBLIC_API_URL) ||
  'http://localhost:3001';

function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return window.localStorage.getItem('auth-token');
}

function handle401(): void {
  if (typeof window !== 'undefined') {
    window.localStorage.removeItem('auth-token');
    window.location.href = '/login';
  }
}

async function request<T = unknown>(
  method: string,
  path: string,
  body?: unknown,
): Promise<T> {
  if (!path.startsWith('/')) {
    throw new Error(`path must start with '/', got: ${path}`);
  }

  const url = `${BASE_URL}${path}`;

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  const token = getToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const init: RequestInit = {
    method,
    headers,
  };

  if (body !== undefined) {
    init.body = JSON.stringify(body);
  }

  const response = await fetch(url, init);

  if (response.status === 401) {
    handle401();
    // Throw after triggering redirect so callers can catch if needed
    const data = await response.json().catch(() => ({}));
    throw new ApiError(401, data);
  }

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new ApiError(response.status, data);
  }

  return data as T;
}

export const apiClient = {
  get<T = unknown>(path: string): Promise<T> {
    return request<T>('GET', path);
  },

  post<T = unknown>(path: string, body?: unknown): Promise<T> {
    return request<T>('POST', path, body);
  },

  patch<T = unknown>(path: string, body?: unknown): Promise<T> {
    return request<T>('PATCH', path, body);
  },
};
