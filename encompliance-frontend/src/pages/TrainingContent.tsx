import React, { useState, useEffect } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { 
  ArrowLeft, 
  BookOpen, 
  Video, 
  FileText, 
  ExternalLink, 
  Clock, 
  CheckCircle, 
  Play,
  Download,
  AlertTriangle,
  BarChart3
} from 'lucide-react';
import { 
  trainingProgramService, 
  trainingMaterialService, 
  trainingAssignmentService,
  TrainingProgram, 
  TrainingMaterial, 
  TrainingAssignment 
} from '../services/trainingService';

const TrainingContentPage: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [searchParams] = useSearchParams();
  const assignmentId = searchParams.get('assignment_id');
  
  const [loading, setLoading] = useState(true);
  const [program, setProgram] = useState<TrainingProgram | null>(null);
  const [materials, setMaterials] = useState<TrainingMaterial[]>([]);
  const [assignment, setAssignment] = useState<TrainingAssignment | null>(null);
  const [error, setError] = useState<string>('');
  const [currentMaterialIndex, setCurrentMaterialIndex] = useState(0);

  useEffect(() => {
    if (id) {
      loadTrainingContent(parseInt(id));
    }
  }, [id, assignmentId]);

  const loadTrainingContent = async (programId: number) => {
    try {
      setLoading(true);
      
      // Load program and materials in parallel
      const [programData, materialsData] = await Promise.all([
        trainingProgramService.getById(programId),
        trainingMaterialService.getByProgram(programId)
      ]);
      
      setProgram(programData);
      setMaterials(materialsData.sort((a, b) => a.sort_order - b.sort_order));
      
      // Load assignment if assignment_id is provided
      if (assignmentId) {
        try {
          const assignmentData = await trainingAssignmentService.getById(parseInt(assignmentId));
          setAssignment(assignmentData);
        } catch (assignmentError) {
          console.warn('Could not load assignment:', assignmentError);
        }
      }
      
      setError('');
    } catch (error) {
      console.error('Error loading training content:', error);
      setError('Failed to load training content. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleMaterialClick = (material: TrainingMaterial, index: number) => {
    setCurrentMaterialIndex(index);
    
    if (material.external_url) {
      // Open external URL in new tab
      window.open(material.external_url, '_blank');
    } else if (material.file_path) {
      // Handle file download or viewing
      const fileUrl = `/api/v1/training/materials/${material.id}/file`;
      window.open(fileUrl, '_blank');
    }
  };

  const updateProgress = async () => {
    if (!assignment) return;
    
    try {
      const completedMaterials = currentMaterialIndex + 1;
      const totalMaterials = materials.length;
      const progressPercentage = Math.round((completedMaterials / totalMaterials) * 100);
      
      await trainingAssignmentService.updateProgress(assignment.id, progressPercentage);
      
      // Update local assignment state
      setAssignment({
        ...assignment,
        progress_percentage: progressPercentage
      });
    } catch (error) {
      console.error('Error updating progress:', error);
    }
  };

  const handleNextMaterial = () => {
    if (currentMaterialIndex < materials.length - 1) {
      setCurrentMaterialIndex(currentMaterialIndex + 1);
      updateProgress();
    }
  };

  const handlePreviousMaterial = () => {
    if (currentMaterialIndex > 0) {
      setCurrentMaterialIndex(currentMaterialIndex - 1);
    }
  };

  const getMaterialIcon = (materialType: string) => {
    switch (materialType) {
      case 'video':
        return Video;
      case 'document':
        return FileText;
      case 'link':
        return ExternalLink;
      case 'quiz':
      case 'assessment':
        return CheckCircle;
      case 'presentation':
        return Play;
      default:
        return BookOpen;
    }
  };

  const formatDuration = (minutes?: number) => {
    if (!minutes) return 'Duration not specified';
    
    if (minutes < 60) {
      return `${minutes} minutes`;
    } else {
      const hours = Math.floor(minutes / 60);
      const remainingMinutes = minutes % 60;
      return `${hours}h ${remainingMinutes}m`;
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-6">
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <p className="ml-4 text-gray-600 dark:text-gray-400">Loading training content...</p>
        </div>
      </div>
    );
  }

  if (error || !program) {
    return (
      <div className="container mx-auto px-4 py-6">
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6 text-center">
          <AlertTriangle className="h-12 w-12 text-red-600 dark:text-red-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-red-900 dark:text-red-100 mb-2">Error Loading Content</h3>
          <p className="text-red-700 dark:text-red-300 mb-4">{error || 'Training program not found'}</p>
          <button
            onClick={() => navigate('/training/programs')}
            className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors"
          >
            Back to Training Programs
          </button>
        </div>
      </div>
    );
  }

  const currentMaterial = materials[currentMaterialIndex];

  return (
    <div className="container mx-auto px-4 py-6">
      {/* Header */}
      <div className="mb-6">
        <button
          onClick={() => assignment ? navigate(`/training/assignments/${assignment.id}`) : navigate('/training/programs')}
          className="flex items-center text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 mb-4"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          {assignment ? 'Back to Assignment' : 'Back to Programs'}
        </button>
        
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-800 dark:text-white mb-2">
              {program.title}
            </h1>
            <p className="text-gray-600 dark:text-gray-300">
              {program.description || 'Training content and materials'}
            </p>
          </div>
          
          {assignment && (
            <div className="text-right">
              <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Progress</div>
              <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                {assignment.progress_percentage}%
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Progress Bar */}
      {assignment && (
        <div className="mb-6">
          <div className="flex items-center justify-between text-sm mb-2">
            <span className="text-gray-600 dark:text-gray-400">Training Progress</span>
            <span className="font-medium">{assignment.progress_percentage}%</span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${assignment.progress_percentage}%` }}
            ></div>
          </div>
        </div>
      )}

      {/* Training Materials */}
      {materials.length === 0 ? (
        <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-12 text-center">
          <BookOpen className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">No Training Materials</h3>
          <p className="text-gray-600 dark:text-gray-400">This training program doesn't have any materials yet.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Materials List */}
          <div className="lg:col-span-1">
            <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md">
              <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Training Materials ({materials.length})
                </h3>
              </div>
              <div className="divide-y divide-gray-200 dark:divide-gray-700">
                {materials.map((material, index) => {
                  const Icon = getMaterialIcon(material.material_type);
                  const isActive = index === currentMaterialIndex;
                  const isCompleted = assignment && index < (assignment.progress_percentage / 100) * materials.length;
                  
                  return (
                    <div
                      key={material.id}
                      className={`p-4 cursor-pointer transition-colors ${
                        isActive 
                          ? 'bg-blue-50 dark:bg-blue-900/20 border-r-4 border-blue-600' 
                          : 'hover:bg-gray-50 dark:hover:bg-gray-800'
                      }`}
                      onClick={() => handleMaterialClick(material, index)}
                    >
                      <div className="flex items-center space-x-3">
                        <div className={`p-2 rounded-lg ${
                          isCompleted 
                            ? 'bg-green-100 dark:bg-green-900/20' 
                            : isActive 
                              ? 'bg-blue-100 dark:bg-blue-900/20' 
                              : 'bg-gray-100 dark:bg-gray-700'
                        }`}>
                          {isCompleted ? (
                            <CheckCircle className="h-4 w-4 text-green-600 dark:text-green-400" />
                          ) : (
                            <Icon className={`h-4 w-4 ${
                              isActive 
                                ? 'text-blue-600 dark:text-blue-400' 
                                : 'text-gray-600 dark:text-gray-400'
                            }`} />
                          )}
                        </div>
                        
                        <div className="flex-1 min-w-0">
                          <h4 className={`text-sm font-medium truncate ${
                            isActive 
                              ? 'text-blue-900 dark:text-blue-100' 
                              : 'text-gray-900 dark:text-white'
                          }`}>
                            {material.title}
                          </h4>
                          <div className="flex items-center space-x-2 text-xs text-gray-500 dark:text-gray-400">
                            <span className="capitalize">{material.material_type}</span>
                            {material.duration_minutes && (
                              <>
                                <span>•</span>
                                <span>{formatDuration(material.duration_minutes)}</span>
                              </>
                            )}
                            {material.is_required && (
                              <>
                                <span>•</span>
                                <span className="text-red-600 dark:text-red-400">Required</span>
                              </>
                            )}
                          </div>
                        </div>
                        
                        {material.external_url && (
                          <ExternalLink className="h-4 w-4 text-gray-400" />
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Current Material Content */}
          <div className="lg:col-span-2">
            {currentMaterial && (
              <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md">
                <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                        {currentMaterial.title}
                      </h3>
                      <p className="text-sm text-gray-600 dark:text-gray-400 capitalize">
                        {currentMaterial.material_type}
                        {currentMaterial.duration_minutes && (
                          <span> • {formatDuration(currentMaterial.duration_minutes)}</span>
                        )}
                      </p>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={handlePreviousMaterial}
                        disabled={currentMaterialIndex === 0}
                        className="px-3 py-1 text-sm bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-200 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                      >
                        Previous
                      </button>
                      <button
                        onClick={handleNextMaterial}
                        disabled={currentMaterialIndex === materials.length - 1}
                        className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                      >
                        Next
                      </button>
                    </div>
                  </div>
                </div>
                
                <div className="p-6">
                  {currentMaterial.description && (
                    <p className="text-gray-600 dark:text-gray-400 mb-4">
                      {currentMaterial.description}
                    </p>
                  )}
                  
                  {/* Material Content */}
                  <div className="space-y-4">
                    {currentMaterial.external_url && (
                      <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                        <div className="flex items-center justify-between">
                          <div>
                            <h4 className="font-medium text-gray-900 dark:text-white mb-1">
                              External Training Content
                            </h4>
                            <p className="text-sm text-gray-600 dark:text-gray-400">
                              Click to open the training content in a new tab
                            </p>
                          </div>
                          <button
                            onClick={() => window.open(currentMaterial.external_url, '_blank')}
                            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center transition-colors"
                          >
                            <ExternalLink className="h-4 w-4 mr-2" />
                            Open Training
                          </button>
                        </div>
                      </div>
                    )}
                    
                    {currentMaterial.file_path && (
                      <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                        <div className="flex items-center justify-between">
                          <div>
                            <h4 className="font-medium text-gray-900 dark:text-white mb-1">
                              Training File
                            </h4>
                            <p className="text-sm text-gray-600 dark:text-gray-400">
                              {currentMaterial.file_name || 'Training document'}
                              {currentMaterial.file_size && (
                                <span> • {Math.round(currentMaterial.file_size / 1024)} KB</span>
                              )}
                            </p>
                          </div>
                          <button
                            onClick={() => window.open(`/api/v1/training/materials/${currentMaterial.id}/file`, '_blank')}
                            className="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 flex items-center transition-colors"
                          >
                            <Download className="h-4 w-4 mr-2" />
                            View/Download
                          </button>
                        </div>
                      </div>
                    )}
                    
                    {currentMaterial.embed_code && (
                      <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                        <h4 className="font-medium text-gray-900 dark:text-white mb-3">
                          Interactive Content
                        </h4>
                        <div 
                          className="w-full"
                          dangerouslySetInnerHTML={{ __html: currentMaterial.embed_code }}
                        />
                      </div>
                    )}
                    
                    {!currentMaterial.external_url && !currentMaterial.file_path && !currentMaterial.embed_code && (
                      <div className="text-center py-8">
                        <BookOpen className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                        <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                          Content Not Available
                        </h4>
                        <p className="text-gray-600 dark:text-gray-400">
                          This training material doesn't have content configured yet.
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default TrainingContentPage; 