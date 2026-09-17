import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ProfilePage from '@/app/profile/page';
import { useAuthStore } from '@/lib/auth-store';

// Mock next/navigation
const mockPush = vi.fn();
const mockReplace = vi.fn();
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
    replace: mockReplace,
  }),
}));

// Mock the auth store
vi.mock('@/lib/auth-store', () => ({
  useAuthStore: vi.fn(),
}));

// Mock the Avatar component
vi.mock('@/components/Avatar', () => ({
  Avatar: ({ displayName, avatarColor }: { displayName: string; avatarColor: string }) => (
    <div data-testid="avatar" style={{ backgroundColor: avatarColor }}>
      {displayName}
    </div>
  ),
}));

describe('ProfilePage Integration', () => {
  const mockFetchProfile = vi.fn();
  const mockUpdateProfile = vi.fn();
  const mockLogout = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    mockPush.mockClear();
    mockReplace.mockClear();
  });

  it('[TC-24] displays user profile information', async () => {
    const mockUser = {
      id: '550e8400-e29b-41d4-a716-446655440000',
      email: 'user@example.com',
      displayName: 'Test User',
      avatarColor: '#E53E3E',
      passwordHash: 'hashedpassword',
      createdAt: new Date('2024-01-01'),
      updatedAt: new Date('2024-01-01'),
    };

    (useAuthStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      user: mockUser,
      token: 'valid-token',
      fetchProfile: mockFetchProfile,
      updateProfile: mockUpdateProfile,
      logout: mockLogout,
    });

    render(<ProfilePage />);

    await waitFor(() => {
      expect(screen.getByDisplayValue('Test User')).toBeInTheDocument();
    });

    expect(screen.getByDisplayValue('user@example.com')).toBeInTheDocument();
    expect(screen.getByDisplayValue('user@example.com')).toBeDisabled();
    expect(screen.getByTestId('avatar')).toBeInTheDocument();
  });

  it('[TC-25] submits display name update', async () => {
    const mockUser = {
      id: '550e8400-e29b-41d4-a716-446655440000',
      email: 'user@example.com',
      displayName: 'Old Name',
      avatarColor: '#E53E3E',
      passwordHash: 'hashedpassword',
      createdAt: new Date('2024-01-01'),
      updatedAt: new Date('2024-01-01'),
    };

    const updatedUser = {
      ...mockUser,
      displayName: 'Updated Name',
    };

    mockUpdateProfile.mockResolvedValue(updatedUser);

    (useAuthStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      user: mockUser,
      token: 'valid-token',
      fetchProfile: mockFetchProfile,
      updateProfile: mockUpdateProfile,
      logout: mockLogout,
    });

    const user = userEvent.setup();
    render(<ProfilePage />);

    await waitFor(() => {
      expect(screen.getByDisplayValue('Old Name')).toBeInTheDocument();
    });

    const displayNameInput = screen.getByDisplayValue('Old Name');
    await user.clear(displayNameInput);
    await user.type(displayNameInput, 'Updated Name');

    const submitButton = screen.getByRole('button', { name: /save changes/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(mockUpdateProfile).toHaveBeenCalledWith('Updated Name');
    });

    await waitFor(() => {
      expect(screen.getByText(/profile updated successfully/i)).toBeInTheDocument();
    });
  });

  it('[TC-26] logout button calls logout endpoint', async () => {
    const mockUser = {
      id: '550e8400-e29b-41d4-a716-446655440000',
      email: 'user@example.com',
      displayName: 'Test User',
      avatarColor: '#E53E3E',
      passwordHash: 'hashedpassword',
      createdAt: new Date('2024-01-01'),
      updatedAt: new Date('2024-01-01'),
    };

    mockLogout.mockResolvedValue(undefined);

    (useAuthStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      user: mockUser,
      token: 'valid-token',
      fetchProfile: mockFetchProfile,
      updateProfile: mockUpdateProfile,
      logout: mockLogout,
    });

    const user = userEvent.setup();
    render(<ProfilePage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /log out/i })).toBeInTheDocument();
    });

    const logoutButton = screen.getByRole('button', { name: /log out/i });
    await user.click(logoutButton);

    await waitFor(() => {
      expect(mockLogout).toHaveBeenCalled();
    });

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/login');
    });
  });
});
