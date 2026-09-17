import postgres from 'postgres';
import { drizzle } from 'drizzle-orm/postgres-js';
import { users } from '@/db/schema';

const DATABASE_URL = process.env.DATABASE_URL ?? 'postgres://localhost:5432/chat';

const client = postgres(DATABASE_URL);

export const db = drizzle(client, { schema: { users } });

export async function initializeDatabase(): Promise<void> {
  await client`
    CREATE TABLE IF NOT EXISTS users (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      email VARCHAR(255) NOT NULL UNIQUE,
      password_hash VARCHAR(255) NOT NULL,
      display_name VARCHAR(50) NOT NULL,
      avatar_color VARCHAR(7) NOT NULL,
      created_at TIMESTAMP NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMP NOT NULL DEFAULT NOW()
    )
  `;
}
