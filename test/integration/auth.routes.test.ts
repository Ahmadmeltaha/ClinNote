import { describe, it, expect, beforeEach, vi } from 'vitest';
import request from 'supertest';
import { Hono } from 'hono';
import { authRoutes } from '@/routes/auth.routes';
import {
  createExistingUserWithHash,
  createValidAuthToken,
  validUserCredentials,
  existingUser
} from '@/test/fixtures/auth-fixtures';
import {
  mockDbSelectReturns,
  mockDbInsertReturns,
  mockDbUpdateReturns,
  mockDbSelectEmpty
} from '@/test/mocks/backend-mocks';

vi.mock('@/db/index', () => ({
  db: {
    select: vi.fn(),
    insert: vi.fn(),
    update: vi.fn(),
  },
}));

vi.mock('@/lib/auth-utils', () => ({
  hashPassword: vi.fn(),
  verifyPassword: vi.fn(),
  generateToken: vi.fn(),
}));

vi.mock('@/lib/avatar-utils', () => ({
  getAvatarColor: vi.fn().mockReturnValue('#6366f1'),
}));

import { db } from '@/db/index';
import { hashPassword, verifyPassword, generateToken } from '@/lib/auth-utils';

const app = new Hono();
app.route('/api/auth', authRoutes);

describe('Auth Routes Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('POST /api/auth/signup', () => {
    it('[TC-signup-valid] creates account with valid data', async () => {
      mockDbSelectEmpty();
      const mockUser = createExistingUserWithHash('user-123', 'test@example.com', 'Test User');
      mockDbInsertReturns(mockUser);
      mockDbUpdateReturns(mockUser);
      vi.mocked(hashPassword).mockResolvedValue('hashed-password');
      vi.mocked(generateToken).mockResolvedValue('valid-token');

      const response = await request(app.fetch)
        .post('/api/auth/signup')
        .send({
          email: 'test@example.com',
          password: 'password123',
          displayName: 'Test User'
        });

      expect(response.status).toBe(200);
      expect(response.body).toHaveProperty('user');
      expect(response.body).toHaveProperty('token');
      expect(response.body.user).toHaveProperty('id');
      expect(response.body.user).toHaveProperty('email', 'test@example.com');
      expect(response.body.user).toHaveProperty('displayName', 'Test User');
      expect(response.body.user).toHaveProperty('avatarColor');
      expect(response.body.token).toBe('valid-token');
    });

    it('[TC-signup-duplicate-email] rejects duplicate email', async () => {
      const existingUser = createExistingUserWithHash('existing-id', 'existing@example.com', 'Existing User');
      mockDbSelectReturns([existingUser]);

      const response = await request(app.fetch)
        .post('/api/auth/signup')
        .send({
          email: 'existing@example.com',
          password: 'password123',
          displayName: 'Test'
        });

      expect(response.status).toBe(409);
      expect(response.body).toHaveProperty('error');
      expect(response.body.error).toBe('An account with this email already exists.');
    });

    it('[TC-signup-invalid-email] rejects invalid email format', async () => {
      const response = await request(app.fetch)
        .post('/api/auth/signup')
        .send({
          email: 'not-an-email',
          password: 'password123',
          displayName: 'Test'
        });

      expect(response.status).toBe(400);
      expect(response.body).toHaveProperty('success', false);
    });

    it('[TC-signup-short-password] rejects password under 8 chars', async () => {
      const response = await request(app.fetch)
        .post('/api/auth/signup')
        .send({
          email: 'test@example.com',
          password: 'short',
          displayName: 'Test'
        });

      expect(response.status).toBe(400);
      expect(response.body).toHaveProperty('success', false);
    });

    it('[TC-signup-long-displayname] rejects displayName over 50 chars', async () => {
      const longName = 'a'.repeat(51);
      const response = await request(app.fetch)
        .post('/api/auth/signup')
        .send({
          email: 'test@example.com',
          password: 'password123',
          displayName: longName
        });

      expect(response.status).toBe(400);
      expect(response.body).toHaveProperty('success', false);
    });

    it('[TC-signup-no-password-in-response] response excludes password hash', async () => {
      mockDbSelectEmpty();
      const mockUser = createExistingUserWithHash('user-456', 'test@example.com', 'Test');
      mockDbInsertReturns(mockUser);
      mockDbUpdateReturns(mockUser);
      vi.mocked(hashPassword).mockResolvedValue('hashed-password');
      vi.mocked(generateToken).mockResolvedValue('valid-token');

      const response = await request(app.fetch)
        .post('/api/auth/signup')
        .send({
          email: 'test@example.com',
          password: 'password123',
          displayName: 'Test'
        });

      expect(response.status).toBe(200);
      expect(response.body.user).not.toHaveProperty('passwordHash');
      expect(response.body.user).toHaveProperty('id');
      expect(response.body.user).toHaveProperty('email');
      expect(response.body.user).toHaveProperty('displayName');
      expect(response.body.user).toHaveProperty('avatarColor');
    });
  });

  describe('POST /api/auth/login', () => {
    it('[TC-login-valid] authenticates with correct credentials', async () => {
      const existingUser = createExistingUserWithHash('user-789', 'user@example.com', 'User Name');
      mockDbSelectReturns([existingUser]);
      vi.mocked(verifyPassword).mockResolvedValue(true);
      vi.mocked(generateToken).mockResolvedValue('valid-token');

      const response = await request(app.fetch)
        .post('/api/auth/login')
        .send({
          email: 'user@example.com',
          password: 'password123'
        });

      expect(response.status).toBe(200);
      expect(response.body).toHaveProperty('user');
      expect(response.body).toHaveProperty('token');
      expect(response.body.user).toHaveProperty('id');
      expect(response.body.user).toHaveProperty('email', 'user@example.com');
      expect(response.body.user).toHaveProperty('displayName', 'User Name');
      expect(response.body.user).toHaveProperty('avatarColor');
      expect(response.body.token).toBe('valid-token');
    });

    it('[TC-login-invalid-email] rejects unregistered email', async () => {
      mockDbSelectEmpty();

      const response = await request(app.fetch)
        .post('/api/auth/login')
        .send({
          email: 'unknown@example.com',
          password: 'password123'
        });

      expect(response.status).toBe(401);
      expect(response.body).toHaveProperty('error');
      expect(response.body.error).toBe('Invalid email or password.');
    });

    it('[TC-login-wrong-password] rejects incorrect password', async () => {
      const existingUser = createExistingUserWithHash('user-999', 'user@example.com', 'User Name');
      mockDbSelectReturns([existingUser]);
      vi.mocked(verifyPassword).mockResolvedValue(false);

      const response = await request(app.fetch)
        .post('/api/auth/login')
        .send({
          email: 'user@example.com',
          password: 'wrongpass'
        });

      expect(response.status).toBe(401);
      expect(response.body).toHaveProperty('error');
      expect(response.body.error).toBe('Invalid email or password.');
    });
  });

  describe('POST /api/auth/logout', () => {
    it('[TC-logout-valid] terminates session', async () => {
      const validToken = createValidAuthToken('user-123');

      const response = await request(app.fetch)
        .post('/api/auth/logout')
        .set('Authorization', `Bearer ${validToken}`);

      expect(response.status).toBe(200);
      expect(response.body).toHaveProperty('success', true);
    });

    it('[TC-logout-no-auth] rejects logout without auth', async () => {
      const response = await request(app.fetch)
        .post('/api/auth/logout');

      expect(response.status).toBe(401);
      expect(response.body).toHaveProperty('error');
    });
  });
});
