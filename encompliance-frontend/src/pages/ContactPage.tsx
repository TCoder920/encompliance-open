/*
  Description: React page for the Contact Us form.
  Purpose: Allows users to send support messages to the EnCompliance team, integrating with the backend contact API and providing user feedback.
*/
import React, { useState } from 'react';
import { Mail, AlertCircle, CheckCircle } from 'lucide-react';
import { sendContactMessage } from '../services/api';
import { useAuth } from '../contexts/AuthContext';

const ContactPage: React.FC = () => {
  const { user } = useAuth();
  const [name, setName] = useState(user?.name || user?.full_name || '');
  const [email, setEmail] = useState(user?.email || '');
  const [message, setMessage] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    // Basic validation
    if (!name.trim()) {
      setError('Please enter your name');
      return;
    }

    if (!email.trim()) {
      setError('Please enter your email');
      return;
    }

    if (!message.trim()) {
      setError('Please enter a message');
      return;
    }

    setIsSubmitting(true);
    try {
      await sendContactMessage({ name, email, message });
      setSubmitted(true);
      setName(user?.name || user?.full_name || '');
      setEmail(user?.email || '');
      setMessage('');
    } catch (err: any) {
      setError(
        err?.response?.data?.detail ||
        err?.message ||
        'Failed to send message. Please try again.'
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <h1 className="text-3xl font-bold text-navy-blue dark:text-white mb-6">Contact Us</h1>
      
      <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6 mb-8">
        {!submitted ? (
          <>
            <p className="mb-6 dark:text-gray-300">
              Have questions or need assistance? Fill out the form below and our team will get back to you as soon as possible.
            </p>
            
            {error && (
              <div className="bg-red-100 dark:bg-red-900 border border-red-400 dark:border-red-700 text-red-700 dark:text-red-200 px-4 py-3 rounded relative mb-4 flex items-center">
                <AlertCircle className="h-5 w-5 mr-2" />
                <span>{error}</span>
              </div>
            )}
            
            <form onSubmit={handleSubmit}>
              <div className="mb-4">
                <label htmlFor="name" className="block text-gray-700 dark:text-gray-300 font-medium mb-2">
                  Your Name
                </label>
                <input
                  type="text"
                  id="name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                  placeholder="John Doe"
                  disabled={!!user}
                />
              </div>
              
              <div className="mb-4">
                <label htmlFor="email" className="block text-gray-700 dark:text-gray-300 font-medium mb-2">
                  Your Email
                </label>
                <input
                  type="email"
                  id="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                  placeholder="john@example.com"
                  disabled={!!user}
                />
              </div>
              
              <div className="mb-4">
                <label htmlFor="message" className="block text-gray-700 dark:text-gray-300 font-medium mb-2">
                  Your Message
                </label>
                <textarea
                  id="message"
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  rows={5}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                  placeholder="How can we help you?"
                  disabled={isSubmitting}
                ></textarea>
              </div>
              
              <button
                type="submit"
                className="bg-blue-600 hover:bg-blue-700 dark:bg-blue-700 dark:hover:bg-blue-800 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline transition duration-150 ease-in-out"
                disabled={isSubmitting}
              >
                {isSubmitting ? 'Sending...' : 'Send Message'}
              </button>
            </form>
          </>
        ) : (
          <div className="text-center py-8">
            <CheckCircle className="h-16 w-16 text-green-500 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-navy-blue dark:text-white mb-2">Thank You!</h2>
            <p className="text-gray-600 dark:text-gray-300 mb-6">
              Your message has been sent. We'll get back to you as soon as possible.
            </p>
            <button
              onClick={() => setSubmitted(false)}
              className="bg-blue-600 hover:bg-blue-700 dark:bg-blue-700 dark:hover:bg-blue-800 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline transition duration-150 ease-in-out"
            >
              Send Another Message
            </button>
          </div>
        )}
        
        <div className="mt-8 pt-6 border-t border-gray-200 dark:border-gray-700">
          <h3 className="text-xl font-bold text-navy-blue dark:text-white mb-3">Direct Contact</h3>
          <p className="flex items-center text-gray-600 dark:text-gray-300 mb-2">
            <Mail className="h-5 w-5 mr-2 text-blue-600 dark:text-blue-400" />
            <a href="mailto:support@encompliance.io" className="text-blue-600 dark:text-blue-400 hover:underline">
              support@encompliance.io
            </a>
          </p>
          <p className="text-gray-600 dark:text-gray-400 mt-4 text-sm italic">
            Note: For legal advice, please consult with your attorney. Our team can only provide general information about our services.
          </p>
        </div>
      </div>
    </div>
  );
};

export default ContactPage; 