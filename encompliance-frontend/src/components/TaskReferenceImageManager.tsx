/*
  Description: TaskReferenceImageManager component for managing task reference images
  Purpose: Allows users to upload, edit, delete, and reorder reference images for tasks
*/

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Upload, X, Camera, Plus, Loader2, AlertCircle, Edit2, Save, RotateCcw } from 'lucide-react';
import { taskReferenceImageService, TaskReferenceImage } from '../services/taskReferenceImageService';

interface TaskReferenceImageManagerProps {
  taskId: number;
  disabled?: boolean;
  title?: string;
  description?: string;
}

const TaskReferenceImageManager: React.FC<TaskReferenceImageManagerProps> = ({
  taskId,
  disabled = false,
  title = "Reference Photos",
  description = "Upload photos to provide visual guidance for this task"
}) => {
  const [images, setImages] = useState<TaskReferenceImage[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [editingImage, setEditingImage] = useState<number | null>(null);
  const [editLabel, setEditLabel] = useState('');
  const [selectedImage, setSelectedImage] = useState<TaskReferenceImage | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Load existing images
  useEffect(() => {
    const loadImages = async () => {
      try {
        setLoading(true);
        const existingImages = await taskReferenceImageService.getTaskReferenceImages(taskId);
        setImages(existingImages);
      } catch (error) {
        console.error('Failed to load reference images:', error);
      } finally {
        setLoading(false);
      }
    };

    loadImages();
  }, [taskId]);

  const handleFiles = useCallback(async (files: FileList | File[]) => {
    if (disabled || uploading) return;

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

    try {
      setUploading(true);
      
      const labels = validFiles.map((_, index) => 
        `Pre-task photo #${images.length + index + 1}`
      );

      const response = await taskReferenceImageService.uploadImages(
        taskId,
        validFiles,
        labels
      );

      // Reload images to get the updated list
      const updatedImages = await taskReferenceImageService.getTaskReferenceImages(taskId);
      setImages(updatedImages);
      
    } catch (error) {
      console.error('Upload error:', error);
      alert('Failed to upload images. Please try again.');
    } finally {
      setUploading(false);
    }
  }, [disabled, uploading, taskId, images.length]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFiles(e.dataTransfer.files);
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

  const deleteImage = async (imageId: number) => {
    if (disabled) return;

    try {
      await taskReferenceImageService.deleteImage(taskId, imageId);
      setImages(prev => prev.filter(img => img.id !== imageId));
    } catch (error) {
      console.error('Delete error:', error);
      alert('Failed to delete image. Please try again.');
    }
  };

  const startEditLabel = (image: TaskReferenceImage) => {
    setEditingImage(image.id);
    setEditLabel(image.label || '');
  };

  const saveLabel = async () => {
    if (editingImage === null) return;

    try {
      const updatedImage = await taskReferenceImageService.updateImageMetadata(
        taskId,
        editingImage,
        { label: editLabel }
      );

      setImages(prev => prev.map(img => 
        img.id === editingImage ? { ...img, label: updatedImage.label } : img
      ));
      
      setEditingImage(null);
      setEditLabel('');
    } catch (error) {
      console.error('Update error:', error);
      alert('Failed to update image label. Please try again.');
    }
  };

  const cancelEdit = () => {
    setEditingImage(null);
    setEditLabel('');
  };

  const triggerFileInput = () => {
    if (disabled || uploading) return;
    fileInputRef.current?.click();
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFiles(files);
    }
    // Reset input
    e.target.value = '';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="h-6 w-6 animate-spin" />
        <span className="ml-2">Loading reference images...</span>
      </div>
    );
  }

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
        } ${disabled || uploading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
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
      {images.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {images.map((image) => (
            <div key={image.id} className="relative group">
              <div className="aspect-square bg-gray-100 dark:bg-gray-800 rounded-lg overflow-hidden cursor-pointer" onClick={() => setSelectedImage(image)}>
                <img
                  src={taskReferenceImageService.getImageUrl(taskId, image.id)}
                  alt={image.label || image.original_file_name}
                  className="w-full h-full object-cover"
                />
              </div>

              {/* Action buttons */}
              {!disabled && (
                <div className="absolute top-2 right-2 flex space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      startEditLabel(image);
                    }}
                    className="bg-blue-600 text-white rounded-full p-1 hover:bg-blue-700"
                  >
                    <Edit2 className="h-3 w-3" />
                  </button>
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteImage(image.id);
                    }}
                    className="bg-red-600 text-white rounded-full p-1 hover:bg-red-700"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </div>
              )}

              {/* Label Input */}
              {editingImage === image.id ? (
                <div className="mt-2 flex items-center space-x-1">
                  <input
                    type="text"
                    value={editLabel}
                    onChange={(e) => setEditLabel(e.target.value)}
                    className="flex-1 text-xs border border-gray-300 dark:border-gray-600 rounded px-2 py-1 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    placeholder="Photo label..."
                    autoFocus
                  />
                  <button
                    type="button"
                    onClick={saveLabel}
                    className="bg-green-600 text-white rounded p-1 hover:bg-green-700"
                  >
                    <Save className="h-3 w-3" />
                  </button>
                  <button
                    type="button"
                    onClick={cancelEdit}
                    className="bg-gray-600 text-white rounded p-1 hover:bg-gray-700"
                  >
                    <RotateCcw className="h-3 w-3" />
                  </button>
                </div>
              ) : (
                <div className="mt-2 text-xs text-gray-700 dark:text-gray-300 truncate">
                  {image.label || image.original_file_name}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Empty state */}
      {images.length === 0 && (
        <div className="text-center py-8 text-gray-500 dark:text-gray-400">
          <Camera className="h-12 w-12 mx-auto mb-4 opacity-50" />
          <p>No reference photos uploaded yet.</p>
          <p className="text-sm">Add photos to provide visual guidance for this task.</p>
        </div>
      )}

      {/* Hidden File Input */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept="image/*,.heic"
        onChange={handleFileInputChange}
        className="hidden"
      />

      {selectedImage && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50"
          onClick={() => setSelectedImage(null)}
        >
          <div className="relative max-w-3xl max-h-[80vh]">
            <img 
              src={taskReferenceImageService.getImageUrl(taskId, selectedImage.id)}
              alt={selectedImage.label || selectedImage.original_file_name}
              className="max-w-full max-h-[80vh] object-contain rounded-lg"
            />
            <p className="text-white text-center mt-4 text-lg">{selectedImage.label}</p>
          </div>
          <button
            onClick={() => setSelectedImage(null)}
            className="absolute top-4 right-4 text-white hover:text-gray-300"
          >
            <X className="h-8 w-8" />
          </button>
        </div>
      )}
    </div>
  );
};

export default TaskReferenceImageManager; 