/*
  Description: DocumentLabelEditor component. Provides inline editing functionality for document custom labels.
  Purpose: Allows users to edit and update custom labels for their uploaded documents.
*/
import React, { useState } from 'react';
import { Edit3, Save, X, Tag } from 'lucide-react';
import documentService from '../services/documentService';

interface DocumentLabelEditorProps {
  documentId: number;
  currentLabel?: string;
  filename: string;
  onLabelUpdate?: (newLabel?: string) => void;
  onTitleClick?: () => void;
  className?: string;
}

const DocumentLabelEditor: React.FC<DocumentLabelEditorProps> = ({
  documentId,
  currentLabel,
  filename,
  onLabelUpdate,
  onTitleClick,
  className = ''
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(currentLabel || '');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleStartEdit = () => {
    setIsEditing(true);
    setEditValue(currentLabel || '');
    setError(null);
  };

  const handleCancel = () => {
    setIsEditing(false);
    setEditValue(currentLabel || '');
    setError(null);
  };

  const handleSave = async () => {
    if (editValue.length > 255) {
      setError('Label cannot exceed 255 characters');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      console.log(`[DEBUG] DocumentLabelEditor: Attempting to save label "${editValue}" for document ${documentId}`);
      const trimmedValue = editValue.trim();
      await documentService.updateDocumentLabel(
        documentId,
        trimmedValue || undefined
      );
      
      console.log(`[DEBUG] DocumentLabelEditor: Label save successful for document ${documentId}`);
      setIsEditing(false);
      if (onLabelUpdate) {
        onLabelUpdate(trimmedValue || undefined);
      }
    } catch (err: any) {
      console.error(`[DEBUG] DocumentLabelEditor: Error saving label for document ${documentId}:`, err);
      
      let errorMessage = 'Failed to update label. Please try again.';
      
      // Provide more specific error messages based on the error type
      if (err.response?.status === 404) {
        errorMessage = 'This document cannot be labeled. Only manually uploaded documents support custom labels. Regulatory documents do not support labeling.';
      } else if (err.response?.status === 401) {
        errorMessage = 'Authentication expired. Please log in again.';
      } else if (err.response?.status === 403) {
        errorMessage = 'You do not have permission to edit this document.';
      } else if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail;
      }
      
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSave();
    } else if (e.key === 'Escape') {
      handleCancel();
    }
  };

  const displayTitle = currentLabel || filename;
  const displaySubtitle = currentLabel ? filename : null;

  if (isEditing) {
    return (
      <div className={`${className}`}>
        <div className="flex items-center space-x-2">
          <Tag className="h-4 w-4 text-gray-500 flex-shrink-0" />
          <input
            type="text"
            value={editValue}
            onChange={(e) => setEditValue(e.target.value)}
            onKeyDown={handleKeyPress}
            placeholder="Enter custom label..."
            maxLength={255}
            className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            autoFocus
          />
          <button
            onClick={handleSave}
            disabled={isLoading}
            className="p-1 text-green-600 hover:bg-green-50 rounded disabled:opacity-50"
            title="Save label"
          >
            <Save className="h-4 w-4" />
          </button>
          <button
            onClick={handleCancel}
            disabled={isLoading}
            className="p-1 text-gray-500 hover:bg-gray-50 rounded disabled:opacity-50"
            title="Cancel"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
        {displaySubtitle && (
          <div className="text-sm text-gray-600 mt-1 ml-6 truncate">
            {displaySubtitle}
          </div>
        )}
        {error && (
          <div className="text-xs text-red-600 mt-1 ml-6">
            {error}
          </div>
        )}
        <div className="text-xs text-gray-500 mt-1 ml-6">
          Press Enter to save, Escape to cancel
        </div>
      </div>
    );
  }

  return (
    <div className={`${className}`}>
      <div className="flex items-center space-x-2 group">
        <div className="flex-1 min-w-0">
          <div className="flex items-center space-x-2">
            <h3 
              className="text-md font-semibold truncate text-blue-600 hover:text-blue-800 cursor-pointer"
              onClick={onTitleClick}
            >
              {displayTitle}
            </h3>
            <button
              onClick={handleStartEdit}
              className="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-gray-600 rounded transition-opacity"
              title="Edit label"
            >
              <Edit3 className="h-3 w-3" />
            </button>
          </div>
          {displaySubtitle && (
            <div className="text-sm text-gray-600 mt-1 truncate">
              {displaySubtitle}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default DocumentLabelEditor; 