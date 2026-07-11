import React, { useState } from 'react';
import ContactForm from './ContactForm/ContactForm';
import ConfirmationMessage from './ContactForm/ConfirmationMessage';

interface ContactPageProps {
  // Add any props that the ContactPage may need here
}

const ContactPage: React.FC<ContactPageProps> = (props) => {
  const [isFormSubmitted, setIsFormSubmitted] = useState(false);

  const handleFormSubmit = () => {
    // When the form is submitted, set isFormSubmitted to true
    // IMPLEMENT
  };

  return (
    <div>
      {!isFormSubmitted ? (
        <ContactForm onSubmit={handleFormSubmit} />
      ) : (
        <ConfirmationMessage />
      )}
    </div>
  );
};

export default ContactPage;