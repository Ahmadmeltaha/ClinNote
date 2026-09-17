import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { apiClient, type AuthUser } from '@/lib/api-client';

export interface AuthState {
  user: AuthUser | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, displayName: string) => Promise<void>;
  logout: () => Promise<void>;
  fetchProfile: () => Promise<void>;
  updateProfile: (displayName: string) => Promise<void>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      login: async (email: string, password: string): Promise<void> => {
        set({ isLoading: true, error: null });
        try {
          const { user, token } = await apiClient.post<{ user: AuthUser; token: string }>(
            '/api/auth/login',
            { email, password },
          );
          if (typeof window !== 'undefined') {
            window.localStorage.setItem('auth-token', token);
          }
          set({ user, token, isAuthenticated: true, isLoading: false });
        } catch (err: unknown) {
          const message = err instanceof Error ? err.message : 'Login failed';
          set({ error: message, isLoading: false });
        }
      },

      signup: async (email: string, password: string, displayName: string): Promise<void> => {
        set({ isLoading: true, error: null });
        try {
          const { user, token } = await apiClient.post<{ user: AuthUser; token: string }>(
            '/api/auth/signup',
            { email, password, displayName },
          );
          if (typeof window !== 'undefined') {
            window.localStorage.setItem('auth-token', token);
          }
          set({ user, token, isAuthenticated: true, isLoading: false });
        } catch (err: unknown) {
          const message = err instanceof Error ? err.message : 'Signup failed';
          set({ error: message, isLoading: false });
        }
      },

      logout: async (): Promise<void> => {
        try {
          await apiClient.post('/api/auth/logout');
        } finally {
          if (typeof window !== 'undefined') {
            window.localStorage.removeItem('auth-token');
          }
          set({ user: null, token: null, isAuthenticated: false, isLoading: false });
        }
      },

      fetchProfile: async (): Promise<void> => {
        set({ isLoading: true, error: null });
        try {
          const { user } = await apiClient.get<{ user: AuthUser }>('/api/users/me');
          set({ user, isLoading: false });
        } catch (err: unknown) {
          const message = err instanceof Error ? err.message : 'Failed to fetch profile';
          set({ error: message, isLoading: false });
        }
      },

      updateProfile: async (displayName: string): Promise<void> => {
        set({ isLoading: true, error: null });
        try {
          const { user } = await apiClient.patch<{ user: AuthUser }>('/api/users/me', {
            displayName,
          });
          set({ user, isLoading: false });
        } catch (err: unknown) {
          const message = err instanceof Error ? err.message : 'Failed to update profile';
          set({ error: message, isLoading: false });
        }
      },

      clearError: (): void => {
        set({ error: null });
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
      onRehydrateStorage: () => (state) => {
        if (typeof window !== 'undefined') {
          if (state?.token) {
            window.localStorage.setItem('auth-token', state.token);
          } else {
            window.localStorage.removeItem('auth-token');
          }
        }
      },
    },
  ),
);
