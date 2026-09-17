import { Hono } from 'hono';
import { zValidator } from '@hono/zod-validator';
import { z } from 'zod';
import { db } from '@/db/index';
import { users } from '@/db/schema';
import { authMiddleware } from '@/middleware/auth-middleware';
import { eq } from 'drizzle-orm';

type Variables = {
  userId: string;
};

const updateProfileSchema = z.object({
  displayName: z.string().min(1).max(50),
});

export const userRoutes = new Hono<{ Variables: Variables }>();

userRoutes.use('*', authMiddleware());

userRoutes.get('/me', async (c) => {
  const userId = c.get('userId');

  const result = await db.select().from(users).where(eq(users.id, userId));
  const user = result[0];

  if (!user) {
    return c.json({ error: 'User not found' }, 404);
  }

  const { id, email, displayName, avatarColor, createdAt } = user;

  return c.json(
    {
      id,
      email,
      displayName,
      avatarColor,
      createdAt: createdAt.toISOString(),
    },
    200,
  );
});

userRoutes.patch(
  '/me',
  zValidator('json', updateProfileSchema),
  async (c) => {
    const userId = c.get('userId');
    const input = c.req.valid('json');

    const result = await db
      .update(users)
      .set({ displayName: input.displayName, updatedAt: new Date() })
      .where(eq(users.id, userId))
      .returning();

    const user = result[0];
    const { id, email, displayName, avatarColor, updatedAt } = user;

    return c.json(
      {
        id,
        email,
        displayName,
        avatarColor,
        updatedAt: updatedAt.toISOString(),
      },
      200,
    );
  },
);
