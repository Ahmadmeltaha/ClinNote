import { Hono } from 'hono';
import { zValidator } from '@hono/zod-validator';
import { z } from 'zod';
import { db } from '@/db/index';
import { users } from '@/db/schema';
import { hashPassword, verifyPassword, generateToken } from '@/lib/auth-utils';
import { getAvatarColor } from '@/lib/avatar-utils';
import { authMiddleware } from '@/middleware/auth-middleware';
import { eq } from 'drizzle-orm';

const signupSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
  displayName: z.string().min(1).max(50),
});

const loginSchema = z.object({
  email: z.string().email(),
  password: z.string(),
});

function sanitizeUser(user: {
  id: string;
  email: string;
  displayName: string;
  avatarColor: string;
}) {
  return {
    id: user.id,
    email: user.email,
    displayName: user.displayName,
    avatarColor: user.avatarColor,
  };
}

export const authRoutes = new Hono();

authRoutes.post('/signup', zValidator('json', signupSchema), async (c) => {
  const input = c.req.valid('json');

  const existing = await db
    .select()
    .from(users)
    .where(eq(users.email, input.email));

  if (existing[0]) {
    return c.json({ error: 'An account with this email already exists.' }, 409);
  }

  const passwordHash = await hashPassword(input.password);

  const inserted = await db
    .insert(users)
    .values({
      email: input.email,
      passwordHash,
      displayName: input.displayName,
      avatarColor: '#6366f1',
    })
    .returning();

  const user = inserted[0];

  const avatarColor = getAvatarColor(user.id);

  const updated = await db
    .update(users)
    .set({ avatarColor })
    .where(eq(users.id, user.id))
    .returning();

  const finalUser = updated[0];

  const token = await generateToken(finalUser.id);

  return c.json(
    {
      user: sanitizeUser(finalUser),
      token,
    },
    200
  );
});

authRoutes.post('/login', zValidator('json', loginSchema), async (c) => {
  const input = c.req.valid('json');

  const result = await db
    .select()
    .from(users)
    .where(eq(users.email, input.email));

  const user = result[0];

  if (!user) {
    return c.json({ error: 'Invalid email or password.' }, 401);
  }

  const valid = await verifyPassword(input.password, user.passwordHash);

  if (!valid) {
    return c.json({ error: 'Invalid email or password.' }, 401);
  }

  const token = await generateToken(user.id);

  return c.json(
    {
      user: sanitizeUser(user),
      token,
    },
    200
  );
});

authRoutes.post('/logout', authMiddleware(), async (c) => {
  return c.json({ success: true }, 200);
});
