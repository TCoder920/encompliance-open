/*
  Description: AssignmentImageUploader component. Provides unlimited multi-file image upload interface for assignment before/after photos with HEIC support.
  Purpose: Allows users to upload multiple images with labels and descriptions for task assignments, supporting all image formats including Apple's HEIC.
*/
import React, { useState, useRef, useCallback } from 'react';
import { Upload, X, Image as ImageIcon, Tag, FileText, Camera, AlertCircle, CheckCircle, Plus, Loader2 } from 'lucide-react';

export interface AssignmentImage {
  id?: number;
  file?: File;
  url?: string;
  type: 'before' | 'after';
  label?: string;
  uploading?: boolean;
  error?: string;
}

interface AssignmentImageUploaderProps {
  assignmentId: number;
  requiresBeforePhotos?: boolean;
  requiresAfterPhotos?: boolean;
  photoInstructions?: string;
  existingImages?: AssignmentImage[];
  onImagesChange: (images: AssignmentImage[]) => void;
  onUploadComplete?: (images: AssignmentImage[]) => void;
  disabled?: boolean;
}

const AssignmentImageUploader: React.FC<AssignmentImageUploaderProps> = ({
  assignmentId,
  requiresBeforePhotos = false,
  requiresAfterPhotos = false,
  photoInstructions,
  existingImages = [],
  onImagesChange,
  onUploadComplete,
  disabled = false
}) => {
  const [images, setImages] = useState<AssignmentImage[]>(existingImages);
  const [dragActive, setDragActive] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<Record<string, number>>({});
  const fileInputRef = useRef<HTMLInputElement>(null);

  const updateImages = useCallback((newImages: AssignmentImage[]) => {
    setImages(newImages);
    onImagesChange(newImages);
  }, [onImagesChange]);

  const uploadImage = async (file: File, type: 'before' | 'after', label?: string): Promise<AssignmentImage> => {
    const tempId = `temp-${Date.now()}-${Math.random()}`;
    
    const formData = new FormData();
    formData.append('files', file);
    formData.append('image_type', type);
    if (label) formData.append('labels', label);

    try {
      // Update progress
      setUploadProgress(prev => ({ ...prev, [tempId]: 0 }));

      const response = await fetch(`/api/assignments/${assignmentId}/images/upload`, {
        method: 'POST',
        body: formData,
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'x-token': localStorage.getItem('token') || ''
        }
      });

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`);
      }

      const result = await response.json();
      
      // Complete progress
      setUploadProgress(prev => ({ ...prev, [tempId]: 100 }));
      
      setTimeout(() => {
        setUploadProgress(prev => {
          const newProgress = { ...prev };
          delete newProgress[tempId];
          return newProgress;
        });
      }, 1000);

      // Handle the response format from ImageUploadResponse
      const uploadedImage = result.images && result.images.length > 0 ? result.images[0] : result;
      
      return {
        id: uploadedImage.id,
        url: `/api/assignments/${assignmentId}/images/${uploadedImage.id}`,
        type: uploadedImage.image_type,
        label: uploadedImage.label
      };
    } catch (error) {
      console.error('Upload error:', error);
      throw error;
    }
  };

  const handleFiles = async (files: FileList | File[], type: 'before' | 'after') => {
    if (disabled) return;

    const fileArray = Array.from(files);
    const validFiles = fileArray.filter(file => {
      const isValidType = file.type.startsWith('image/') || file.name.toLowerCase().endsWith('.heic');
      const isValidSize = file.size <= 50 * 1024 * 1024; // 50MB limit
      return isValidType && isValidSize;
    });

    if (validFiles.length === 0) {
      alert('Please select valid image files (including HEIC format). Maximum size is 50MB per file.');
      return;
    }

    // Add temporary images with uploading state
    const tempImages: AssignmentImage[] = validFiles.map((file, index) => ({
      file,
      type,
      label: `${type.charAt(0).toUpperCase() + type.slice(1)} Photo ${images.filter(img => img.type === type).length + index + 1}`,
      uploading: true
    }));

    const newImages = [...images, ...tempImages];
    updateImages(newImages);

    // Upload files
    try {
      const uploadPromises = validFiles.map(async (file, index) => {
        const tempImage = tempImages[index];
        try {
          const uploadedImage = await uploadImage(file, type, tempImage.label);
          return uploadedImage;
        } catch (error) {
          return {
            ...tempImage,
            uploading: false,
            error: error instanceof Error ? error.message : 'Upload failed'
          };
        }
      });

      const uploadResults = await Promise.all(uploadPromises);
      
      // Replace temp images with results
      const finalImages = newImages.map(img => {
        if (img.uploading) {
          const resultIndex = tempImages.findIndex(temp => temp === img);
          return uploadResults[resultIndex] || img;
        }
        return img;
      });

      updateImages(finalImages);
      
      if (onUploadComplete) {
        onUploadComplete(finalImages);
      }
    } catch (error) {
      console.error('Batch upload error:', error);
    }
  };

  const handleDrop = useCallback((e: React.DragEvent, type: 'before' | 'after') => {
    e.preventDefault();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFiles(e.dataTransfer.files, type);
    }
  }, [disabled, images]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
  }, []);

  const removeImage = async (index: number) => {
    if (disabled) return;

    const image = images[index];
    
    // If it's an uploaded image, delete from server
    if (image.id) {
      try {
        await fetch(`/api/assignments/${assignmentId}/images/${image.id}`, {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'x-token': localStorage.getItem('token') || ''
          }
        });
      } catch (error) {
        console.error('Delete error:', error);
        alert('Failed to delete image from server');
        return;
      }
    }

    const newImages = images.filter((_, i) => i !== index);
    updateImages(newImages);
  };

  const updateImageLabel = async (index: number, newLabel: string) => {
    if (disabled) return;

    const updatedImages = [...images];
    updatedImages[index] = { ...updatedImages[index], label: newLabel };
    updateImages(updatedImages);

    // Update on server if it's an uploaded image
    const image = updatedImages[index];
    if (image.id) {
      try {
        await fetch(`/api/assignments/${assignmentId}/images/${image.id}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'x-token': localStorage.getItem('token') || ''
          },
          body: JSON.stringify({ label: newLabel })
        });
      } catch (error) {
        console.error('Label update error:', error);
      }
    }
  };

  const triggerFileInput = (type: 'before' | 'after') => {
    if (disabled) return;
    
    if (fileInputRef.current) {
      fileInputRef.current.dataset.uploadType = type;
      fileInputRef.current.click();
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    const type = e.target.dataset.uploadType as 'before' | 'after';
    
    if (files && files.length > 0) {
      handleFiles(files, type);
    }
    
    // Reset input
    e.target.value = '';
  };

  const getPhotoRequirementStatus = () => {
    const beforePhotos = images.filter(img => img.type === 'before' && !img.uploading && !img.error);
    const afterPhotos = images.filter(img => img.type === 'after' && !img.uploading && !img.error);
    
    const beforeMet = !requiresBeforePhotos || beforePhotos.length > 0;
    const afterMet = !requiresAfterPhotos || afterPhotos.length > 0;
    
    return { beforeMet, afterMet, allMet: beforeMet && afterMet };
  };

  const { beforeMet, afterMet, allMet } = getPhotoRequirementStatus();

  const renderPhotoSection = (type: 'before' | 'after', required: boolean) => {
    const typeImages = images.filter(img => img.type === type);
    const title = type === 'before' ? 'Before Photos' : 'After Photos';
    const isMet = type === 'before' ? beforeMet : afterMet;

    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
            <Camera className="h-5 w-5 mr-2" />
            {title}
            {required && (
              <span className="text-red-500 ml-1">*</span>
            )}
            {required && isMet && (
              <CheckCircle className="h-4 w-4 text-green-600 ml-2" />
            )}
            {required && !isMet && (
              <AlertCircle className="h-4 w-4 text-red-600 ml-2" />
            )}
          </h3>
          <button
            onClick={() => triggerFileInput(type)}
            disabled={disabled}
            className="flex items-center px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
          >
            <Plus className="h-4 w-4 mr-1" />
            Add Photo
          </button>
        </div>

        {/* Drop Zone */}
        <div
          className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
            dragActive
              ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
              : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'
          } ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
          onDrop={(e) => handleDrop(e, type)}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onClick={() => triggerFileInput(type)}
        >
          <Upload className="h-8 w-8 text-gray-400 mx-auto mb-2" />
          <p className="text-gray-600 dark:text-gray-400 mb-1">
            Drop {type} photos here or click to browse
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-500">
            Supports JPG, PNG, HEIC formats. Max 50MB per file.
          </p>
        </div>

        {/* Photo Grid */}
        {typeImages.length > 0 && (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {typeImages.map((image, index) => (
              <div key={index} className="relative group">
                <div className="aspect-square bg-gray-100 dark:bg-gray-800 rounded-lg overflow-hidden">
                  {image.uploading ? (
                    <div className="w-full h-full flex items-center justify-center">
                      <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
                    </div>
                  ) : image.error ? (
                    <div className="w-full h-full flex items-center justify-center bg-red-50 dark:bg-red-900/20">
                      <AlertCircle className="h-8 w-8 text-red-600" />
                    </div>
                  ) : image.url ? (
                    <img
                      src={image.url}
                      alt={image.label || `${type} photo`}
                      className="w-full h-full object-cover"
                    />
                  ) : image.file ? (
                    <div className="w-full h-full flex items-center justify-center">
                      <Camera className="h-8 w-8 text-gray-400" />
                    </div>
                  ) : null}
                </div>

                {/* Remove Button */}
                {!disabled && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      removeImage(images.indexOf(image));
                    }}
                    className="absolute top-2 right-2 bg-red-600 text-white rounded-full p-1 opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    <X className="h-3 w-3" />
                  </button>
                )}

                {/* Label Input */}
                <input
                  type="text"
                  value={image.label || ''}
                  onChange={(e) => updateImageLabel(images.indexOf(image), e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      e.stopPropagation();
                    }
                  }}
                  disabled={disabled || image.uploading}
                  className="mt-2 w-full text-xs border border-gray-300 dark:border-gray-600 rounded px-2 py-1 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  placeholder="Photo label..."
                />

                {/* Error Message */}
                {image.error && (
                  <p className="mt-1 text-xs text-red-600">{image.error}</p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Instructions */}
      {photoInstructions && (
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
          <h3 className="text-sm font-medium text-blue-800 dark:text-blue-300 mb-2">Photo Instructions</h3>
          <p className="text-sm text-blue-700 dark:text-blue-400">{photoInstructions}</p>
        </div>
      )}

      {/* Requirements Status */}
      {(requiresBeforePhotos || requiresAfterPhotos) && (
        <div className={`p-4 rounded-lg border ${
          allMet 
            ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800' 
            : 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800'
        }`}>
          <div className="flex items-center">
            {allMet ? (
              <CheckCircle className="h-5 w-5 text-green-600 mr-2" />
            ) : (
              <AlertCircle className="h-5 w-5 text-yellow-600 mr-2" />
            )}
            <span className={`text-sm font-medium ${
              allMet ? 'text-green-800 dark:text-green-300' : 'text-yellow-800 dark:text-yellow-300'
            }`}>
              {allMet ? 'All photo requirements met' : 'Photo requirements pending'}
            </span>
          </div>
        </div>
      )}

      {/* Before Photos Section */}
      {requiresBeforePhotos && renderPhotoSection('before', true)}

      {/* After Photos Section */}
      {requiresAfterPhotos && renderPhotoSection('after', true)}

      {/* Hidden File Input */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept="image/*,.heic"
        onChange={handleFileInputChange}
        className="hidden"
      />
    </div>
  );
};

export default AssignmentImageUploader; 