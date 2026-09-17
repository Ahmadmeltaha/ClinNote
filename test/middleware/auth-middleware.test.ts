import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('@/lib/auth-utils', () => ({
  verifyToken: vi.fn(),
}));

import { authMiddleware } from '@/middleware/auth-middleware';
import { verifyToken } from '@/lib/auth-utils';

const mockVerifyToken = vi.mocked(verifyToken);

describe('authMiddleware', () => {
  let mockNext: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    vi.clearAllMocks();
    mockNext = vi.fn().mockResolvedValue(undefined);
  });

  function createMockContext(headers: Record<string, string> = {}) {
    const setCalls: Array<[string, unknown]> = [];
    const ctx = {
      req: {
        header: (name: string) => {
          const normalizedHeaders: Record<string, string> = {};
          for (const [key, value] of Object.entries(headers)) {
            normalizedHeaders[key.toLowerCase()] = value;
          }
          return normalizedHeaders[name.toLowerCase()];
        },
      },
      json: (data: unknown, status: number) => {
        return new Response(JSON.stringify(data), {
          status,
          headers: { 'Content-Type': 'application/json' },
        });
      },
      set: (key: string, value: unknown) => {
        setCalls.push([key, value]);
      },
      _setCalls: setCalls,
    };
    return ctx;
  }

  it('[middleware-valid-token] passes request with valid token', async () => {
    const userId = 'user-123-uuid';
    mockVerifyToken.mockResolvedValue({ userId });

    const ctx = createMockContext({ Authorization: 'Bearer valid-jwt-token' });
    const middleware = authMiddleware();

    await middleware(ctx as any, mockNext);

    expect(mockVerifyToken).toHaveBeenCalledWith('valid-jwt-token');
    expect(mockNext).toHaveBeenCalled();
    expect(ctx._setCalls).toContainEqual(['userId', userId]);
  });

  it('[middleware-missing-token] rejects request without token', async () => {
    const ctx = createMockContext({});
    const middleware = authMiddleware();

    const response = await middleware(ctx as any, mockNext);

    expect(mockVerifyToken).not.toHaveBeenCalled();
    expect(mockNext).not.toHaveBeenCalled();
    expect(response).toBeDefined();
    const body = await (response as Response).json();
    expect(body).toEqual({ error: 'Unauthorized' });
    expect((response as Response).status).toBe(401);
  });

  it('[middleware-invalid-token] rejects request with invalid token', async () => {
    mockVerifyToken.mockRejectedValue(new Error('Invalid token'));

    const ctx = createMockContext({ Authorization: 'Bearer invalid-token' });
    const middleware = authMiddleware();

    const response = await middleware(ctx as any, mockNext);

    expect(mockVerifyToken).toHaveBeenCalledWith('invalid-token');
    expect(mockNext).not.toHaveBeenCalled();
    expect(response).toBeDefined();
    const body = await (response as Response).json();
    expect(body).toEqual({ error: 'Unauthorized' });
    expect((response as Response).status).toBe(401);
  });
});
