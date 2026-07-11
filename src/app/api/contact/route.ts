import { Hono } from 'hono';
import { ContactController } from '@/controllers/contactController';

const contactRoute = new Hono();

contactRoute.post('/api/contact', async (ctx) => {
  const body = await ctx.req.json();
  const response = await ContactController.handleContactForm(body);
  return ctx.json(response, response.statusCode);
});

export default contactRoute;
