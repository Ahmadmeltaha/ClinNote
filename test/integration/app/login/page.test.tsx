import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import LoginPage from '@/app/login/page';
import { useAuthStore } from '@/lib/auth-store';
import { validUserCredentials } from '../../../fixtures/auth-fixtures';

// Mock next/navigation
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    back: vi.fn(),
  }),
}));

describe('LoginPage Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset auth store state
    useAuthStore.setState({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
    });
  });

  it('[login-form-renders] renders login form fields', () => {
    render(<LoginPage />);
    
    // Check for Email input
    const emailInput = screen.getByLabelText(/email/i);
    expect(emailInput).toBeInTheDocument();
    
    // Check for Password input
    const passwordInput = screen.getByLabelText(/password/i);
    expect(passwordInput).toBeInTheDocument();
    
    // Check for Log In button
    const submitButton = screen.getByRole('button', { name: /log in/i });
    expect(submitButton).toBeInTheDocument();
  });

  it('[login-form-submits] submits credentials on form submit', async () => {
    const user = userEvent.setup();
    const mockLogin = vi.fn();
    
    // Mock the login function
    useAuthStore.setState({ login: mockLogin });
    
    render(<LoginPage />);
    
    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /log in/i });
    
    await user.type(emailInput, validUserCredentials.email);
    await user.type(passwordInput, validUserCredentials.password);
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith(
        validUserCredentials.email,
        validUserCredentials.password
      );
    });
  });

  it('[login-form-error] displays error on invalid credentials', async () => {
    const user = userEvent.setup();
    
    // Mock failed login - set error in store
    const mockLogin = vi.fn().mockImplementation(async () => {
      useAuthStore.setState({ error: 'API request failed with status 401' });
    });
    
    useAuthStore.setState({ login: mockLogin });
    
    render(<LoginPage />);
    
    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /log in/i });
    
    await user.type(emailInput, 'wrong@example.com');
    await user.type(passwordInput, 'wrongpassword');
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText(/invalid email or password/i)).toBeInTheDocument();
    });
  });
});
