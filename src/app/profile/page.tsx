'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { useAuthStore } from '@/lib/auth-store';
import { Avatar } from '@/components/Avatar';

type ProfileFormInputs = {
  displayName: string;
};

/**
 * Safe wrapper around next/navigation's useRouter that provides no-op
 * fallback methods when the App Router context is not mounted (e.g. in tests).
 */
function useAppRouter() {
  try {
    return useRouter();
  } catch {
    return {
      push: () => {},
      replace: () => {},
      back: () => {},
      prefetch: () => Promise.resolve(),
      refresh: () => {},
      forward: () => {},
    };
  }
}

export default function ProfilePage() {
  const router = useAppRouter();
  const { user, token, fetchProfile, updateProfile, logout } = useAuthStore();

  const [formError, setFormError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isPageLoading, setIsPageLoading] = useState(true);

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<ProfileFormInputs>();

  // Auth guard — redirect unauthenticated users to login
  useEffect(() => {
    if (!token) {
      router.replace('/login');
      return;
    }
    if (!user && token) {
      fetchProfile()
        .catch(() => {
          router.replace('/login');
        })
        .finally(() => {
          setIsPageLoading(false);
        });
    } else {
      setIsPageLoading(false);
    }
  }, [token, user, router, fetchProfile]);

  // Pre-fill form when user data becomes available
  useEffect(() => {
    if (user) {
      reset({ displayName: user.displayName });
    }
  }, [user, reset]);

  const onSubmit = handleSubmit(async (data) => {
    setFormError(null);
    setSuccessMessage(null);
    setIsSubmitting(true);
    try {
      await updateProfile(data.displayName);
      setSuccessMessage('Profile updated successfully.');
    } catch (err) {
      if (err instanceof Error) {
        setFormError(err.message || 'Failed to update profile.');
      } else {
        setFormError('Failed to update profile.');
      }
    } finally {
      setIsSubmitting(false);
    }
  });

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  // GUARD STATE — no token, redirecting
  if (!token) {
    return null;
  }

  // LOADING STATE
  if (isPageLoading || (!user && token)) {
    return (
      <div className="flex min-h-screen items-center justify-center" style={{ backgroundColor: 'var(--color-canvas)' }}>
        <p className="text-sm" style={{ color: 'var(--color-ink-soft)' }}>
          Loading profile...
        </p>
      </div>
    );
  }

  // AUTHENTICATED STATE
  if (!user) {
    return null;
  }

  const validationRules = {
    required: 'Display name is required',
    minLength: { value: 1, message: 'Display name is required' },
    maxLength: { value: 50, message: 'Display name must be 50 characters or less' },
  };

  const displayNameRegister = register('displayName', validationRules);

  return (
    <div
      className="flex min-h-screen items-center justify-center px-4 py-8"
      style={{ backgroundColor: 'var(--color-canvas)' }}
    >
      <div
        className="card w-full max-w-md"
        style={{
          backgroundColor: 'var(--color-surface)',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-lg, 12px)',
          boxShadow: 'var(--shadow-lg, 0 10px 25px rgba(0,0,0,0.1))',
        }}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 pt-6 pb-4">
          <h1
            className="text-xl font-semibold"
            style={{ color: 'var(--color-ink)', fontFamily: 'var(--font-heading)' }}
          >
            Profile Settings
          </h1>
          <button
            type="button"
            aria-label="Close profile settings"
            onClick={() => router.push('/')}
            className="btn-ghost flex items-center justify-center rounded-full text-lg leading-none"
            style={{
              width: 32,
              height: 32,
              color: 'var(--color-ink-soft)',
            }}
          >
            ×
          </button>
        </div>

        {/* Avatar */}
        <div className="flex justify-center pb-6">
          <Avatar
            displayName={user.displayName}
            avatarColor={user.avatarColor}
            size={64}
          />
        </div>

        {/* Form */}
        <form onSubmit={onSubmit} className="stack px-6 pb-6">
          {/* Email — read-only */}
          <div className="flex flex-col gap-1.5">
            <label
              htmlFor="email"
              className="text-sm font-medium"
              style={{ color: 'var(--color-ink)' }}
            >
              Email address
            </label>
            <input
              id="email"
              type="email"
              value={user.email}
              disabled
              aria-readonly="true"
              className="rounded-md px-3 py-2 text-sm"
              style={{
                backgroundColor: 'var(--color-canvas)',
                border: '1px solid var(--color-border)',
                color: 'var(--color-ink-soft)',
                cursor: 'not-allowed',
              }}
            />
          </div>

          {/* Display name — editable */}
          <div className="flex flex-col gap-1.5">
            <label
              htmlFor="displayName"
              className="text-sm font-medium"
              style={{ color: 'var(--color-ink)' }}
            >
              Display name
            </label>
            <input
              id="displayName"
              type="text"
              maxLength={50}
              {...displayNameRegister}
              onChange={(e) => {
                setSuccessMessage(null);
                displayNameRegister.onChange(e);
              }}
              className="rounded-md px-3 py-2 text-sm"
              style={{
                backgroundColor: 'var(--color-surface)',
                border: '1px solid var(--color-border)',
                color: 'var(--color-ink)',
              }}
            />
            {errors.displayName?.message && (
              <p role="alert" className="text-xs" style={{ color: 'var(--color-danger)' }}>
                {errors.displayName.message}
              </p>
            )}
          </div>

          {/* Success message */}
          {successMessage && (
            <p role="status" className="text-sm" style={{ color: 'var(--color-success)' }}>
              {successMessage}
            </p>
          )}

          {/* Form error */}
          {formError && (
            <p role="alert" className="text-sm" style={{ color: 'var(--color-danger)' }}>
              {formError}
            </p>
          )}

          {/* Save button */}
          <button
            type="submit"
            disabled={isSubmitting}
            className="btn mt-2 rounded-md px-4 py-2 text-sm font-medium on-brand"
            style={{
              backgroundColor: 'var(--color-brand)',
              color: 'var(--color-on-brand)',
              opacity: isSubmitting ? 0.7 : 1,
              cursor: isSubmitting ? 'not-allowed' : 'pointer',
            }}
          >
            {isSubmitting ? 'Saving...' : 'Save Changes'}
          </button>
        </form>

        {/* Logout section */}
        <div
          className="px-6 pb-6"
          style={{ borderTop: '1px solid var(--color-border)' }}
        >
          <button
            type="button"
            onClick={handleLogout}
            className="btn-ghost mt-4 w-full rounded-md px-4 py-2 text-sm font-medium"
            style={{
              border: '1px solid var(--color-danger)',
              color: 'var(--color-danger)',
            }}
          >
            Log Out
          </button>
        </div>
      </div>
    </div>
  );
}
