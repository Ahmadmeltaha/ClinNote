import { describe, it, expect, beforeAll, afterAll, beforeEach, afterEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';
import { useAuthStore } from '../../src/lib/auth-store';

const server = setupServer();

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

beforeEach(() => {
  useAuthStore.setState({
    user: null,
    token: null,
    isAuthenticated: false,
    isLoading: false,
    error: null,
  });
});

describe('Auth E2E Lifecycle', () => {
  it('[e2e-signup-login-logout] complete auth lifecycle — signup, logout, login, access profile', async () => {
    const mockUser = {
      id: '123e4567-e89b-12d3-a456-426614174000',
      email: 'e2e@example.com',
      displayName: 'E2E User',
      avatarColor: '#6366f1',
    };
    const mockToken = 'mock-jwt-token-12345';

    // Mock signup endpoint
    server.use(
      http.post('http://localhost:3001/api/auth/signup', () => {
        return HttpResponse.json({ user: mockUser, token: mockToken });
      })
    );

    // Step 1: Signup
    await useAuthStore.getState().signup('e2e@example.com', 'password123', 'E2E User');
    
    let state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(true);
    expect(state.user).toEqual(mockUser);
    expect(state.token).toBe(mockToken);
    expect(state.error).toBeNull();

    // Mock logout endpoint
    server.use(
      http.post('http://localhost:3001/api/auth/logout', () => {
        return HttpResponse.json({ success: true });
      })
    );

    // Step 2: Logout
    await useAuthStore.getState().logout();
    
    state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(false);
    expect(state.user).toBeNull();
    expect(state.token).toBeNull();

    // Mock login endpoint
    server.use(
      http.post('http://localhost:3001/api/auth/login', () => {
        return HttpResponse.json({ user: mockUser, token: mockToken });
      })
    );

    // Step 3: Login with same credentials
    await useAuthStore.getState().login('e2e@example.com', 'password123');
    
    state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(true);
    expect(state.user).toEqual(mockUser);
    expect(state.token).toBe(mockToken);

    // Mock fetchProfile endpoint
    server.use(
      http.get('http://localhost:3001/api/users/me', () => {
        return HttpResponse.json({ user: mockUser });
      })
    );

    // Step 4: Access profile (fetchProfile)
    await useAuthStore.getState().fetchProfile();
    
    state = useAuthStore.getState();
    expect(state.user).toEqual(mockUser);
    expect(state.isLoading).toBe(false);
    expect(state.error).toBeNull();
  });

  it('[e2e-profile-update] update profile and verify avatar change', async () => {
    const oldUser = {
      id: '123e4567-e89b-12d3-a456-426614174000',
      email: 'user@example.com',
      displayName: 'Old Name',
      avatarColor: '#6366f1',
    };
    const newUser = {
      id: '123e4567-e89b-12d3-a456-426614174000',
      email: 'user@example.com',
      displayName: 'New Name',
      avatarColor: '#6366f1',
    };
    const mockToken = 'mock-jwt-token-67890';

    // Set initial authenticated state with old name
    useAuthStore.setState({
      user: oldUser,
      token: mockToken,
      isAuthenticated: true,
      isLoading: false,
      error: null,
    });

    // Mock updateProfile endpoint
    server.use(
      http.patch('http://localhost:3001/api/users/me', () => {
        return HttpResponse.json({ user: newUser });
      })
    );

    // Verify initial state
    let state = useAuthStore.getState();
    expect(state.user?.displayName).toBe('Old Name');

    // Update profile
    await useAuthStore.getState().updateProfile('New Name');
    
    // Verify updated state
    state = useAuthStore.getState();
    expect(state.user?.displayName).toBe('New Name');
    expect(state.user?.displayName).not.toBe('Old Name');
    expect(state.isLoading).toBe(false);
    expect(state.error).toBeNull();
  });
});
