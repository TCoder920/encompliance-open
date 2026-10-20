/*
  Description: Task Reference Image Service for API communication
  Purpose: Handles all API calls related to task reference image management
*/

import apiClient from './api';

export interface TaskReferenceImage {
  id: number;
  operational_task_id: number;
  image_type: string;
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
  image_metadata?: any;
  created_at: string;
  updated_at: string;
  total_storage_bytes: number;
  requires_conversion: boolean;
  is_heic_format: boolean;
  conversion_completed: boolean;
}

export interface TaskReferenceImageUploadResponse {
  message: string;
  uploaded_count: number;
  images: TaskReferenceImage[];
}

class TaskReferenceImageService {
  private baseUrl = '/operational-tasks';

  async uploadImages(
    taskId: number,
    files: File[],
    labels?: string[],
    descriptions?: string[]
  ): Promise<TaskReferenceImageUploadResponse> {
    const formData = new FormData();
    
    files.forEach(file => {
      formData.append('files', file);
    });
    
    if (labels) {
      labels.forEach(label => {
        formData.append('labels', label);
      });
    }
    
    if (descriptions) {
      descriptions.forEach(description => {
        formData.append('descriptions', description);
      });
    }

    const response = await apiClient.post(
      `${this.baseUrl}/${taskId}/reference-images/upload`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  }

  async getTaskReferenceImages(taskId: number): Promise<TaskReferenceImage[]> {
    const response = await apiClient.get(`${this.baseUrl}/${taskId}/reference-images`);
    return response.data;
  }

  async getImageFile(taskId: number, imageId: number, original: boolean = false): Promise<Blob> {
    const response = await apiClient.get(
      `${this.baseUrl}/${taskId}/reference-images/${imageId}`,
      {
        params: { original },
        responseType: 'blob',
      }
    );
    return response.data;
  }

  getImageUrl(taskId: number, imageId: number, original: boolean = false): string {
    const token = localStorage.getItem('token');
    const apiBase = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '');
    let url = `${apiBase}/api/v1${this.baseUrl}/${taskId}/reference-images/${imageId}`;
    const queryParams: string[] = [];
    if (original) {
      queryParams.push('original=true');
    }
    if (token) {
      queryParams.push(`token=${token}`);
    }
    if (queryParams.length > 0) {
      url += `?${queryParams.join('&')}`;
    }
    return url;
  }

  async updateImageMetadata(
    taskId: number,
    imageId: number,
    updates: {
      label?: string;
      description?: string;
      display_order?: number;
    }
  ): Promise<TaskReferenceImage> {
    const response = await apiClient.put(
      `${this.baseUrl}/${taskId}/reference-images/${imageId}`,
      updates
    );
    return response.data;
  }

  async deleteImage(taskId: number, imageId: number): Promise<void> {
    await apiClient.delete(`${this.baseUrl}/${taskId}/reference-images/${imageId}`);
  }

  async reorderImages(
    taskId: number,
    imageOrders: { id: number; display_order: number }[]
  ): Promise<void> {
    await apiClient.post(`${this.baseUrl}/${taskId}/reference-images/reorder`, {
      image_orders: imageOrders,
    });
  }
}

export const taskReferenceImageService = new TaskReferenceImageService(); 