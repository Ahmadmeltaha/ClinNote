import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';
import { afterAll, afterEach, beforeAll } from 'vitest';

export const handlers = {
  signupSuccess: http.post('/api/auth/signup', () => {
    return HttpResponse.json(
      {
        user: {
          id: '550e8400-e29b-41d4-a716-446655440000',
          email: 'new@example.com',
          displayName: 'Test User',
          avatarColor: '#E53E3E',
        },
        token: 'mock-jwt-token',
      },
      { status: 200 }
    );
  }),

  signupDuplicateEmail: http.post('/api/auth/signup', () => {
    return HttpResponse.json(
      { error: 'An account with this email already exists.' },
      { status: 409 }
    );
  }),

  loginSuccess: http.post('/api/auth/login', () => {
    return HttpResponse.json(
      {
        user: {
          id: '550e8400-e29b-41d4-a716-446655440000',
          email: 'user@example.com',
          displayName: 'Test User',
          avatarColor: '#E53E3E',
        },
        token: 'mock-jwt-token',
      },
      { status: 200 }
    );
  }),

  loginInvalidCredentials: http.post('/api/auth/login', () => {
    return HttpResponse.json(
      { error: 'Invalid email or password.' },
      { status: 401 }
    );
  }),

  logoutSuccess: http.post('/api/auth/logout', () => {
    return HttpResponse.json({ success: true }, { status: 200 });
  }),

  getProfileSuccess: http.get('/api/users/me', () => {
    return HttpResponse.json(
      {
        id: '550e8400-e29b-41d4-a716-446655440000',
        email: 'user@example.com',
        displayName: 'Test User',
        avatarColor: '#E53E3E',
        createdAt: '2024-01-01T00:00:00.000Z',
      },
      { status: 200 }
    );
  }),

  updateProfileSuccess: http.patch('/api/users/me', async ({ request }) => {
    const body = (await request.json()) as { displayName?: string };
    return HttpResponse.json(
      {
        id: '550e8400-e29b-41d4-a716-446655440000',
        email: 'user@example.com',
        displayName: body.displayName || 'Test User',
        avatarColor: '#E53E3E',
        updatedAt: new Date().toISOString(),
      },
      { status: 200 }
    );
  }),
};

export function setupMockServer(...initialHandlers: Array<ReturnType<typeof http.get | typeof http.post | typeof http.patch>>) {
  const server = setupServer(...initialHandlers);

  beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
  afterEach(() => server.resetHandlers());
  afterAll(() => server.close());

  return server;
}
