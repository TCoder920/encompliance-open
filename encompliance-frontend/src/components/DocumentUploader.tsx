/*
  Description: DocumentUploader component. Provides a file upload interface for users to submit compliance documents with optional custom labels.
  Purpose: Allows users to upload, validate, and manage documents for compliance analysis and storage with custom labeling.
*/
import React, { useState, useRef } from 'react';
import { Upload, FileText, X, Check, AlertCircle, Tag } from 'lucide-react';
import pdfService from '../services/pdfService';
import documentService from '../services/documentService';

interface DocumentUploaderProps {
  onUploadComplete?: (file: File, customLabel?: string) => void;
  allowedFileTypes?: string[];
  maxSizeMB?: number;
  enableCustomLabel?: boolean;
  enableExpirationTracking?: boolean;  // New prop for Pro Mode facility administrators
}

const DocumentUploader: React.FC<DocumentUploaderProps> = ({
  onUploadComplete,
  allowedFileTypes = ['.pdf', '.docx', '.doc', '.txt'],
  maxSizeMB = 50,
  enableCustomLabel = true,
  enableExpirationTracking = false
}) => {
  const [dragActive, setDragActive] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [customLabel, setCustomLabel] = useState<string>('');
  const [expirationDate, setExpirationDate] = useState<string>('');
  const [documentType, setDocumentType] = useState<string>('');
  const [issuingAuthority, setIssuingAuthority] = useState<string>('');
  const [renewalRequired, setRenewalRequired] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadComplete, setUploadComplete] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDrag = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const validateFile = (file: File): { valid: boolean; error?: string } => {
    // Validate file type
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!allowedFileTypes.includes(fileExtension)) {
      const error = `File type not allowed. Please upload ${allowedFileTypes.join(', ')} files.`;
      return { valid: false, error };
    }
    
    // Validate file size
    const fileSize = file.size / 1024 / 1024; // Convert to MB
    if (fileSize > maxSizeMB) {
      const error = `File size exceeds ${maxSizeMB}MB limit.`;
      return { valid: false, error };
    }
    
    return { valid: true };
  };

  const validateCustomLabel = (label: string): { valid: boolean; error?: string } => {
    if (label && label.length > 255) {
      return { valid: false, error: 'Custom label cannot exceed 255 characters' };
    }
    return { valid: true };
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      handleFileSelection(file);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      handleFileSelection(file);
    }
  };

  const handleFileSelection = (file: File) => {
    const validation = validateFile(file);
    
    if (!validation.valid) {
      setError(validation.error || 'File validation failed');
      return;
    }
    
    setError(null);
    setFile(file);
  };

  const handleUpload = async () => {
    if (!file) return;

    // Validate custom label
    const labelValidation = validateCustomLabel(customLabel);
    if (!labelValidation.valid) {
      setError(labelValidation.error || 'Label validation failed');
      return;
    }

    setUploading(true);
    setError(null);
    
    try {
      // Prepare expiration data if expiration tracking is enabled
      let expirationData = undefined;
      if (enableExpirationTracking && (expirationDate || documentType || issuingAuthority || renewalRequired)) {
        expirationData = {
          expirationDate: expirationDate || undefined,
          documentType: documentType || undefined,
          issuingAuthority: issuingAuthority || undefined,
          renewalRequired: renewalRequired
        };
      }

      // Upload the file using documentService with custom label and expiration data
      const uploadResult = await documentService.uploadDocument(
        file, 
        customLabel.trim() || undefined,
        expirationData
      );
      
      if (onUploadComplete) {
        onUploadComplete(file, customLabel.trim() || undefined);
      }
      
      // Force refresh of document list after upload
      await documentService.refreshDocumentCache(true);
      setUploadComplete(true);
    } catch (error) {
      setError('An error occurred while processing the file.');
    } finally {
      setUploading(false);
    }
  };

  const handleButtonClick = () => {
    inputRef.current?.click();
  };

  const resetUpload = () => {
    setFile(null);
    setCustomLabel('');
    setExpirationDate('');
    setDocumentType('');
    setIssuingAuthority('');
    setRenewalRequired(false);
    setError(null);
    setUploading(false);
    setUploadComplete(false);
    if (inputRef.current) {
      inputRef.current.value = '';
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' bytes';
    else if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    else return (bytes / 1048576).toFixed(1) + ' MB';
  };

  return (
    <div className="w-full">
      {!file ? (
        <div 
          className={`border-2 border-dashed rounded-lg p-6 text-center ${
            dragActive 
              ? 'border-navy-blue dark:border-blue-400 bg-blue-50 dark:bg-blue-900/20' 
              : 'border-gray-300 dark:border-gray-600'
          }`}
          onDragEnter={handleDrag}
          onDragOver={handleDrag}
          onDragLeave={handleDrag}
          onDrop={handleDrop}
        >
          <input
            ref={inputRef}
            type="file"
            className="hidden"
            onChange={handleChange}
            accept={allowedFileTypes.join(',')}
          />
          
          <Upload className="h-12 w-12 mx-auto text-navy-blue dark:text-blue-400 mb-4" />
          
          <h3 className="text-lg font-bold text-navy-blue dark:text-white mb-2">Upload Document</h3>
          
          <p className="text-gray-600 dark:text-gray-300 mb-4">
            Drag and drop your file here, or click to browse
          </p>
          
          <button
            onClick={handleButtonClick}
            className="bg-navy-blue dark:bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-800 dark:hover:bg-blue-700 transition duration-200"
          >
            Select File
          </button>
          
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-4">
            Supported formats: {allowedFileTypes.join(', ')} (Max size: {maxSizeMB}MB)
          </p>
        </div>
      ) : (
        <div className="border border-gray-300 dark:border-gray-600 rounded-lg p-4">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center">
              <FileText className="h-8 w-8 text-navy-blue dark:text-blue-400 mr-3" />
              <div>
                <p className="font-medium text-navy-blue dark:text-white">{file.name}</p>
                <p className="text-sm text-gray-500 dark:text-gray-400">{formatFileSize(file.size)}</p>
              </div>
            </div>
            
            {!uploading && !uploadComplete && (
              <button 
                onClick={resetUpload}
                className="text-gray-500 hover:text-red-500"
              >
                <X className="h-5 w-5" />
              </button>
            )}
            
            {uploadComplete && (
              <div className="flex items-center text-green-600">
                <Check className="h-5 w-5 mr-1" />
                <span className="text-sm">Upload complete</span>
              </div>
            )}
          </div>

          {enableCustomLabel && !uploadComplete && (
            <div className="mb-4">
              <label htmlFor="customLabel" className="flex items-center text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                <Tag className="h-4 w-4 mr-1" />
                Custom Label (Optional)
              </label>
              <input
                id="customLabel"
                type="text"
                value={customLabel}
                onChange={(e) => setCustomLabel(e.target.value)}
                placeholder="e.g., Policy, Training, Rosters"
                maxLength={255}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-navy-blue dark:focus:ring-blue-500 focus:border-transparent"
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Add a custom label to organize your document (max 255 characters)
              </p>
            </div>
          )}

          {enableExpirationTracking && !uploadComplete && (
            <div className="mb-4 p-4 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
              <h4 className="text-sm font-medium text-navy-blue dark:text-blue-400 mb-3">Document Expiration Tracking</h4>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label htmlFor="documentType" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Document Type
                  </label>
                  <select
                    id="documentType"
                    value={documentType}
                    onChange={(e) => setDocumentType(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-navy-blue dark:focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="">Select type...</option>
                    <option value="license">License</option>
                    <option value="certification">Certification</option>
                    <option value="permit">Permit</option>
                    <option value="policy">Policy</option>
                    <option value="insurance">Insurance</option>
                    <option value="contract">Contract</option>
                    <option value="other">Other</option>
                  </select>
                </div>

                <div>
                  <label htmlFor="expirationDate" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Expiration Date
                  </label>
                  <input
                    id="expirationDate"
                    type="date"
                    value={expirationDate}
                    onChange={(e) => setExpirationDate(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-navy-blue dark:focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                <div className="md:col-span-2">
                  <label htmlFor="issuingAuthority" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Issuing Authority (Optional)
                  </label>
                  <input
                    id="issuingAuthority"
                    type="text"
                    value={issuingAuthority}
                    onChange={(e) => setIssuingAuthority(e.target.value)}
                    placeholder="e.g., State Health Department, DOT, etc."
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-navy-blue dark:focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                <div className="md:col-span-2">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={renewalRequired}
                      onChange={(e) => setRenewalRequired(e.target.checked)}
                      className="h-4 w-4 text-navy-blue dark:text-blue-500 focus:ring-navy-blue dark:focus:ring-blue-500 border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 rounded"
                    />
                    <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">Renewal Required</span>
                  </label>
                </div>
              </div>
              
              <p className="text-xs text-navy-blue dark:text-blue-400 mt-2">
                Set expiration tracking to receive automated reminders before this document expires.
              </p>
            </div>
          )}

          {!uploading && !uploadComplete && (
            <button
              onClick={handleUpload}
              className="w-full bg-navy-blue text-white px-4 py-2 rounded hover:bg-blue-800 transition duration-200"
            >
              Upload Document
            </button>
          )}
          
          {uploading && (
            <div className="w-full bg-gray-200 rounded-full h-2.5">
              <div className="bg-navy-blue h-2.5 rounded-full animate-pulse w-full"></div>
            </div>
          )}
        </div>
      )}
      
      {error && (
        <div className="mt-4 flex items-center p-3 bg-red-50 border border-red-200 rounded-lg">
          <AlertCircle className="h-5 w-5 text-red-500 mr-2" />
          <span className="text-red-700 text-sm">{error}</span>
        </div>
      )}
    </div>
  );
};

export default DocumentUploader;