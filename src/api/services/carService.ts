import { db } from '@/db';
import { cars } from '@/db/schema';
import type { CarPhoto } from '@/db/schema';
import { eq, or, and, ne, sql, desc, asc, like, gte, lte } from 'drizzle-orm';
import {
  CarDetailResponse,
  CarPhotoSchema,
  CarListQuery,
  SimilarCar,
} from '@/api/validators/cars';
import type { z } from 'zod';

// ─── Constants ────────────────────────────────────────────────────────────────

const PLACEHOLDER_IMAGE = '/images/placeholder-car.jpg';

// ─── Helpers ──────────────────────────────────────────────────────────────────

/** Parse the JSONB photos column into a validated CarPhoto array. */
function parsePhotos(raw: unknown): CarPhoto[] {
  return CarPhotoSchema.array().parse((raw as CarPhoto[]) ?? []);
}

/** Derive the main photo URL from a parsed photos array, falling back to placeholder. */
function mainPhotoUrl(photos: CarPhoto[]): string {
  return photos[0]?.url ?? PLACEHOLDER_IMAGE;
}

// ─── Service class ────────────────────────────────────────────────────────────

export class CarService {
  constructor(private readonly database: any) {}

  // ── Existing method (prior wave): list cars with filtering / sorting / pagination ──

  async getCars(query: z.output<typeof CarListQuery>) {
    const {
      page,
      limit,
      make,
      model,
      minYear,
      maxYear,
      minPrice,
      maxPrice,
      fuel,
      transmission,
      bodyType,
      sort,
    } = query;

    // Build dynamic WHERE conditions
    const conditions: any[] = [];
    if (make) conditions.push(like(cars.make, `%${make}%`));
    if (model) conditions.push(like(cars.model, `%${model}%`));
    if (minYear !== undefined) conditions.push(gte(cars.year, minYear));
    if (maxYear !== undefined) conditions.push(lte(cars.year, maxYear));
    if (minPrice !== undefined) conditions.push(gte(sql`${cars.price}::numeric`, minPrice));
    if (maxPrice !== undefined) conditions.push(lte(sql`${cars.price}::numeric`, maxPrice));
    if (fuel) conditions.push(eq(cars.fuel, fuel));
    if (transmission) conditions.push(eq(cars.transmission, transmission));
    if (bodyType) conditions.push(eq(cars.bodyType, bodyType));

    const whereClause = conditions.length > 0 ? and(...conditions) : undefined;

    // Determine ORDER BY
    let orderByClause: any;
    switch (sort) {
      case 'price_asc':
        orderByClause = asc(sql`${cars.price}::numeric`);
        break;
      case 'price_desc':
        orderByClause = desc(sql`${cars.price}::numeric`);
        break;
      case 'year_desc':
        orderByClause = desc(cars.year);
        break;
      case 'year_asc':
        orderByClause = asc(cars.year);
        break;
      case 'mileage_asc':
        orderByClause = asc(cars.mileage);
        break;
      default:
        orderByClause = desc(cars.id);
    }

    const offset = (page - 1) * limit;

    const rows = await this.database
      .select()
      .from(cars)
      .where(whereClause)
      .orderBy(orderByClause)
      .limit(limit)
      .offset(offset);

    // Total count for pagination metadata
    const [countResult] = await this.database
      .select({ count: sql<number>`count(*)` })
      .from(cars)
      .where(whereClause);

    const total = Number(countResult?.count ?? 0);

    const data = rows.map((row: any) => ({
      ...row,
      price: Number(row.price),
      photos: parsePhotos(row.photos),
    }));

    return {
      data,
      pagination: {
        page,
        limit,
        total,
        totalPages: Math.ceil(total / limit),
      },
    };
  }

  // ── Existing method (prior wave): create a new car ──

  async createCar(data: {
    make: string;
    model: string;
    year: number;
    mileage: number;
    fuel: string;
    transmission: string;
    color: string;
    price: number;
    description?: string | null;
    photos?: CarPhoto[];
    bodyType?: string;
  }) {
    const [created] = await this.database
      .insert(cars)
      .values({
        make: data.make,
        model: data.model,
        year: data.year,
        mileage: data.mileage,
        fuel: data.fuel,
        transmission: data.transmission,
        color: data.color,
        price: String(data.price),
        description: data.description ?? null,
        photos: data.photos ?? [],
        bodyType: data.bodyType ?? 'sedan',
      })
      .returning();

    return {
      ...created,
      price: Number(created.price),
      photos: parsePhotos(created.photos),
    };
  }

  // ── New method (wave 4): fetch a single car with similar cars ──

  /**
   * Fetches a single car by ID, parses its photos JSONB column, queries up to 6
   * similar cars matching on make OR bodyType (excluding self), and returns the
   * combined CarDetailResponse object — or null if the car is not found.
   *
   * DB / query errors are intentionally left to propagate to the global error handler.
   */
  async getCarById(carId: string): Promise<z.infer<typeof CarDetailResponse> | null> {
    // (1) Query the car by ID
    const result = await this.database
      .select()
      .from(cars)
      .where(eq(cars.id, carId))
      .limit(1);

    if (result.length === 0) {
      return null;
    }

    const car = result[0];

    // (2) Parse the photos JSONB column into validated CarPhoto[]
    const photos = parsePhotos(car.photos);

    // (3) Query similar cars: same make OR same bodyType, excluding self, limit 6
    const similarRows = await this.database
      .select()
      .from(cars)
      .where(
        and(
          or(eq(cars.make, car.make), eq(cars.bodyType, car.bodyType)),
          ne(cars.id, car.id),
        ),
      )
      .limit(6);

    // (4) Map similar rows to SimilarCar shape
    const similarCars = similarRows.map((row: any) => {
      const rowPhotos = parsePhotos(row.photos);
      return {
        id: row.id,
        make: row.make,
        model: row.model,
        year: row.year,
        price: Number(row.price),
        mainPhotoUrl: mainPhotoUrl(rowPhotos),
      };
    });

    // (5) Resolve status — the schema may or may not carry a status column yet;
    //     default to 'available' so sold cars (when the column exists) pass through.
    const status: 'available' | 'sold' =
      (car as any).status === 'sold' ? 'sold' : 'available';

    // (6) Return the combined CarDetailResponse-shaped object
    return {
      id: car.id,
      make: car.make,
      model: car.model,
      year: car.year,
      mileage: car.mileage,
      fuel: car.fuel,
      transmission: car.transmission,
      color: car.color,
      bodyType: car.bodyType,
      price: Number(car.price),
      description: car.description ?? '',
      photos,
      status,
      similarCars,
    };
  }
}

// ─── DI instance & standalone convenience export ──────────────────────────────

export const carService = new CarService(db);

/** Standalone function that delegates to the singleton CarService instance. */
export async function getCarById(
  carId: string,
): Promise<z.infer<typeof CarDetailResponse> | null> {
  return carService.getCarById(carId);
}