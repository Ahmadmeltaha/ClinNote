import { Hono } from 'hono';
import { contactFormValidation } from '@/lib/validation/contactFormValidation';
import { ContactService } from '@/services/contactService';

const contactService = new ContactService();

export class ContactController {
  private app: Hono;

  constructor() {
    this.app = new Hono();
    this.routes();
  }

  private routes() {
    this.app.post('/submit', async (ctx) => {
      const body = await ctx.req.json();
      const { success, data, error } = contactFormValidation(body);

      if (!success) {
        return ctx.text(error, 400);
      }

      try {
        const result = await contactService.submitContactForm(data);
        return ctx.json(result, 200);
      } catch (err) {
        // Assuming the service throws an error with a message
        return ctx.text(err.message, 500);
      }
    });
  }
}
