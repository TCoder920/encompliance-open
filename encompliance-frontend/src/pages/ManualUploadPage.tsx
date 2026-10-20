/*
  Description: Manual document upload page component. Allows users to upload compliance documents for analysis and storage.
  Purpose: Provides a user interface for uploading and managing compliance-related files.
*/

import React, { useState } from 'react';
import { FileText, ArrowRight } from 'lucide-react';
import DocumentUploader from '../components/DocumentUploader';
import ErrorMessage from '../components/ErrorMessage';

interface ManualUploadPageProps {
  operationType: string;
  onUploadComplete: () => void;
  onBack: () => void;
  onSkip: () => void;
  navigateTo?: (page: string) => void;
}

const ManualUploadPage: React.FC<ManualUploadPageProps> = ({ operationType, onUploadComplete, onBack, onSkip, navigateTo }) => {
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleUploadComplete = (file: File) => {
    try {
      setUploadedFile(file);
      setIsProcessing(true);
      setError(null);
      
      // Simulate file processing
      setTimeout(() => {
        setIsProcessing(false);
      }, 2000);
    } catch (err) {
      console.error('Upload processing error:', err);
      setError('Failed to process the uploaded file. Please try again.');
      setIsProcessing(false);
    }
  };

  const handleContinue = () => {
    try {
      onUploadComplete();
    } catch (err) {
      console.error('Navigation error:', err);
      setError('Failed to proceed to the next step. Please try again.');
    }
  };

  const handleSkip = () => {
    try {
      if(navigateTo) {
        navigateTo('dashboard');
      } else {
        onSkip();
      }
    } catch (err) {
      console.error('Skip error:', err);
      setError('Failed to skip this step. Please try again.');
    }
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-3xl">
      <div className="bg-white dark:bg-dark-surface rounded-lg shadow-lg p-8 transition-colors duration-300">
        <h1 className="text-3xl font-bold text-navy-blue dark:text-white mb-2 font-times transition-colors duration-300">Upload Your Operations Policy</h1>
        <p className="text-gray-600 dark:text-gray-300 mb-8 transition-colors duration-300">
          Before accessing the regulations, please upload your operation's operational policy for AI-powered analysis and personalized compliance recommendations.
        </p>

        {error && (
          <div className="mb-4">
            <ErrorMessage 
              message={error}
              type="error"
              onClose={() => setError(null)}
            />
          </div>
        )}

        <div className="mb-8">
          <DocumentUploader 
            onUploadComplete={handleUploadComplete}
            allowedFileTypes={['.pdf', '.docx', '.doc', '.txt']}
            maxSizeMB={50}
          />
        </div>

        {uploadedFile && (
          <div className="mt-8">
            <h2 className="text-xl font-bold text-navy-blue dark:text-white mb-4 transition-colors duration-300">Upload Successful</h2>
            <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4 transition-colors duration-300">
              <div className="flex items-start">
                <FileText className="h-6 w-6 text-green-600 dark:text-green-400 mr-3 mt-1 transition-colors duration-300" />
                <div>
                  <p className="font-medium dark:text-white transition-colors duration-300">Your operational policy has been uploaded successfully</p>
                  <p className="text-sm text-gray-600 dark:text-gray-300 mt-1 transition-colors duration-300">
                    File: {uploadedFile.name} ({(uploadedFile.size / 1024 / 1024).toFixed(2)} MB)
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-300 mt-3 transition-colors duration-300">
                    {isProcessing 
                      ? "Your operational policy is being processed..."
                      : "Processing complete! You can now access the compliance tools."}
                  </p>
                </div>
              </div>
            </div>
            
            <div className="mt-6 flex justify-center">
              <button
                onClick={handleContinue}
                disabled={isProcessing}
                className={`${
                  isProcessing 
                    ? 'bg-gray-400 dark:bg-gray-600 cursor-not-allowed'
                    : 'bg-navy-blue dark:bg-blue-700 hover:bg-blue-800 dark:hover:bg-blue-600'
                } text-white px-8 py-3 rounded-lg font-semibold flex items-center transition duration-300`}
              >
                {isProcessing ? 'Processing...' : 'Access Compliance Tools'}
                <ArrowRight className="ml-2 h-5 w-5" />
              </button>
            </div>
          </div>
        )}

        <div className="mt-8 border-t border-gray-200 dark:border-gray-700 pt-6 transition-colors duration-300">
          <h3 className="font-bold text-navy-blue dark:text-white mb-3 transition-colors duration-300">Why Upload Your Operational Policy?</h3>
          <ul className="list-disc pl-5 space-y-2 text-gray-700 dark:text-gray-300 transition-colors duration-300">
            <li>Get personalized compliance recommendations</li>
            <li>Identify potential gaps between your operational policies and current regulations</li>
            <li>Receive AI-powered insights specific to your operation</li>
            <li>Streamline your compliance review process</li>
            <li>Keep your operational policies up-to-date with the latest requirements</li>
          </ul>
        </div>

        <div className="mt-8 pt-6 flex justify-center">
          <button
            onClick={handleSkip}
            className="text-gray-600 dark:text-gray-400 hover:text-navy-blue dark:hover:text-blue-400 transition duration-300"
          >
            Upload Later
          </button>
        </div>
      </div>
    </div>
  );
};

export default ManualUploadPage;