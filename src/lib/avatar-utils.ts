export const AVATAR_COLORS = [
  '#E53E3E',
  '#DD6B20',
  '#D69E2E',
  '#38A169',
  '#319795',
  '#3182CE',
  '#5A67D8',
  '#805AD5',
] as const;

export function getInitials(displayName: string): string {
  const words = displayName.split(' ').filter((w) => w.length > 0);

  let result: string;

  if (words.length === 0) {
    result = '';
  } else if (words.length === 1) {
    result = words[0].substring(0, 2);
  } else {
    result = words[0].charAt(0) + words[1].charAt(0);
  }

  result = result.replace(/[^a-zA-Z]/g, '').toUpperCase();

  if (result === '') {
    return 'U';
  }

  return result;
}

export function getAvatarColor(userId: string): string {
  let hash = 5381;
  for (let i = 0; i < userId.length; i++) {
    hash = hash * 33 + userId.charCodeAt(i);
  }
  return AVATAR_COLORS[Math.abs(hash) % AVATAR_COLORS.length];
}
