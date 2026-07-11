import { Hono } from 'hono';
import ContactPage from 'pages/ContactPage/ContactPage';

const app = new Hono();

app.get('/contact', (c) => {
  return c.html(ContactPage());
});

export default app;