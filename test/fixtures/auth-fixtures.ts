import { hashPassword, generateToken } from '@/lib/auth-utils';
import { getAvatarColor } from '@/lib/avatar-utils';
import type { User } from '@/db/tables/user-accounts-profiles';

export const validUserCredentials = {
  email: 'test@example.com',
  password: 'password123',
  displayName: 'Test User',
};

export const existingUser: User = {
  id: '550e8400-e29b-41d4-a716-446655440000',
  email: 'existing@example.com',
  passwordHash: 'placeholder',
  displayName: 'Existing User',
  avatarColor: '#E53E3E',
  createdAt: new Date('2024-01-01T00:00:00.000Z'),
  updatedAt: new Date('2024-01-01T00:00:00.000Z'),
};

export async function createExistingUserWithHash(): Promise<User> {
  const passwordHash = await hashPassword('password123');
  return {
    ...existingUser,
    passwordHash,
  };
}

export async function createValidAuthToken(userId: string = existingUser.id): Promise<string> {
  return await generateToken(userId);
}

export function createSanitizedUser(user: User) {
  return {
    id: user.id,
    email: user.email,
    displayName: user.displayName,
    avatarColor: user.avatarColor,
  };
}

export const mockUserResponse = {
  id: existingUser.id,
  email: existingUser.email,
  displayName: existingUser.displayName,
  avatarColor: existingUser.avatarColor,
  createdAt: existingUser.createdAt.toISOString(),
};

export const mockUpdatedUserResponse = {
  id: existingUser.id,
  email: existingUser.email,
  displayName: 'Updated Name',
  avatarColor: getAvatarColor(existingUser.id),
  updatedAt: new Date().toISOString(),
};
