import { describe, it, expect, vi, beforeEach } from 'vitest';
import { Hono } from 'hono';
import { userRoutes } from '@/routes/users.routes';
import { sign } from 'hono/jwt';

// Mock the database
vi.mock('@/db/index', () => ({
  db: {
    select: vi.fn(),
    update: vi.fn(),
  },
}));

// Mock auth utilities
vi.mock('@/lib/auth-utils', () => ({
  verifyToken: vi.fn(),
  generateToken: vi.fn(),
}));

import { db } from '@/db/index';
import { verifyToken } from '@/lib/auth-utils';

const app = new Hono();
app.route('/api/users', userRoutes);

describe('Users Routes Integration', () => {
  const JWT_SECRET = process.env.JWT_SECRET ?? 'dev-secret-change-me';
  const testUserId = '550e8400-e29b-41d4-a716-446655440000';

  beforeEach(() => {
    vi.clearAllMocks();
  });

  async function generateValidToken(userId: string): Promise<string> {
    return await sign({ userId }, JWT_SECRET, 'HS256');
  }

  const mockUser = {
    id: testUserId,
    email: 'user@example.com',
    passwordHash: 'hashedpassword',
    displayName: 'Test User',
    avatarColor: '#E53E3E',
    createdAt: new Date('2024-01-01'),
    updatedAt: new Date('2024-01-01'),
  };

  describe('GET /api/users/me', () => {
    it('[TC-12] returns current user profile', async () => {
      const token = await generateValidToken(testUserId);

      (verifyToken as ReturnType<typeof vi.fn>).mockResolvedValue({ userId: testUserId });

      const mockSelect = vi.fn().mockReturnValue({
        from: vi.fn().mockReturnValue({
          where: vi.fn().mockResolvedValue([mockUser]),
        }),
      });

      (db.select as ReturnType<typeof vi.fn>).mockImplementation(mockSelect);

      const res = await app.request('/api/users/me', {
        method: 'GET',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      expect(res.status).toBe(200);
      const data = await res.json();
      expect(data).toMatchObject({
        id: testUserId,
        email: 'user@example.com',
        displayName: 'Test User',
        avatarColor: '#E53E3E',
      });
      expect(data.createdAt).toBeDefined();
    });

    it('[TC-13] rejects unauthenticated request', async () => {
      const res = await app.request('/api/users/me', {
        method: 'GET',
      });

      expect(res.status).toBe(401);
      const data = await res.json();
      expect(data).toHaveProperty('error');
    });
  });

  describe('PATCH /api/users/me', () => {
    it('[TC-14] updates display name', async () => {
      const token = await generateValidToken(testUserId);

      (verifyToken as ReturnType<typeof vi.fn>).mockResolvedValue({ userId: testUserId });

      const updatedUser = {
        ...mockUser,
        displayName: 'New Name',
        avatarColor: '#DD6B20',
        updatedAt: new Date('2024-01-02'),
      };

      const mockUpdate = vi.fn().mockReturnValue({
        set: vi.fn().mockReturnValue({
          where: vi.fn().mockReturnValue({
            returning: vi.fn().mockResolvedValue([updatedUser]),
          }),
        }),
      });

      (db.update as ReturnType<typeof vi.fn>).mockImplementation(mockUpdate);

      const res = await app.request('/api/users/me', {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ displayName: 'New Name' }),
      });

      expect(res.status).toBe(200);
      const data = await res.json();
      expect(data).toMatchObject({
        id: testUserId,
        email: 'user@example.com',
        displayName: 'New Name',
        avatarColor: '#DD6B20',
      });
      expect(data.updatedAt).toBeDefined();
    });

    it('[TC-15] rejects empty displayName', async () => {
      const token = await generateValidToken(testUserId);

      (verifyToken as ReturnType<typeof vi.fn>).mockResolvedValue({ userId: testUserId });

      const res = await app.request('/api/users/me', {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ displayName: '' }),
      });

      expect(res.status).toBe(400);
    });

    it('[TC-16] ignores email/id in request body', async () => {
      const token = await generateValidToken(testUserId);

      (verifyToken as ReturnType<typeof vi.fn>).mockResolvedValue({ userId: testUserId });

      const updatedUser = {
        ...mockUser,
        displayName: 'New',
        updatedAt: new Date('2024-01-02'),
      };

      const mockUpdate = vi.fn().mockReturnValue({
        set: vi.fn().mockReturnValue({
          where: vi.fn().mockReturnValue({
            returning: vi.fn().mockResolvedValue([updatedUser]),
          }),
        }),
      });

      (db.update as ReturnType<typeof vi.fn>).mockImplementation(mockUpdate);

      const res = await app.request('/api/users/me', {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          displayName: 'New',
          email: 'hacked@example.com',
          id: 'other-user-id',
        }),
      });

      expect(res.status).toBe(200);
      const data = await res.json();
      expect(data.email).toBe('user@example.com');
      expect(data.id).toBe(testUserId);
    });

    it('[TC-17] rejects update without auth', async () => {
      const res = await app.request('/api/users/me', {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ displayName: 'New Name' }),
      });

      expect(res.status).toBe(401);
    });
  });
});
