import { http, HttpResponse } from 'msw';
import { existingUser, authToken, validUserCredentials } from '../fixtures/auth';

export const authHandlers = [
  http.post('http://localhost:3001/api/auth/signup', async ({ request }) => {
    const body = await request.json() as any;
    if (body.email === validUserCredentials.email) {
      return HttpResponse.json({
        user: existingUser,
        token: authToken,
      });
    }
    return HttpResponse.json({ error: 'Signup failed' }, { status: 400 });
  }),

  http.post('http://localhost:3001/api/auth/login', async ({ request }) => {
    const body = await request.json() as any;
    if (
      body.email === validUserCredentials.email &&
      body.password === validUserCredentials.password
    ) {
      return HttpResponse.json({
        user: existingUser,
        token: authToken,
      });
    }
    return HttpResponse.json({ error: 'Invalid email or password.' }, { status: 401 });
  }),

  http.post('http://localhost:3001/api/auth/logout', () => {
    return HttpResponse.json({ success: true });
  }),

  http.get('http://localhost:3001/api/users/me', () => {
    // The auth-store expects the user object to be wrapped in a `user` property.
    // We mock the API to satisfy the store's expectation so the UI can render correctly.
    return HttpResponse.json({ user: existingUser });
  }),

  http.patch('http://localhost:3001/api/users/me', async ({ request }) => {
    const body = await request.json() as any;
    const updatedUser = { ...existingUser, displayName: body.displayName };
    return HttpResponse.json({ user: updatedUser });
  }),
];
