import { describe, it, expect } from 'vitest';
import { Hono } from 'hono';
import { contactController } from '@/routes/contactController';
import { AppError } from '@/lib/error/AppError';
import { contactFormSchema } from '@/lib/validation/contactForm';

const app = new Hono();
app.post('/contact/submit', contactController.submitForm);

// Mock the incoming request with valid data and test the response.
describe('submitForm with valid data', () => {
  it('should handle a valid form submission and return a success response', async () => {
    const validData = {
      name: 'John Doe',
      email: 'john.doe@example.com',
      message: 'Hello, this is a test message.'
    };

    const formData = new FormData();
    for (const key in validData) {
      if (validData.hasOwnProperty(key)) {
        formData.append(key, validData[key]);
      }
    }

    const req = new Request('http://localhost:3000/contact/submit', {
      method: 'POST',
      body: formData
    });

    const res = await app.request(req);
    expect(res.status).toBe(200);
    expect(await res.text()).toBe('Form submitted successfully!');
  });
});

// Mock the incoming request with missing required fields and test the response.
describe('submitForm with missing required fields', () => {
  it('should handle an invalid form submission (missing required fields) and return a validation error', async () => {
    const invalidData = {
      // Missing 'name' and 'email'
      message: 'Hello, this is a test message.'
    };

    const formData = new FormData();
    for (const key in invalidData) {
      if (invalidData.hasOwnProperty(key)) {
        formData.append(key, invalidData[key]);
      }
    }

    const req = new Request('http://localhost:3000/contact/submit', {
      method: 'POST',
      body: formData
    });

    const res = await app.request(req);
    expect(res.status).toBe(400);
    expect(await res.text()).toContain('Validation Error:');
  });
});

// Mock the incoming request with an invalid email format and test the response.
describe('submitForm with invalid email format', () => {
  it('should handle an invalid form submission (invalid email format) and return a validation error', async () => {
    const invalidData = {
      name: 'John Doe',
      email: 'not-an-email', // Invalid email format
      message: 'Hello, this is a test message.'
    };

    const formData = new FormData();
    for (const key in invalidData) {
      if (invalidData.hasOwnProperty(key)) {
        formData.append(key, invalidData[key]);
      }
    }

    const req = new Request('http://localhost:3000/contact/submit', {
      method: 'POST',
      body: formData
    });

    const res = await app.request(req);
    expect(res.status).toBe(400);
    expect(await res.text()).toContain('Validation Error:');
  });
});