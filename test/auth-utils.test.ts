import { describe, it, expect } from 'vitest';
import {
  hashPassword,
  verifyPassword,
  generateToken,
  verifyToken,
} from '@/lib/auth-utils';
import { sign } from 'hono/jwt';
import { validUserCredentials } from './fixtures/auth-fixtures';

const JWT_SECRET = process.env.JWT_SECRET ?? 'dev-secret-change-me';

describe('auth-utils', () => {
  it('[hash-password] hashes password with bcrypt/argon2', async () => {
    const hash = await hashPassword(validUserCredentials.password);
    expect(hash).not.toBe(validUserCredentials.password);
    expect(hash).toMatch(/^[a-f0-9]+:[a-f0-9]+$/);
  });

  it('[verify-password-valid] verifies correct password', async () => {
    const hash = await hashPassword(validUserCredentials.password);
    const isValid = await verifyPassword(validUserCredentials.password, hash);
    expect(isValid).toBe(true);
  });

  it('[verify-password-invalid] rejects incorrect password', async () => {
    const hash = await hashPassword(validUserCredentials.password);
    const isValid = await verifyPassword('wrongPass', hash);
    expect(isValid).toBe(false);
  });

  it('[generate-token] generates JWT/session token', async () => {
    const token = await generateToken('user-123-uuid');
    expect(token).toBeTruthy();
    expect(typeof token).toBe('string');
    expect(token.split('.')).toHaveLength(3);
  });

  it('[verify-token-valid] verifies valid token', async () => {
    const token = await generateToken('user-123-uuid');
    const payload = await verifyToken(token);
    expect(payload.userId).toBe('user-123-uuid');
  });

  it('[verify-token-expired] rejects expired token', async () => {
    const expiredPayload = {
      userId: 'user-123-uuid',
      exp: Math.floor(Date.now() / 1000) - 3600,
    };
    const expiredToken = await sign(expiredPayload, JWT_SECRET, 'HS256');
    await expect(verifyToken(expiredToken)).rejects.toThrow();
  });
});
