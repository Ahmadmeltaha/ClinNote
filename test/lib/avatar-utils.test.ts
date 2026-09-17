import { describe, it, expect } from 'vitest';
import { getInitials, getAvatarColor, AVATAR_COLORS } from '@/lib/avatar-utils';

describe('avatar-utils', () => {
  describe('getInitials', () => {
    it('[avatar-initials-two-words] generates initials from two-word name', () => {
      const result = getInitials('John Doe');
      expect(result).toBe('JD');
    });

    it('[avatar-initials-single-word] generates two letters from single word', () => {
      const result = getInitials('Alice');
      expect(result).toBe('AL');
    });

    it('[avatar-initials-special-chars] strips non-alphabetic characters', () => {
      const result = getInitials('@John #Doe');
      expect(result).toBe('U');
    });

    it('[avatar-initials-empty] fallback to U for empty input', () => {
      const result = getInitials('');
      expect(result).toBe('U');
    });
  });

  describe('getAvatarColor', () => {
    it('[avatar-color-deterministic] same userId produces same color', () => {
      const userId = 'user-123-uuid';
      const color1 = getAvatarColor(userId);
      const color2 = getAvatarColor(userId);
      expect(color1).toBe(color2);
    });

    it('[avatar-color-palette] color is from 8-color palette', () => {
      const userId = 'user-456-uuid';
      const color = getAvatarColor(userId);
      expect(AVATAR_COLORS).toContain(color);
    });
  });
});
