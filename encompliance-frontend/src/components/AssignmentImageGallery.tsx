/*
  Description: AssignmentImageGallery component. Displays assignment images with before/after comparison, editing, and management capabilities.
  Purpose: Provides comprehensive image viewing, editing, and comparison interface for task assignment photos with HEIC support.
*/
import React, { useState, useEffect } from 'react';
import { 
  Image as ImageIcon, 
  Edit3, 
  Trash2, 
  Download, 
  Eye, 
  X, 
  Save, 
  ArrowLeft, 
  ArrowRight,
  Grid,
  Maximize2,
  Tag,
  FileText,
  Calendar,
  User,
  HardDrive
} from 'lucide-react';

interface AssignmentImage {
  id: number;
  assignment_id: number;
  image_type: 'before' | 'after' | 'progress';
  file_name: string;
  original_file_name: string;
  file_size: number;
  original_file_size?: number;
  mime_type: string;
  original_mime_type: string;
  uploaded_by: number;
  uploaded_at: string;
  label?: string;
  description?: string;
  display_order: number;
  conversion_status: string;
  total_storage_bytes: number;
  is_heic_format: boolean;
  conversion_completed: boolean;
}

interface AssignmentImageGalleryProps {
  assignmentId: number;
  imageType?: 'before' | 'after' | 'progress';
  editable?: boolean;
  showComparison?: boolean;
  onImageUpdate?: () => void;
}

const AssignmentImageGallery: React.FC<AssignmentImageGalleryProps> = ({
  assignmentId,
  imageType,
  editable = false,
  showComparison = false,
  onImageUpdate
}) => {
  const [images, setImages] = useState<AssignmentImage[]>([]);
  const [beforeImages, setBeforeImages] = useState<AssignmentImage[]>([]);
  const [afterImages, setAfterImages] = useState<AssignmentImage[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedImage, setSelectedImage] = useState<AssignmentImage | null>(null);
  const [lightboxOpen, setLightboxOpen] = useState(false);
  const [editingImage, setEditingImage] = useState<number | null>(null);
  const [editForm, setEditForm] = useState({ label: '', description: '' });
  const [viewMode, setViewMode] = useState<'grid' | 'comparison'>('grid');

  useEffect(() => {
    loadImages();
  }, [assignmentId, imageType]);

  const loadImages = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const url = imageType 
        ? `/api/assignments/${assignmentId}/images?image_type=${imageType}`
        : `/api/assignments/${assignmentId}/images`;
      
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to load images');
      }

      const imageData = await response.json();
      
      if (showComparison) {
        // Separate images by type for comparison view
        const before = imageData.filter((img: AssignmentImage) => img.image_type === 'before');
        const after = imageData.filter((img: AssignmentImage) => img.image_type === 'after');
        setBeforeImages(before);
        setAfterImages(after);
        setViewMode('comparison');
      } else {
        setImages(imageData);
      }
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load images');
    } finally {
      setLoading(false);
    }
  };

  const handleImageClick = (image: AssignmentImage) => {
    setSelectedImage(image);
    setLightboxOpen(true);
  };

  const handleEdit = (image: AssignmentImage) => {
    setEditingImage(image.id);
    setEditForm({
      label: image.label || '',
      description: image.description || ''
    });
  };

  const handleSaveEdit = async (imageId: number) => {
    try {
      const response = await fetch(`/api/assignments/${assignmentId}/images/${imageId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(editForm)
      });

      if (!response.ok) {
        throw new Error('Failed to update image');
      }

      setEditingImage(null);
      loadImages();
      
      if (onImageUpdate) {
        onImageUpdate();
      }
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update image');
    }
  };

  const handleDelete = async (imageId: number) => {
    if (!confirm('Are you sure you want to delete this image?')) {
      return;
    }

    try {
      const response = await fetch(`/api/assignments/${assignmentId}/images/${imageId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to delete image');
      }

      loadImages();
      
      if (onImageUpdate) {
        onImageUpdate();
      }
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete image');
    }
  };

  const handleDownload = (image: AssignmentImage, original: boolean = false) => {
    const url = `/api/assignments/${assignmentId}/images/${image.id}${original ? '?original=true' : ''}`;
    const link = document.createElement('a');
    link.href = url;
    link.download = original ? image.original_file_name : image.file_name;
    link.click();
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    else if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    else if (bytes < 1073741824) return (bytes / 1048576).toFixed(1) + ' MB';
    else return (bytes / 1073741824).toFixed(1) + ' GB';
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getImageUrl = (image: AssignmentImage) => {
    return `/api/assignments/${assignmentId}/images/${image.id}`;
  };

  const renderImageCard = (image: AssignmentImage) => (
    <div key={image.id} className="border border-gray-300 dark:border-gray-600 rounded-lg overflow-hidden bg-white dark:bg-dark-surface">
      {/* Image */}
      <div className="relative aspect-square bg-gray-100 dark:bg-gray-700">
        <img
          src={getImageUrl(image)}
          alt={image.label || image.original_file_name}
          className="w-full h-full object-cover cursor-pointer hover:opacity-90 transition-opacity"
          onClick={() => handleImageClick(image)}
        />
        
        {/* HEIC Badge */}
        {image.is_heic_format && (
          <div className="absolute top-2 left-2 bg-blue-500 text-white text-xs px-2 py-1 rounded">
            HEIC
          </div>
        )}
        
        {/* Actions */}
        <div className="absolute top-2 right-2 flex space-x-1">
          <button
            onClick={() => handleImageClick(image)}
            className="bg-black bg-opacity-50 text-white p-1 rounded hover:bg-opacity-70"
          >
            <Eye className="h-4 w-4" />
          </button>
          
          {editable && (
            <>
              <button
                onClick={() => handleEdit(image)}
                className="bg-black bg-opacity-50 text-white p-1 rounded hover:bg-opacity-70"
              >
                <Edit3 className="h-4 w-4" />
              </button>
              
              <button
                onClick={() => handleDelete(image.id)}
                className="bg-black bg-opacity-50 text-white p-1 rounded hover:bg-opacity-70"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </>
          )}
        </div>
      </div>
      
      {/* Metadata */}
      <div className="p-3">
        {editingImage === image.id ? (
          <div className="space-y-2">
            <input
              type="text"
              placeholder="Image label"
              value={editForm.label}
              onChange={(e) => setEditForm(prev => ({ ...prev, label: e.target.value }))}
              className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded text-sm"
              maxLength={255}
            />
            <textarea
              placeholder="Image description"
              value={editForm.description}
              onChange={(e) => setEditForm(prev => ({ ...prev, description: e.target.value }))}
              className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded text-sm"
              rows={2}
            />
            <div className="flex space-x-2">
              <button
                onClick={() => handleSaveEdit(image.id)}
                className="flex-1 bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700"
              >
                <Save className="h-4 w-4 inline mr-1" />
                Save
              </button>
              <button
                onClick={() => setEditingImage(null)}
                className="flex-1 bg-gray-600 text-white px-3 py-1 rounded text-sm hover:bg-gray-700"
              >
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <div className="space-y-2">
            {image.label && (
              <div className="flex items-center space-x-1">
                <Tag className="h-3 w-3 text-gray-400" />
                <span className="text-sm font-medium text-navy-blue dark:text-white">
                  {image.label}
                </span>
              </div>
            )}
            
            {image.description && (
              <div className="flex items-start space-x-1">
                <FileText className="h-3 w-3 text-gray-400 mt-0.5" />
                <span className="text-xs text-gray-600 dark:text-gray-300">
                  {image.description}
                </span>
              </div>
            )}
            
            <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
              <div className="flex items-center space-x-1">
                <HardDrive className="h-3 w-3" />
                <span>{formatFileSize(image.total_storage_bytes)}</span>
              </div>
              
              <div className="flex items-center space-x-1">
                <Calendar className="h-3 w-3" />
                <span>{formatDate(image.uploaded_at)}</span>
              </div>
            </div>
            
            {/* Download Options */}
            <div className="flex space-x-1 pt-1">
              <button
                onClick={() => handleDownload(image, false)}
                className="flex-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 px-2 py-1 rounded text-xs hover:bg-gray-200 dark:hover:bg-gray-600"
              >
                <Download className="h-3 w-3 inline mr-1" />
                Web
              </button>
              
              {image.is_heic_format && (
                <button
                  onClick={() => handleDownload(image, true)}
                  className="flex-1 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 px-2 py-1 rounded text-xs hover:bg-blue-200 dark:hover:bg-blue-800"
                >
                  <Download className="h-3 w-3 inline mr-1" />
                  Original
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );

  const renderComparison = () => (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Before Images */}
      <div>
        <h3 className="text-lg font-semibold text-navy-blue dark:text-white mb-4 flex items-center">
          <ArrowLeft className="h-5 w-5 mr-2" />
          Before Photos ({beforeImages.length})
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {beforeImages.map(renderImageCard)}
        </div>
      </div>
      
      {/* After Images */}
      <div>
        <h3 className="text-lg font-semibold text-navy-blue dark:text-white mb-4 flex items-center">
          <ArrowRight className="h-5 w-5 mr-2" />
          After Photos ({afterImages.length})
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {afterImages.map(renderImageCard)}
        </div>
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="flex justify-center items-center h-32">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
        <p className="text-red-700 dark:text-red-300">{error}</p>
      </div>
    );
  }

  const totalImages = showComparison ? beforeImages.length + afterImages.length : images.length;

  if (totalImages === 0) {
    return (
      <div className="text-center py-8">
        <ImageIcon className="h-12 w-12 mx-auto text-gray-400 mb-4" />
        <p className="text-gray-500 dark:text-gray-400">
          No {imageType ? `${imageType} ` : ''}images uploaded yet
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-navy-blue dark:text-white">
          Assignment Images ({totalImages})
        </h2>
        
        {showComparison && (
          <div className="flex space-x-2">
            <button
              onClick={() => setViewMode('grid')}
              className={`px-3 py-1 rounded text-sm ${
                viewMode === 'grid' 
                  ? 'bg-navy-blue text-white' 
                  : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
              }`}
            >
              <Grid className="h-4 w-4 inline mr-1" />
              Grid
            </button>
            <button
              onClick={() => setViewMode('comparison')}
              className={`px-3 py-1 rounded text-sm ${
                viewMode === 'comparison' 
                  ? 'bg-navy-blue text-white' 
                  : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
              }`}
            >
              <Maximize2 className="h-4 w-4 inline mr-1" />
              Compare
            </button>
          </div>
        )}
      </div>

      {/* Images */}
      {showComparison && viewMode === 'comparison' ? (
        renderComparison()
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {(showComparison ? [...beforeImages, ...afterImages] : images).map(renderImageCard)}
        </div>
      )}

      {/* Lightbox */}
      {lightboxOpen && selectedImage && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
          <div className="relative max-w-4xl max-h-full">
            <button
              onClick={() => setLightboxOpen(false)}
              className="absolute top-4 right-4 text-white hover:text-gray-300 z-10"
            >
              <X className="h-6 w-6" />
            </button>
            
            <img
              src={getImageUrl(selectedImage)}
              alt={selectedImage.label || selectedImage.original_file_name}
              className="max-w-full max-h-full object-contain"
            />
            
            {/* Image Info */}
            <div className="absolute bottom-4 left-4 bg-black bg-opacity-75 text-white p-3 rounded">
              <p className="font-medium">{selectedImage.label || selectedImage.original_file_name}</p>
              {selectedImage.description && (
                <p className="text-sm text-gray-300 mt-1">{selectedImage.description}</p>
              )}
              <p className="text-xs text-gray-400 mt-1">
                {formatFileSize(selectedImage.total_storage_bytes)} • {formatDate(selectedImage.uploaded_at)}
                {selectedImage.is_heic_format && ' • HEIC'}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AssignmentImageGallery; 