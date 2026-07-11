import { describe, it, expect } from 'vitest';
import { contactFormSchema } from '@/lib/validation/contactForm';

// Test suite for contact form validation

describe('Contact Form Validation', () => {
  it('should validate a valid form input', () => {
    const validInput = {
      name: 'John Doe',
      email: 'john.doe@example.com',
      message: 'Hello, this is a test message.'
    };

    const result = contactFormSchema.safeParse(validInput);

    expect(result.success).toBe(true);
    expect(result.error).toBe(undefined);
  });

  it('should reject an invalid form input (missing required fields)', () => {
    const invalidInput = {};

    const result = contactFormSchema.safeParse(invalidInput);

    expect(result.success).toBe(false);
    // Assuming there are 3 required fields: name, email, and message
    expect(result.error.issues.length).toBe(3);
  });

  it('should reject an invalid form input (invalid email format)', () => {
    const invalidInput = {
      name: 'John Doe',
      email: 'not-an-email', // Invalid email
      message: 'Hello, this is a test message.'
    };

    const result = contactFormSchema.safeParse(invalidInput);

    expect(result.success).toBe(false);
    // Assuming that the validation schema checks for email format
    // and returns an error with an issue related to the email field.
    expect(result.error.issues.find(issue => issue.path[0] === 'email')).toBeDefined();
  });
});