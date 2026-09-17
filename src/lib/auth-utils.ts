import { scrypt, randomBytes, timingSafeEqual } from 'crypto';
import { promisify } from 'util';
import { sign, verify } from 'hono/jwt';

const scryptAsync = promisify(scrypt) as (
  password: string | Buffer,
  salt: string | Buffer,
  keylen: number
) => Promise<Buffer>;

const JWT_SECRET = process.env.JWT_SECRET ?? 'dev-secret-change-me';

export async function hashPassword(password: string): Promise<string> {
  const salt = randomBytes(16);
  const derivedKey = await scryptAsync(password, salt, 64);
  return `${salt.toString('hex')}:${derivedKey.toString('hex')}`;
}

export async function verifyPassword(
  password: string,
  storedHash: string
): Promise<boolean> {
  const [saltHex, keyHex] = storedHash.split(':');
  const saltBuffer = Buffer.from(saltHex, 'hex');
  const keyBuffer = Buffer.from(keyHex, 'hex');
  const derivedKey = await scryptAsync(password, saltBuffer, 64);
  return timingSafeEqual(derivedKey, keyBuffer);
}

export async function generateToken(userId: string): Promise<string> {
  const token = await sign({ userId }, JWT_SECRET, 'HS256');
  return token;
}

export async function verifyToken(
  token: string
): Promise<{ userId: string }> {
  const payload = await verify(token, JWT_SECRET, 'HS256');
  return payload as { userId: string };
}
