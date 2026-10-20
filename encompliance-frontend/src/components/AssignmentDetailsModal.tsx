import React, { useState, useEffect } from 'react';
import { X, Camera, Clock, User, MapPin, AlertTriangle, CheckCircle, PlayCircle, Calendar } from 'lucide-react';
import { TaskAssignment } from '../services/operationalTaskService';
import { operationalTaskService } from '../services/operationalTaskService';
import { taskReferenceImageService, TaskReferenceImage } from '../services/taskReferenceImageService';
import AssignmentImageUploader from './AssignmentImageUploader';

interface AssignmentDetailsModalProps {
  isOpen: boolean;
  onClose: () => void;
  assignment: TaskAssignment;
  onUpdate: () => void;
}

const AssignmentDetailsModal: React.FC<AssignmentDetailsModalProps> = ({
  isOpen,
  onClose,
  assignment: initialAssignment,
  onUpdate
}) => {
  const [assignment, setAssignment] = useState<TaskAssignment>(initialAssignment);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'details' | 'photos'>('details');
  const [referenceImages, setReferenceImages] = useState<TaskReferenceImage[]>([]);
  const [selectedImage, setSelectedImage] = useState<TaskReferenceImage | null>(null);

  useEffect(() => {
    setAssignment(initialAssignment);
  }, [initialAssignment]);

  useEffect(() => {
    const loadReference = async () => {
      if (!initialAssignment?.operational_task?.id) return;
      try {
        const imgs = await taskReferenceImageService.getTaskReferenceImages(initialAssignment.operational_task.id);
        setReferenceImages(imgs);
      } catch (e) {
        console.error('Failed to load reference images', e);
      }
    };
    if (isOpen) loadReference();
  }, [isOpen, initialAssignment]);

  const handleStartAssignment = async () => {
    setIsLoading(true);
    setError(null);
    try {
      await operationalTaskService.updateAssignment(assignment.id, {
        status: 'in_progress',
        started_date: new Date().toISOString()
      });
      const updatedAssignment = { ...assignment, status: 'in_progress' as const, started_date: new Date().toISOString() };
      setAssignment(updatedAssignment);
      onUpdate();
    } catch (err) {
      setError('Failed to start assignment');
      console.error('Error starting assignment:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    const colors = {
      assigned: 'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300',
      in_progress: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300',
      completed: 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300',
      overdue: 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300',
      cancelled: 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300'
    };
    
    return (
      <span className={`px-3 py-1 rounded-full text-sm font-medium ${colors[status as keyof typeof colors] || colors.assigned}`}>
        {status.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
      </span>
    );
  };

  const getPriorityBadge = (priority: string) => {
    const colors = {
      low: 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300',
      medium: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300', 
      high: 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300'
    };
    
    return (
      <span className={`px-3 py-1 rounded-full text-sm font-medium ${colors[priority as keyof typeof colors] || colors.medium}`}>
        {priority.charAt(0).toUpperCase() + priority.slice(1)} Priority
      </span>
    );
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' at ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const formatDueDate = (dueDate: string) => {
    const date = new Date(dueDate);
    const now = new Date();
    const diffTime = date.getTime() - now.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays < 0) {
      return `${Math.abs(diffDays)} days overdue`;
    } else if (diffDays === 0) {
      return 'Due today';
    } else if (diffDays === 1) {
      return 'Due tomorrow';
    } else {
      return `Due in ${diffDays} days`;
    }
  };

  const canUploadBeforePhotos = () => {
    return assignment.status === 'assigned' || assignment.status === 'in_progress';
  };

  const canUploadAfterPhotos = () => {
    return assignment.status === 'in_progress';
  };

  const renderImageGrid = (imgs: TaskReferenceImage[]) => (
    <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
      {imgs.map(img => (
        <div key={img.id} className="cursor-pointer" onClick={() => setSelectedImage(img)}>
          <img
            src={taskReferenceImageService.getImageUrl(initialAssignment!.operational_task!.id, img.id)}
            alt={img.label}
            className="w-full h-40 object-cover rounded-lg"
          />
          <p className="text-sm text-center mt-2 text-gray-700 dark:text-gray-300">{img.label}</p>
        </div>
      ))}
    </div>
  );

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-dark-surface rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white">
              Assignment Details
            </h2>
            {getStatusBadge(assignment.status)}
            {assignment.is_overdue && (
              <div className="flex items-center space-x-1 text-red-600 dark:text-red-400">
                <AlertTriangle className="h-4 w-4" />
                <span className="text-sm font-medium">Overdue</span>
              </div>
            )}
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="px-6 border-b border-gray-200 dark:border-gray-700">
          <nav className="-mb-px flex space-x-8">
            {[
              { id: 'details', label: 'Task Details', icon: CheckCircle },
              { id: 'photos', label: 'Photo Documentation', icon: Camera }
            ].map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setActiveTab(id as any)}
                className={`py-3 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${
                  activeTab === id
                    ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                    : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
                }`}
              >
                <Icon className="h-4 w-4" />
                <span>{label}</span>
              </button>
            ))}
          </nav>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-180px)]">
          {error && (
            <div className="mb-4 p-4 bg-red-100 dark:bg-red-900/30 border border-red-300 dark:border-red-700 rounded-lg">
              <p className="text-red-800 dark:text-red-300">{error}</p>
            </div>
          )}

          {activeTab === 'details' && (
            <div className="space-y-6">
              {/* Task Information */}
              <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                  {assignment.operational_task?.title || `Task #${assignment.operational_task_id}`}
                </h3>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-600 dark:text-gray-400">Status</label>
                      {getStatusBadge(assignment.status)}
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-600 dark:text-gray-400">Priority</label>
                      {getPriorityBadge(assignment.priority)}
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-600 dark:text-gray-400">Assigned To</label>
                      <div className="flex items-center space-x-2 mt-1">
                        <User className="h-4 w-4 text-gray-500" />
                        <span className="text-gray-900 dark:text-white">
                          {assignment.staff_member?.full_name || 'Unassigned'}
                        </span>
                      </div>
                    </div>

                    {assignment.operational_task?.location && (
                      <div>
                        <label className="block text-sm font-medium text-gray-600 dark:text-gray-400">Location</label>
                        <div className="flex items-center space-x-2 mt-1">
                          <MapPin className="h-4 w-4 text-gray-500" />
                          <span className="text-gray-900 dark:text-white">
                            {assignment.operational_task.location}
                          </span>
                        </div>
                      </div>
                    )}
                  </div>

                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-600 dark:text-gray-400">Due Date</label>
                      <div className="flex items-center space-x-2 mt-1">
                        <Calendar className="h-4 w-4 text-gray-500" />
                        <span className={`${assignment.is_overdue ? 'text-red-600 dark:text-red-400' : 'text-gray-900 dark:text-white'}`}>
                          {formatDate(assignment.due_date)} ({formatDueDate(assignment.due_date)})
                        </span>
                      </div>
                    </div>

                    {assignment.operational_task?.estimated_duration_minutes && (
                      <div>
                        <label className="block text-sm font-medium text-gray-600 dark:text-gray-400">Estimated Duration</label>
                        <div className="flex items-center space-x-2 mt-1">
                          <Clock className="h-4 w-4 text-gray-500" />
                          <span className="text-gray-900 dark:text-white">
                            {assignment.operational_task.estimated_duration_minutes} minutes
                          </span>
                        </div>
                      </div>
                    )}

                    {assignment.started_date && (
                      <div>
                        <label className="block text-sm font-medium text-gray-600 dark:text-gray-400">Started</label>
                        <span className="text-gray-900 dark:text-white">
                          {formatDate(assignment.started_date)}
                        </span>
                      </div>
                    )}

                    {assignment.completed_date && (
                      <div>
                        <label className="block text-sm font-medium text-gray-600 dark:text-gray-400">Completed</label>
                        <span className="text-gray-900 dark:text-white">
                          {formatDate(assignment.completed_date)}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Task Description */}
              {assignment.operational_task?.description && (
                <div>
                  <h4 className="text-md font-semibold text-gray-900 dark:text-white mb-2">Description</h4>
                  <p className="text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
                    {assignment.operational_task.description}
                  </p>
                </div>
              )}

              {/* Special Instructions */}
              {assignment.operational_task?.special_instructions && (
                <div>
                  <h4 className="text-md font-semibold text-gray-900 dark:text-white mb-2">Special Instructions</h4>
                  <p className="text-gray-600 dark:text-gray-400 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-700 rounded-lg p-4">
                    {assignment.operational_task.special_instructions}
                  </p>
                </div>
              )}

              {/* Photo Requirements */}
              {(assignment.operational_task?.requires_before_photos || assignment.operational_task?.requires_after_photos) && (
                <div>
                  <h4 className="text-md font-semibold text-gray-900 dark:text-white mb-2">Photo Requirements</h4>
                  <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700 rounded-lg p-4">
                    <div className="space-y-2">
                      {assignment.operational_task?.requires_before_photos && (
                        <div className="flex items-center space-x-2">
                          <Camera className="h-4 w-4 text-blue-600" />
                          <span className="text-blue-800 dark:text-blue-300">Before photos required</span>
                        </div>
                      )}
                      {assignment.operational_task?.requires_after_photos && (
                        <div className="flex items-center space-x-2">
                          <Camera className="h-4 w-4 text-blue-600" />
                          <span className="text-blue-800 dark:text-blue-300">After photos required</span>
                        </div>
                      )}
                    </div>
                    {assignment.operational_task?.photo_instructions && (
                      <div className="mt-3 pt-3 border-t border-blue-200 dark:border-blue-700">
                        <p className="text-blue-800 dark:text-blue-300 text-sm">
                          <strong>Instructions:</strong> {assignment.operational_task.photo_instructions}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Assignment Notes */}
              {assignment.assignment_notes && (
                <div>
                  <h4 className="text-md font-semibold text-gray-900 dark:text-white mb-2">Assignment Notes</h4>
                  <p className="text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
                    {assignment.assignment_notes}
                  </p>
                </div>
              )}

              {/* Progress and Quality */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {assignment.progress_percentage > 0 && (
                  <div>
                    <h4 className="text-md font-semibold text-gray-900 dark:text-white mb-2">Progress</h4>
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600 dark:text-gray-400">Completion</span>
                        <span className="text-gray-900 dark:text-white">{assignment.progress_percentage}%</span>
                      </div>
                      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                        <div 
                          className="bg-blue-600 h-2 rounded-full transition-all duration-300" 
                          style={{ width: `${assignment.progress_percentage}%` }}
                        ></div>
                      </div>
                    </div>
                  </div>
                )}

                {assignment.time_spent_minutes > 0 && (
                  <div>
                    <h4 className="text-md font-semibold text-gray-900 dark:text-white mb-2">Time Spent</h4>
                    <div className="flex items-center space-x-2">
                      <Clock className="h-4 w-4 text-gray-500" />
                      <span className="text-gray-900 dark:text-white">
                        {Math.round(assignment.time_spent_minutes / 60)} hours {assignment.time_spent_minutes % 60} minutes
                      </span>
                    </div>
                  </div>
                )}
              </div>

              {/* Action Buttons */}
              <div className="flex space-x-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                {assignment.status === 'assigned' && (
                  <button
                    onClick={handleStartAssignment}
                    disabled={isLoading}
                    className="flex items-center space-x-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white px-6 py-2 rounded-lg font-medium transition-colors"
                  >
                    <PlayCircle className="h-4 w-4" />
                    <span>{isLoading ? 'Starting...' : 'Start Assignment'}</span>
                  </button>
                )}
              </div>
            </div>
          )}

          {activeTab === 'photos' && (
            <div className="space-y-6">
              {/* Before Photos Section */}
              {assignment.operational_task?.requires_before_photos && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Before Photos</h3>
                  {canUploadBeforePhotos() ? (
                    <AssignmentImageUploader
                      assignmentId={assignment.id}
                      requiresBeforePhotos={assignment.operational_task?.requires_before_photos || false}
                      requiresAfterPhotos={false}
                      photoInstructions={assignment.operational_task?.photo_instructions}
                      onImagesChange={() => {}}
                      onUploadComplete={onUpdate}
                    />
                  ) : (
                    <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-6 text-center">
                      <Camera className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                      <p className="text-gray-600 dark:text-gray-400">
                        {assignment.status === 'completed' 
                          ? 'Assignment is completed. Before photos can no longer be uploaded.'
                          : 'Before photos will be available once the assignment is created.'
                        }
                      </p>
                    </div>
                  )}
                </div>
              )}

              {/* After Photos Section */}
              {assignment.operational_task?.requires_after_photos && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">After Photos</h3>
                  {canUploadAfterPhotos() ? (
                    <AssignmentImageUploader
                      assignmentId={assignment.id}
                      requiresBeforePhotos={false}
                      requiresAfterPhotos={assignment.operational_task?.requires_after_photos || false}
                      photoInstructions={assignment.operational_task?.photo_instructions}
                      onImagesChange={() => {}}
                      onUploadComplete={onUpdate}
                    />
                  ) : (
                    <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-6 text-center">
                      <Camera className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                      <p className="text-gray-600 dark:text-gray-400">
                        {assignment.status === 'assigned'
                          ? 'After photos will be available once you start working on the assignment.'
                          : assignment.status === 'completed'
                          ? 'Assignment is completed. After photos can no longer be uploaded.'
                          : 'After photos are not available for this assignment status.'
                        }
                      </p>
                    </div>
                  )}
                </div>
              )}

              {/* No photos required message */}
              {referenceImages.length > 0 && (
                <div className="space-y-4">
                  <h4 className="text-md font-semibold text-gray-900 dark:text-white">Reference Photos</h4>
                  {renderImageGrid(referenceImages)}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700 flex justify-end">
          <button
            onClick={onClose}
            className="bg-gray-600 hover:bg-gray-700 text-white px-6 py-2 rounded-lg font-medium transition-colors"
          >
            Close
          </button>
        </div>
      </div>

      {selectedImage && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50"
          onClick={() => setSelectedImage(null)}
        >
          <div className="relative max-w-3xl max-h-[80vh]">
            <img 
              src={taskReferenceImageService.getImageUrl(initialAssignment!.operational_task!.id, selectedImage.id)}
              alt={selectedImage.label}
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

export default AssignmentDetailsModal; 