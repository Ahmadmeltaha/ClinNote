import { vi } from 'vitest';
import type { User } from '@/db/tables/user-accounts-profiles';

export function createMockDb() {
  const mockDb = {
    select: vi.fn().mockReturnThis(),
    from: vi.fn().mockReturnThis(),
    where: vi.fn().mockReturnThis(),
    insert: vi.fn().mockReturnThis(),
    values: vi.fn().mockReturnThis(),
    returning: vi.fn().mockResolvedValue([]),
    update: vi.fn().mockReturnThis(),
    set: vi.fn().mockReturnThis(),
  };

  return mockDb;
}

export function mockDbSelectReturns(mockDb: ReturnType<typeof createMockDb>, users: User[]) {
  mockDb.returning.mockResolvedValue(users);
  mockDb.where.mockResolvedValue(users);
}

export function mockDbInsertReturns(mockDb: ReturnType<typeof createMockDb>, users: User[]) {
  mockDb.returning.mockResolvedValue(users);
}

export function mockDbUpdateReturns(mockDb: ReturnType<typeof createMockDb>, users: User[]) {
  mockDb.returning.mockResolvedValue(users);
}

export function mockDbSelectEmpty(mockDb: ReturnType<typeof createMockDb>) {
  mockDb.returning.mockResolvedValue([]);
  mockDb.where.mockResolvedValue([]);
}
