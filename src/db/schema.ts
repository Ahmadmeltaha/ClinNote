import { pgTable, uuid, text, integer, numeric, jsonb } from 'drizzle-orm/pg-core';

export type CarPhoto = { url: string; altText: string };

export const cars = pgTable('cars', {
  id: uuid('id').primaryKey().defaultRandom(),
  make: text('make').notNull(),
  model: text('model').notNull(),
  year: integer('year').notNull(),
  mileage: integer('mileage').notNull(),
  fuel: text('fuel').notNull(),
  transmission: text('transmission').notNull(),
  color: text('color').notNull(),
  price: numeric('price').notNull(),
  description: text('description'),
  photos: jsonb('photos').notNull().default([]).$type<CarPhoto[]>(),
  bodyType: text('body_type').notNull().default('sedan'),
});