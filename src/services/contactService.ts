import { inject, singleton } from 'tsyringe';
import { ContactRepository } from '@/db/contactRepository';
import { ContactFormData } from '@/types/contactForm';

@singleton()
class ContactService {
    private contactRepository: ContactRepository;

    constructor(@inject(ContactRepository) contactRepository: ContactRepository) {
        this.contactRepository = contactRepository;
    }

    public async submitContactForm(formData: ContactFormData): Promise<void> {
        try {
            await this.contactRepository.storeFormData(formData);
        } catch (error) {
            throw new AppError('Failed to submit contact form', 500, error);
        }
    }
}

export { ContactService };