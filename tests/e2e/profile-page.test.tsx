import { describe, it, expect, beforeAll, afterAll, afterEach, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';
import '@testing-library/jest-dom';
import ProfilePage from '@/app/profile/page';
import { existingUser, authToken } from '@/tests/fixtures/auth';
import { authHandlers } from '@/tests/mocks/auth-handlers';

const server = setupServer(...authHandlers);

describe('Profile Page E2E', () => {
  beforeAll(() => server.listen());
  afterEach(() => server.resetHandlers());
  afterAll(() => server.close());

  beforeEach(() => {
    window.localStorage.setItem('auth-token', authToken);
  });

  it('[e2e-profile-update] update profile and verify avatar change', async () => {
    const user = userEvent.setup();

    // Mock GET /me to return user with "Old Name"
    server.use(
      http.get('*/api/users/me', () => {
        return HttpResponse.json({
          user: {
            id: existingUser.id,
            email: existingUser.email,
            displayName: 'Old Name',
            avatarColor: existingUser.avatarColor,
          },
        });
      }),
      http.patch('*/api/users/me', async () => {
        return HttpResponse.json({
          user: {
            id: existingUser.id,
            email: existingUser.email,
            displayName: 'New Name',
            avatarColor: existingUser.avatarColor,
          },
        });
      })
    );

    render(<ProfilePage />);

    // Wait for profile to load and avatar to appear
    await waitFor(() => {
      expect(screen.getByLabelText(/Avatar for Old Name/i)).toBeInTheDocument();
    });

    // Verify initial avatar shows "ON" (Old Name)
    const initialAvatar = screen.getByLabelText(/Avatar for Old Name/i);
    expect(initialAvatar).toHaveTextContent('ON');

    // Update display name to "New Name"
    const displayNameInput = screen.getByLabelText(/Display name/i);
    await user.clear(displayNameInput);
    await user.type(displayNameInput, 'New Name');

    // Submit the form
    const submitButton = screen.getByRole('button', { name: /Save Changes/i });
    await user.click(submitButton);

    // Wait for success message and avatar to update
    await waitFor(() => {
      expect(screen.getByText(/Profile updated successfully/i)).toBeInTheDocument();
    });

    // Verify avatar now shows "NN" (New Name)
    const updatedAvatar = screen.getByLabelText(/Avatar for New Name/i);
    expect(updatedAvatar).toHaveTextContent('NN');
  });
});