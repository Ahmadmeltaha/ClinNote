import { Hono, Context } from 'hono';
import { db } from '../db/index';
import { cylinders } from '../db/schema';
import { authMiddleware } from '../lib/auth';

const app = new Hono();

app.use('*', authMiddleware);

export const getCatalog = async (c: Context) => {
  try {
    const result = await db.select().from(cylinders);
    return c.json(result);
  } catch (error) {
    return c.json({ error: 'Failed to fetch catalog' }, 500);
  }
};

app.get('/api/v1/catalog', getCatalog);

export default app;