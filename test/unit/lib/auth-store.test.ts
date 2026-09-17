import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useAuthStore } from '../../../src/lib/auth-store';

vi.mock('../../../src/lib/api-client', () => ({
  apiClient: {
    post: vi.fn(),
    get: vi.fn(),
    patch: vi.fn(),
  },
  ApiError: class ApiError extends Error {
    status: number;
    data: unknown;
    constructor(status: number, data: unknown) {
      super(`API request failed with status ${status}`);
      this.status = status;
      this.data = data;
    }
  },
}));

import { apiClient } from '../../../src/lib/api-client';
const mockedApiClient = vi.mocked(apiClient);

describe('auth-store', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    useAuthStore.setState({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
    });
  });

  it('[store-token-on-login] stores token after successful login', async () => {
    const mockUser = {
      id: '550e8400-e29b-41d4-a716-446655440000',
      email: 'john@example.com',
      displayName: 'John Doe',
      avatarColor: '#FF5733',
    };
    const mockToken =
      'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiI1NTBlODQwMC1lMjliLTQxZDQtYTcxNi00NDY2NTU0NDAwMDAifQ.signature';

    mockedApiClient.post.mockResolvedValue({
      user: mockUser,
      token: mockToken,
    });

    await useAuthStore.getState().login('john@example.com', 'securePass123');

    const state = useAuthStore.getState();
    expect(state.token).toBe(mockToken);
    expect(state.user).toEqual(mockUser);
    expect(state.isAuthenticated).toBe(true);
    expect(localStorage.getItem('auth-token')).toBe(mockToken);
  });

  it('[clear-token-on-logout] clears token on logout', async () => {
    const mockToken =
      'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiI1NTBlODQwMC1lMjliLTQxZDQtYTcxNi00NDY2NTU0NDAwMDAifQ.signature';
    localStorage.setItem('auth-token', mockToken);
    useAuthStore.setState({
      token: mockToken,
      isAuthenticated: true,
      user: {
        id: '550e8400-e29b-41d4-a716-446655440000',
        email: 'john@example.com',
        displayName: 'John Doe',
        avatarColor: '#FF5733',
      },
    });

    mockedApiClient.post.mockResolvedValue({ success: true });

    await useAuthStore.getState().logout();

    const state = useAuthStore.getState();
    expect(state.token).toBeNull();
    expect(state.user).toBeNull();
    expect(state.isAuthenticated).toBe(false);
    expect(localStorage.getItem('auth-token')).toBeNull();
  });
});
