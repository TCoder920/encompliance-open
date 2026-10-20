import React, { useState, useRef, useCallback } from 'react';
import { Upload, X, Camera, Plus, Loader2, AlertCircle } from 'lucide-react';

export interface TaskPhoto {
  file: File;
  preview: string;
  label: string;
}

interface TaskPhotoUploaderProps {
  photos: TaskPhoto[];
  onPhotosChange: (photos: TaskPhoto[]) => void;
  disabled?: boolean;
  title?: string;
  description?: string;
}

const TaskPhotoUploader: React.FC<TaskPhotoUploaderProps> = ({
  photos,
  onPhotosChange,
  disabled = false,
  title = "Reference Photos",
  description = "Upload photos to provide visual guidance for this task"
}) => {
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedPhoto, setSelectedPhoto] = useState<TaskPhoto | null>(null);

  const handleFiles = useCallback(async (files: FileList | File[]) => {
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

    // Convert files to data URLs to avoid CSP issues with blob URLs
    const newPhotos: TaskPhoto[] = await Promise.all(
      validFiles.map(async (file, index) => {
        return new Promise<TaskPhoto>((resolve) => {
          const reader = new FileReader();
          reader.onload = (e) => {
            resolve({
              file,
              preview: e.target?.result as string,
              label: `Pre-task photo #${photos.length + index + 1}`
            });
          };
          reader.readAsDataURL(file);
        });
      })
    );

    onPhotosChange([...photos, ...newPhotos]);
  }, [disabled, photos, onPhotosChange]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFiles(e.dataTransfer.files).catch(console.error);
    }
  }, [handleFiles]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
  }, []);

  const removePhoto = (index: number) => {
    if (disabled) return;

    const updatedPhotos = photos.filter((_, i) => i !== index);
    
    // No need to revoke data URLs
    onPhotosChange(updatedPhotos);
  };

  const updatePhotoLabel = (index: number, newLabel: string) => {
    if (disabled) return;

    const updatedPhotos = [...photos];
    updatedPhotos[index] = { ...updatedPhotos[index], label: newLabel };
    onPhotosChange(updatedPhotos);
  };

  const triggerFileInput = () => {
    if (disabled) return;
    fileInputRef.current?.click();
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFiles(files).catch(console.error);
    }
    // Reset input
    e.target.value = '';
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
            <Camera className="h-5 w-5 mr-2" />
            {title}
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400">{description}</p>
        </div>
      </div>

      {/* Drop Zone */}
      <div
        className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
          dragActive
            ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
            : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'
        } ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={triggerFileInput}
      >
        <Upload className="h-8 w-8 text-gray-400 mx-auto mb-2" />
        <p className="text-gray-600 dark:text-gray-400 mb-1">
          Drop reference photos here or click to browse
        </p>
        <p className="text-xs text-gray-500 dark:text-gray-500">
          Supports JPG, PNG, HEIC formats. Max 50MB per file.
        </p>
      </div>

      {/* Photo Grid */}
      {photos.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {photos.map((photo, index) => (
            <div key={index} className="relative group">
              <div className="aspect-square bg-gray-100 dark:bg-gray-800 rounded-lg overflow-hidden cursor-pointer" onClick={() => setSelectedPhoto(photo)}>
                <img
                  src={photo.preview}
                  alt={photo.label}
                  className="w-full h-full object-cover"
                />
              </div>

              {/* Remove Button */}
              {!disabled && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    removePhoto(index);
                  }}
                  className="absolute top-2 right-2 bg-red-600 text-white rounded-full p-1 opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <X className="h-3 w-3" />
                </button>
              )}

              {/* Label Input */}
              <input
                type="text"
                value={photo.label}
                onChange={(e) => updatePhotoLabel(index, e.target.value)}
                disabled={disabled}
                className="mt-2 w-full text-xs border border-gray-300 dark:border-gray-600 rounded px-2 py-1 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                placeholder="Photo label..."
              />
            </div>
          ))}
        </div>
      )}

      {/* Hidden File Input */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept="image/*,.heic"
        className="hidden"
        onChange={handleFileInputChange}
      />

      {selectedPhoto && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50"
          onClick={() => setSelectedPhoto(null)}
        >
          <div className="relative max-w-3xl max-h-[80vh]">
            <img 
              src={selectedPhoto.preview}
              alt={selectedPhoto.label}
              className="max-w-full max-h-[80vh] object-contain rounded-lg"
            />
            <p className="text-white text-center mt-4 text-lg">{selectedPhoto.label}</p>
          </div>
          <button
            onClick={() => setSelectedPhoto(null)}
            className="absolute top-4 right-4 text-white hover:text-gray-300"
          >
            <X className="h-8 w-8" />
          </button>
        </div>
      )}
    </div>
  );
};

export default TaskPhotoUploader; 