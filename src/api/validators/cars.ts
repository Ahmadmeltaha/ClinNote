import { z } from 'zod';
import type { CarPhoto } from '@/db/schema';

// ─── Existing validators from prior build ───────────────────────────────────

export const CarListQuery = z.object({
  page: z.coerce.number().int().positive().optional().default(1),
  limit: z.coerce.number().int().positive().max(100).optional().default(20),
  make: z.string().optional(),
  model: z.string().optional(),
  minYear: z.coerce.number().int().optional(),
  maxYear: z.coerce.number().int().optional(),
  minPrice: z.coerce.number().optional(),
  maxPrice: z.coerce.number().optional(),
  fuel: z.string().optional(),
  transmission: z.string().optional(),
  bodyType: z.string().optional(),
  sort: z
    .enum(['price_asc', 'price_desc', 'year_desc', 'year_asc', 'mileage_asc'])
    .optional(),
});

export type CarListQueryInput = z.input<typeof CarListQuery>;
export type CarListQueryOutput = z.output<typeof CarListQuery>;

// ─── New validators for car detail endpoint ─────────────────────────────────

export const GetCarDetailParams = z.object({
  id: z.string().uuid(),
});

export const CarPhotoSchema = z.object({
  url: z.string().url(),
  altText: z.string(),
});

export const SimilarCar = z.object({
  id: z.string().uuid(),
  make: z.string(),
  model: z.string(),
  year: z.number().int(),
  price: z.number(),
  mainPhotoUrl: z.string().url(),
});

export const CarDetailResponse = z.object({
  id: z.string().uuid(),
  make: z.string(),
  model: z.string(),
  year: z.number().int(),
  mileage: z.number(),
  fuel: z.string(),
  transmission: z.string(),
  color: z.string(),
  bodyType: z.string(),
  price: z.number(),
  description: z.string(),
  photos: z.array(CarPhotoSchema),
  status: z.enum(['available', 'sold']),
  similarCars: z.array(SimilarCar),
});

// ─── Compile-time type assertions ───────────────────────────────────────────
// Ensure the Zod-inferred type for CarPhotoSchema is structurally identical to
// the CarPhoto type exported from the DB schema.

type _CarPhotoSchemaInferred = z.infer<typeof CarPhotoSchema>;

type _AssertCarPhotoMatch = _CarPhotoSchemaInferred extends CarPhoto
  ? CarPhoto extends _CarPhotoSchemaInferred
    ? true
    : never
  : never;

const _carPhotoTypeCheck: _AssertCarPhotoMatch = true;
void _carPhotoTypeCheck;

// ─── Exported inferred types ────────────────────────────────────────────────

export type GetCarDetailParamsInput = z.input<typeof GetCarDetailParams>;
export type CarPhotoSchemaInput = z.input<typeof CarPhotoSchema>;
export type SimilarCarInput = z.input<typeof SimilarCar>;
export type CarDetailResponseInput = z.input<typeof CarDetailResponse>;
export type CarDetailResponseType = z.infer<typeof CarDetailResponse>;