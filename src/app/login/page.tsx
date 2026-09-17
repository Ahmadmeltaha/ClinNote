'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { useAuthStore } from '@/lib/auth-store';
import { ApiError } from '@/lib/api-client';

type LoginFormInputs = {
  email: string;
  password: string;
};

export default function LoginPage() {
  const router = useRouter();
  const { login, clearError } = useAuthStore();

  const [formError, setFormError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
    setError: setFieldError,
  } = useForm<LoginFormInputs>();

  const emailRef = useRef<HTMLInputElement>(null);
  const passwordRef = useRef<HTMLInputElement>(null);

  // Focus first invalid field on validation error
  const hasShownValidationAlert = useRef(false);
  useEffect(() => {
    if (Object.keys(errors).length > 0 && !hasShownValidationAlert.current) {
      hasShownValidationAlert.current = true;
      if (errors.email) {
        emailRef.current?.focus();
      } else if (errors.password) {
        passwordRef.current?.focus();
      }
    }
    if (Object.keys(errors).length === 0) {
      hasShownValidationAlert.current = false;
    }
  }, [errors]);

  const onSubmit = handleSubmit(async (data) => {
    setFormError(null);
    clearError();
    setIsSubmitting(true);
    try {
      await login(data.email, data.password);
      // The store catches errors internally; check store state for failure
      const storeError = useAuthStore.getState().error;
      if (storeError) {
        if (storeError.includes('401')) {
          setFormError('Invalid email or password.');
        } else {
          setFormError(storeError);
        }
        return;
      }
      router.push('/profile');
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        setFormError('Invalid email or password.');
      } else if (err instanceof Error) {
        setFormError(err.message || 'An unexpected error occurred.');
      } else {
        setFormError('An unexpected error occurred.');
      }
    } finally {
      setIsSubmitting(false);
    }
  });

  const hasErrors = Object.keys(errors).length > 0;

  return (
    <div
      className="flex min-h-screen items-center justify-center px-4"
      style={{ backgroundColor: 'var(--color-canvas)' }}
    >
      <div className="w-full max-w-md">
        {/* Card */}
        <div
          className="card rounded-xl p-8 shadow-md"
          style={{
            backgroundColor: 'var(--color-surface)',
            borderColor: 'var(--color-border)',
          }}
        >
          {/* Page title */}
          <h1
            className="mb-6 text-center text-3xl font-bold"
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
            <span
              className="flex-1 cursor-default pb-3 text-center text-sm font-semibold"
              style={{
                color: 'var(--color-accent)',
                borderBottom: '2px solid var(--color-accent)',
              }}
            >
              Log In
            </span>
            <Link
              href="/signup"
              className="flex-1 pb-3 text-center text-sm font-medium transition-colors hover:opacity-80"
              style={{ color: 'var(--color-ink-soft)' }}
            >
              Sign Up
            </Link>
          </div>

          {/* Form */}
          <form onSubmit={onSubmit} noValidate>
            {/* Validation error summary */}
            {hasErrors && (
              <p
                role="alert"
                className="mb-4 rounded-md px-4 py-3 text-sm"
                style={{
                  backgroundColor: 'var(--color-danger-soft, rgba(220, 38, 38, 0.1))',
                  color: 'var(--color-danger)',
                }}
              >
                Please fix the errors in the form.
              </p>
            )}

            {/* Email field */}
            <div className="mb-4">
              <label
                htmlFor="email"
                className="mb-1.5 block text-sm font-medium"
                style={{
                  fontFamily: 'var(--font-body)',
                  color: 'var(--color-ink)',
                }}
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
                onChange={(e) => {
                  setFormError(null);
                  register('email').onChange(e);
                }}
                ref={(el) => {
                  emailRef.current = el;
                  register('email').ref(el);
                }}
                className="w-full rounded-lg border px-3 py-2 text-sm outline-none transition-colors focus:ring-2"
                style={{
                  backgroundColor: 'var(--color-surface)',
                  borderColor: errors.email ? 'var(--color-danger)' : 'var(--color-border)',
                  color: 'var(--color-ink)',
                  fontFamily: 'var(--font-body)',
                }}
              />
              {errors.email && (
                <p
                  className="mt-1 text-xs"
                  style={{ color: 'var(--color-danger)' }}
                >
                  {errors.email.message}
                </p>
              )}
            </div>

            {/* Password field */}
            <div className="mb-6">
              <label
                htmlFor="password"
                className="mb-1.5 block text-sm font-medium"
                style={{
                  fontFamily: 'var(--font-body)',
                  color: 'var(--color-ink)',
                }}
              >
                Password
              </label>
              <input
                id="password"
                type="password"
                autoComplete="current-password"
                {...register('password', {
                  required: 'Password is required',
                })}
                onChange={(e) => {
                  setFormError(null);
                  register('password').onChange(e);
                }}
                ref={(el) => {
                  passwordRef.current = el;
                  register('password').ref(el);
                }}
                className="w-full rounded-lg border px-3 py-2 text-sm outline-none transition-colors focus:ring-2"
                style={{
                  backgroundColor: 'var(--color-surface)',
                  borderColor: errors.password ? 'var(--color-danger)' : 'var(--color-border)',
                  color: 'var(--color-ink)',
                  fontFamily: 'var(--font-body)',
                }}
              />
              {errors.password && (
                <p
                  className="mt-1 text-xs"
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
              className="btn on-accent w-full rounded-lg px-4 py-2.5 text-sm font-semibold transition-opacity disabled:cursor-not-allowed disabled:opacity-50"
              style={{
                backgroundColor: 'var(--color-accent)',
                color: 'var(--color-on-accent, #fff)',
              }}
            >
              {isSubmitting ? 'Logging in...' : 'Log In'}
            </button>

            {/* Auth error display */}
            {formError && (
              <p
                role="alert"
                className="mt-4 text-sm"
                style={{ color: 'var(--color-danger)' }}
              >
                {formError}
              </p>
            )}
          </form>
        </div>

        {/* Footer link */}
        <p
          className="mt-6 text-center text-sm"
          style={{
            fontFamily: 'var(--font-body)',
            color: 'var(--color-ink-soft)',
          }}
        >
          Don&apos;t have an account?{' '}
          <Link
            href="/signup"
            className="font-medium underline transition-opacity hover:opacity-80"
            style={{ color: 'var(--color-accent)' }}
          >
            Sign up
          </Link>
        </p>
      </div>
    </div>
  );
}
