import { getInitials } from '@/lib/avatar-utils';

interface AvatarProps {
  displayName: string;
  avatarColor: string;
  size?: number;
}

export function Avatar({ displayName, avatarColor, size = 64 }: AvatarProps) {
  return (
    <div
      role="img"
      aria-label={`Avatar for ${displayName}`}
      className="flex items-center justify-center rounded-full font-bold select-none text-white"
      style={
        {
          '--avatar-color': avatarColor,
          backgroundColor: 'var(--avatar-color)',
          width: size,
          height: size,
          fontSize: size * 0.4,
        } as React.CSSProperties
      }
    >
      {getInitials(displayName)}
    </div>
  );
}
