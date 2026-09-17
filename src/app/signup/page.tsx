'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { useAuthStore } from '@/lib/auth-store';
import { ApiError } from '@/lib/api-client';

type SignupFormInputs = {
  displayName: string;
  email: string;
  password: string;
};

export default function SignupPage() {
  const router = useRouter();
  const { signup, clearError } = useAuthStore();
  const [formError, setFormError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
  } = useForm<SignupFormInputs>();

  useEffect(() => {
    const subscription = watch(() => {
      setFormError(null);
    });
    return () => subscription.unsubscribe();
  }, [watch]);

  const onSubmit = handleSubmit(async (data) => {
    setFormError(null);
    setIsSubmitting(true);
    clearError();
    try {
      await signup(data.email, data.password, data.displayName);
      router.push('/profile');
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setFormError('An account with this email already exists.');
      } else if (err instanceof Error) {
        setFormError(err.message || 'An unexpected error occurred.');
      } else {
        setFormError('An unexpected error occurred.');
      }
    } finally {
      setIsSubmitting(false);
    }
  });

  return (
    <div
      className="flex min-h-screen items-center justify-center px-4"
      style={{ backgroundColor: 'var(--color-canvas)' }}
    >
      <div className="w-full max-w-md">
        <div
          className="card"
          style={{
            backgroundColor: 'var(--color-surface)',
            borderColor: 'var(--color-border)',
          }}
        >
          <h1
            className="mb-6 text-center text-2xl font-bold"
            style={{
              fontFamily: 'var(--font-heading)',
              color: 'var(--color-ink)',
            }}
          >
            Welcome to Chat
          </h1>

          {/* Tab toggle */}
          <div
            className="mb-6 flex border-b"
            style={{ borderColor: 'var(--color-border)' }}
          >
            <Link
              href="/login"
              className="flex-1 py-2 text-center text-sm font-medium"
              style={{ color: 'var(--color-ink-soft)' }}
            >
              Log In
            </Link>
            <span
              className="flex-1 border-b-2 py-2 text-center text-sm font-medium"
              style={{
                color: 'var(--color-accent)',
                borderColor: 'var(--color-accent)',
              }}
            >
              Sign Up
            </span>
          </div>

          <form onSubmit={onSubmit} className="stack">
            {/* Display name */}
            <div>
              <label
                htmlFor="displayName"
                className="mb-1 block text-sm font-medium"
                style={{ color: 'var(--color-ink)' }}
              >
                Display name
              </label>
              <input
                id="displayName"
                type="text"
                autoComplete="name"
                maxLength={50}
                {...register('displayName', {
                  required: 'Display name is required',
                  minLength: { value: 1, message: 'Display name is required' },
                  maxLength: {
                    value: 50,
                    message: 'Display name must be 50 characters or less',
                  },
                })}
                className="w-full rounded-md border px-3 py-2 text-sm"
                style={{
                  borderColor: 'var(--color-border)',
                  backgroundColor: 'var(--color-surface)',
                  color: 'var(--color-ink)',
                }}
              />
              {errors.displayName?.message && (
                <p
                  role="alert"
                  className="mt-1 text-sm"
                  style={{ color: 'var(--color-danger)' }}
                >
                  {errors.displayName.message}
                </p>
              )}
            </div>

            {/* Email */}
            <div>
              <label
                htmlFor="email"
                className="mb-1 block text-sm font-medium"
                style={{ color: 'var(--color-ink)' }}
              >
                Email address
              </label>
              <input
                id="email"
                type="email"
                autoComplete="email"
                {...register('email', {
                  required: 'Email is required',
                  pattern: {
                    value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                    message: 'Invalid email format',
                  },
                })}
                className="w-full rounded-md border px-3 py-2 text-sm"
                style={{
                  borderColor: 'var(--color-border)',
                  backgroundColor: 'var(--color-surface)',
                  color: 'var(--color-ink)',
                }}
              />
              {errors.email?.message && (
                <p
                  role="alert"
                  className="mt-1 text-sm"
                  style={{ color: 'var(--color-danger)' }}
                >
                  {errors.email.message}
                </p>
              )}
            </div>

            {/* Password */}
            <div>
              <label
                htmlFor="password"
                className="mb-1 block text-sm font-medium"
                style={{ color: 'var(--color-ink)' }}
              >
                Password
              </label>
              <input
                id="password"
                type="password"
                autoComplete="new-password"
                {...register('password', {
                  required: 'Password is required',
                  minLength: {
                    value: 8,
                    message: 'Password must be at least 8 characters',
                  },
                })}
                className="w-full rounded-md border px-3 py-2 text-sm"
                style={{
                  borderColor: 'var(--color-border)',
                  backgroundColor: 'var(--color-surface)',
                  color: 'var(--color-ink)',
                }}
              />
              {errors.password?.message && (
                <p
                  role="alert"
                  className="mt-1 text-sm"
                  style={{ color: 'var(--color-danger)' }}
                >
                  {errors.password.message}
                </p>
              )}
            </div>

            {/* Submit button */}
            <button
              type="submit"
              disabled={isSubmitting}
              className="btn on-accent w-full disabled:opacity-60"
            >
              {isSubmitting ? 'Creating account...' : 'Create Account'}
            </button>

            {/* Form error */}
            {formError && (
              <p
                role="alert"
                className="text-sm"
                style={{ color: 'var(--color-danger)' }}
              >
                {formError}
              </p>
            )}
          </form>

          {/* Footer link */}
          <p
            className="mt-6 text-center text-sm"
            style={{ color: 'var(--color-ink-soft)' }}
          >
            Already have an account?{' '}
            <Link
              href="/login"
              className="font-medium underline"
              style={{ color: 'var(--color-accent)' }}
            >
              Log in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
