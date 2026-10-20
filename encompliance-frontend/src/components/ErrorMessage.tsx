import React from 'react';
import { AlertCircle, Info, CheckCircle, X } from 'lucide-react';

/*
  Description: Reusable component for displaying various types of messages, including errors, warnings, info, and success.
  Purpose: Provides a standardized way to communicate important information and feedback to the user with distinct visual cues.
*/

interface ErrorMessageProps {
  message: string | null;
  type?: 'error' | 'warning' | 'info' | 'success';
  onClose?: () => void;
}

const ErrorMessage: React.FC<ErrorMessageProps> = ({ 
  message, 
  type = 'error',
  onClose
}) => {
  if (!message) return null;
  
  const getIcon = () => {
    switch(type) {
      case 'warning':
        return <AlertCircle className="h-5 w-5 text-yellow-500" />;
      case 'info':
        return <Info className="h-5 w-5 text-blue-500" />;
      case 'success':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'error':
      default:
        return <AlertCircle className="h-5 w-5 text-red-500" />;
    }
  };
  
  const getBackgroundColor = () => {
    switch(type) {
      case 'warning':
        return 'bg-yellow-50';
      case 'info':
        return 'bg-blue-50';
      case 'success':
        return 'bg-green-50';
      case 'error':
      default:
        return 'bg-red-50';
    }
  };
  
  const getBorderColor = () => {
    switch(type) {
      case 'warning':
        return 'border-yellow-300';
      case 'info':
        return 'border-blue-300';
      case 'success':
        return 'border-green-300';
      case 'error':
      default:
        return 'border-red-300';
    }
  };
  
  const getTextColor = () => {
    switch(type) {
      case 'warning':
        return 'text-yellow-700';
      case 'info':
        return 'text-blue-700';
      case 'success':
        return 'text-green-700';
      case 'error':
      default:
        return 'text-red-700';
    }
  };
  
  return (
    <div className={`p-4 mb-4 border rounded-md flex items-start ${getBackgroundColor()} ${getBorderColor()}`}>
      <div className="flex-shrink-0 mr-3 mt-0.5">
        {getIcon()}
      </div>
      <div className={`flex-1 ${getTextColor()}`}>
        <p className="text-sm font-medium">{message}</p>
      </div>
      {onClose && (
        <button 
          onClick={onClose}
          className="ml-auto -mx-1.5 -my-1.5 p-1.5 rounded-md focus:outline-none focus:ring-2 focus:ring-gray-300"
        >
          <X className="h-4 w-4 text-gray-500" />
        </button>
      )}
    </div>
  );
};

export default ErrorMessage; 