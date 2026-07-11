import React, { useState } from 'react';
import { toast } from 'react-toastify';

interface ContactFormData {
  name: string;
  email: string;
  subject: string;
  message: string;
}

type ContactFormProps = {
  onSubmit: (formData: ContactFormData) => void;
};

const ContactForm: React.FC<ContactFormProps> = ({ onSubmit }) => {
  const [formData, setFormData] = useState<ContactFormData>({ name: '', email: '', subject: '', message: '' });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleChange = (event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = event.target;
    setFormData({ ...formData, [name]: value });
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setIsSubmitting(true);

    try {
      // IMPLEMENT: Call the `onSubmit` callback with form data.
      await onSubmit(formData);
      // IMPLEMENT: Show a success message using `toast.success`.
    } catch (error) {
      // IMPLEMENT: Show an error message using `toast.error`.
    } finally {
      // Reset the form and submission state.
      setFormData({ name: '', email: '', subject: '', message: '' });
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} noValidate>
      {/* Name input */}
      <input
        type="text"
        name="name"
        placeholder="Name"
        value={formData.name}
        onChange={handleChange}
        required
      />

      {/* Email input */}
      <input
        type="email"
        name="email"
        placeholder="Email"
        value={formData.email}
        onChange={handleChange}
        required
      />

      {/* Subject input */}
      <input
        type="text"
        name="subject"
        placeholder="Subject"
        value={formData.subject}
        onChange={handleChange}
        required
      />

      {/* Message textarea */}
      <textarea
        name="message"
        placeholder="Message"
        value={formData.message}
        onChange={handleChange}
        required
      ></textarea>

      {/* Submit button */}
      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Sending...' : 'Send'}
      </button>
    </form>
  );
};

export default ContactForm;