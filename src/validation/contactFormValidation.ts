import { z } from 'zod';

// Zod schema for validating contact form request
export const contactFormSchema = z.object({
  name: z.string().min(1, { message: 'Name is required' }),
  email: z.string().email({ message: 'Invalid email format' }).min(1, { message: 'Email is required' }),
  subject: z.string().min(1, { message: 'Subject is required' }),
  message: z.string().min(20, { message: 'Message must be at least 20 characters long' })
});