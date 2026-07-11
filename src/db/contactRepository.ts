import { db } from '@/db/client';
import { ContactFormData } from '@/types/contactForm';
import { AppError } from '@/errors';

export async function storeContactForm(formData: ContactFormData): Promise<void> {
  try {
    const query = `INSERT INTO contact_form (name, email, message) VALUES ($1, $2, $3)`;
    await db.query(query, [formData.name, formData.email, formData.message]);
  } catch (error) {
    console.error('Failed to store contact form data:', error);
    throw new AppError('Failed to store contact form data', 500);
  }
}