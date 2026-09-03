import { Hono } from 'hono';
import { carService } from '@/api/services/carService';
import { CarListQuery, GetCarDetailParams } from '@/api/validators/cars';

export const carsRoute = new Hono();

// ─── GET / — List cars with filtering, sorting, pagination ───────────────────

carsRoute.get('/', async (c) => {
  const query = CarListQuery.parse(c.req.query());
  const result = await carService.getCars(query);
  return c.json(result);
});

// ─── POST / — Create a new car ───────────────────────────────────────────────

carsRoute.post('/', async (c) => {
  const body = await c.req.json();
  const car = await carService.createCar(body);
  return c.json(car, 201);
});

// ─── GET /:id — Fetch a single car with similar cars ─────────────────────────

carsRoute.get('/:id', async (c) => {
  // (1) Extract the raw path parameter
  const rawId = c.req.param('id');

  // (2) Validate via Zod schema — rejects invalid UUIDs
  const parsed = GetCarDetailParams.safeParse({ id: rawId });
  if (!parsed.success) {
    return c.json(
      { error: 'Invalid car ID.', details: parsed.error.flatten() },
      400,
    );
  }

  // (3) Fetch the car (with similar cars) from the service layer
  const car = await carService.getCarById(parsed.data.id);

  // (4) Return 404 if the car does not exist
  if (!car) {
    return c.json({ error: 'Car not found.' }, 404);
  }

  // (5) Return the full car detail response
  return c.json(car, 200);
});