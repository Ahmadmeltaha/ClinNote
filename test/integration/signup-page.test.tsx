import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeAll, afterAll, afterEach, beforeEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import SignupPage from '@/app/signup/page';
import { setupMockServer } from '@/mocks/frontend-mocks';
import { createSanitizedUser } from '@/fixtures/auth-fixtures';

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    prefetch: vi.fn(),
  }),
}));

const server = setupMockServer();

describe('SignupPage', () => {
  beforeAll(() => server.listen());
  afterEach(() => server.resetHandlers());
  afterAll(() => server.close());

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('[signup-form-renders] renders signup form fields', () => {
    render(<SignupPage />);

    expect(screen.getByLabelText(/display name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^password$/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /create account/i })).toBeInTheDocument();
  });

  it('[signup-form-submits] submits registration data', async () => {
    const user = userEvent.setup();
    let capturedBody: any = null;

    server.use(
      http.post('*/api/auth/signup', async ({ request }) => {
        capturedBody = await request.json();
        return HttpResponse.json({
          user: createSanitizedUser({ displayName: 'Test User', email: 'new@example.com' }),
          token: 'mock-token-123',
        });
      })
    );

    render(<SignupPage />);

    await user.type(screen.getByLabelText(/display name/i), 'Test User');
    await user.type(screen.getByLabelText(/email address/i), 'new@example.com');
    await user.type(screen.getByLabelText(/^password$/i), 'password123');

    await user.click(screen.getByRole('button', { name: /create account/i }));

    await waitFor(() => {
      expect(capturedBody).toEqual({
        email: 'new@example.com',
        password: 'password123',
        displayName: 'Test User',
      });
    });
  });

  it('[signup-form-duplicate-error] displays duplicate email error', async () => {
    const user = userEvent.setup();

    server.use(
      http.post('*/api/auth/signup', () => {
        return HttpResponse.json(
          { error: 'An account with this email already exists.' },
          { status: 409 }
        );
      })
    );

    render(<SignupPage />);

    await user.type(screen.getByLabelText(/display name/i), 'Test User');
    await user.type(screen.getByLabelText(/email address/i), 'existing@example.com');
    await user.type(screen.getByLabelText(/^password$/i), 'password123');

    await user.click(screen.getByRole('button', { name: /create account/i }));

    await waitFor(() => {
      expect(screen.getByText(/an account with this email already exists/i)).toBeInTheDocument();
    });
  });
});
