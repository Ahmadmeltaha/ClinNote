import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Avatar } from '../../src/components/Avatar';

describe('Avatar', () => {
  it('[avatar-renders-initials] displays user initials', () => {
    render(<Avatar displayName="John Doe" avatarColor="#FF5733" />);
    const avatar = screen.getByRole('img', { name: /Avatar for John Doe/i });
    expect(avatar.textContent).toBe('JD');
  });

  it('[avatar-applies-color] applies background color', () => {
    render(<Avatar displayName="Alice" avatarColor="#3498DB" />);
    const avatar = screen.getByRole('img', { name: /Avatar for Alice/i });
    expect(avatar.getAttribute('style')).toContain('#3498DB');
  });

  it('[avatar-alt-text] has correct alt text', () => {
    render(<Avatar displayName="Test" avatarColor="#000" />);
    const avatar = screen.getByRole('img', { name: /Avatar for Test/i });
    expect(avatar.getAttribute('aria-label')).toBe('Avatar for Test');
  });
});
