import { pgTable, uuid, varchar, real, text, boolean } from 'drizzle-orm/pg-core';

export const cylinders = pgTable('cylinders', {
  id: uuid('id').defaultRandom().primaryKey(),
  name: varchar('name', { length: 100 }).notNull(),
  sizeKg: real('size_kg').notNull(),
  gasType: varchar('gas_type', { length: 10 }).notNull(),
  price: real('price').notNull(),
  imageUrl: text('image_url').notNull(),
  inStock: boolean('in_stock').notNull().default(true),
});