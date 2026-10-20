/*
  Description: Operation type selection page component. Allows users to select the type of operation they manage for tailored compliance resources.
  Purpose: Guides users to choose their operation type, influencing the compliance content and tools provided.
*/

import React from 'react';
import { Building2, Home } from 'lucide-react';

interface OperationTypePageProps {
  onOperationTypeSelect: (type: string) => void;
}

const OperationTypePage: React.FC<OperationTypePageProps> = ({ onOperationTypeSelect }) => {
  return (
    <div className="container mx-auto px-4 py-12 max-w-2xl">
      <div className="bg-white dark:bg-dark-surface rounded-lg shadow-lg p-8">
        <h1 className="text-3xl font-bold text-navy-blue dark:text-white mb-6 text-center font-times">Select Your Operation Type</h1>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <button
            className="flex flex-col items-center p-6 border border-gray-300 dark:border-gray-700 rounded-lg hover:border-navy-blue dark:hover:border-blue-600 hover:shadow-md transition duration-200 bg-white dark:bg-gray-800"
            onClick={() => onOperationTypeSelect('Daycare')}
          >
            <Home className="h-16 w-16 text-navy-blue dark:text-blue-400 mb-4" />
            <h2 className="text-xl font-bold text-navy-blue dark:text-blue-300 mb-2">Daycare</h2>
            <p className="text-gray-600 dark:text-gray-300 text-center min-h-[3em]">
              Minimum Standards for Licensed and Registered Child-Care Homes
            </p>
          </button>
          
          <button
            className="flex flex-col items-center p-6 border border-gray-300 dark:border-gray-700 rounded-lg hover:border-navy-blue dark:hover:border-blue-600 hover:shadow-md transition duration-200 bg-white dark:bg-gray-800"
            onClick={() => onOperationTypeSelect('GRO/RTC')}
          >
            <Building2 className="h-16 w-16 text-navy-blue dark:text-blue-400 mb-4" />
            <h2 className="text-xl font-bold text-navy-blue dark:text-blue-300 mb-2">GRO/RTC</h2>
            <p className="text-gray-600 dark:text-gray-300 text-center min-h-[3em]">
              Minimum Standards for General Residential Operations
            </p>
          </button>
        </div>
        
        <div className="text-center text-gray-600 dark:text-gray-300">
          <p>Select the type of operation you manage to access the relevant compliance resources.</p>
        </div>
      </div>
    </div>
  );
};

export default OperationTypePage;