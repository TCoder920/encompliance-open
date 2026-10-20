/*
  Description: Reusable FormField component for rendering input fields (text, email, password, number, textarea) with labels, required indicators, and error messages.
  Purpose: Provides a standardized and accessible way to create form inputs with built-in validation feedback.
*/

import React from 'react';

export interface FormFieldProps {
  id: string;
  label: string;
  type?: 'text' | 'email' | 'password' | 'number' | 'textarea';
  required?: boolean;
  error?: string;
  value: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => void;
  placeholder?: string;
  className?: string;
  disabled?: boolean;
}

const FormField: React.FC<FormFieldProps> = ({
  id,
  label,
  type = 'text',
  required = false,
  error,
  value,
  onChange,
  placeholder = '',
  className = '',
  disabled = false,
}) => {
  const baseInputClasses = `w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 ${
    error ? 'border-red-500 focus:ring-red-200' : 'border-gray-300 focus:ring-blue-200'
  }`;

  const renderInput = () => {
    if (type === 'textarea') {
      return (
        <textarea
          id={id}
          value={value}
          onChange={onChange}
          className={`${baseInputClasses} ${className}`}
          placeholder={placeholder}
          required={required}
          disabled={disabled}
          rows={4}
          aria-invalid={!!error}
          aria-describedby={error ? `${id}-error` : undefined}
        />
      );
    }
    
    return (
      <input
        id={id}
        type={type}
        value={value}
        onChange={onChange}
        className={`${baseInputClasses} ${className}`}
        placeholder={placeholder}
        required={required}
        disabled={disabled}
        aria-invalid={!!error}
        aria-describedby={error ? `${id}-error` : undefined}
      />
    );
  };

  return (
    <div className="mb-4">
      <label 
        htmlFor={id} 
        className="block mb-2 font-medium text-gray-700"
      >
        {label}
        {required && <span className="ml-1 text-red-600">*</span>}
      </label>
      {renderInput()}
      {error && (
        <p id={`${id}-error`} className="mt-1 text-sm text-red-600" role="alert">
          {error}
        </p>
      )}
    </div>
  );
};

export default FormField; 