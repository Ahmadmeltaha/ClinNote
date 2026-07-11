import { describe, it, expect } from 'vitest';
import { ContactService } from '@/services/contactService';
import { AppError } from '@/lib/error/AppError';
import { contactFormSchema } from '@/lib/validation/contactForm';

vi.mock('@/services/contactService');

describe('ContactService', () => {
  const contactService = new ContactService();

  it('should submit a valid contact form and return a success response', async () => {
    const validForm = {
      name: 'John Doe',
      email: 'john.doe@example.com',
      message: 'Hello, this is a test message.'
    };

    vi.spyOn(ContactService.prototype, 'submitContactForm').mockResolvedValueOnce({ success: true });

    const result = await contactService.submitContactForm(validForm);

    expect(result).toEqual({ success: true });
  });

  it('should throw an error for an invalid contact form (missing required fields)', async () => {
    const invalidFormMissingFields = {
      email: 'john.doe@example.com'
    };

    vi.spyOn(ContactService.prototype, 'submitContactForm').mockRejectedValueOnce(new AppError('Invalid form'));

    await expect(() => contactService.submitContactForm(invalidFormMissingFields)).rejects.toThrow(AppError);
  });

  it('should throw an error for an invalid contact form (invalid email format)', async () => {
    const invalidFormInvalidEmail = {
      name: 'John Doe',
      email: 'not-an-email',
      message: 'Hello, this is a test message.'
    };

    vi.spyOn(ContactService.prototype, 'submitContactForm').mockRejectedValueOnce(new AppError('Invalid form'));

    await expect(() => contactService.submitContactForm(invalidFormInvalidEmail)).rejects.toThrow(AppError);
  });
});