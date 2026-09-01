import { z } from 'zod';

export const CylinderSchema = z.object({
  id: z.string().uuid(),
  name: z.string().min(1).max(100),
  sizeKg: z.number().positive(),
  gasType: z.enum(['butane', 'propane']),
  price: z.number().nonnegative(),
  imageUrl: z.string().url(),
  inStock: z.boolean(),
});

export const GetCatalogResponseSchema = z.array(CylinderSchema);

export type Cylinder = z.infer<typeof CylinderSchema>;
export type GetCatalogResponse = z.infer<typeof GetCatalogResponseSchema>;