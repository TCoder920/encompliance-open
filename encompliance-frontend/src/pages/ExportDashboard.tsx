/**
 * Description: Data Export Dashboard page for the EnCompliance application.
 * Purpose: Provides interface for Pro/Enterprise users to export their data with quota management and fee calculation.
 * Educational Note: Implements freemium access control with subscription tier validation.
 * Reference: React component patterns - https://react.dev/learn/thinking-in-react
 */

import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { getTierFromSubscriptionStatus } from '../utils/tiers';
import { canUseFeatureWithRole } from '../utils/accessControl';
import { themeClasses } from '../utils/themeUtils';
import { 
  Download, 
  Clock, 
  AlertCircle, 
  CheckCircle, 
  FileText,
  Database,
  Calendar,
  MessageSquare,
  Shield,
  User,
  Activity,
  Loader2,
  RefreshCw,
  DollarSign,
  Info,
  Building,
  GraduationCap,
  ClipboardList,
  Globe,
  Smartphone,
  StickyNote,
  BarChart3
} from 'lucide-react';

interface QuotaStatus {
  quarter: string;
  exports_used: number;
  exports_limit: number | null;
  available: boolean;
  total_data_size: number;
  last_export_date: string | null;
  next_available_date: string | null;
  unlimited?: boolean;
  message?: string;
}

interface SubscriptionStatus {
  tier: string;
  is_active: boolean;
  end_date: string | null;
}

interface ExportEstimate {
  estimated_size: number;
  estimated_size_mb: number;
  requires_fee: boolean;
  fee_amount: number | null;
}

interface ExportRequest {
  id: string;
  status: string;
  format: string;
  data_types: string[];
  created_at: string;
  progress_percentage: number;
  download_expires_at: string | null;
  error_message: string | null;
}

const ExportDashboard: React.FC = () => {
  const { user, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [quotaStatus, setQuotaStatus] = useState<QuotaStatus | null>(null);
  const [subscriptionStatus, setSubscriptionStatus] = useState<SubscriptionStatus | null>(null);
  const [selectedDataTypes, setSelectedDataTypes] = useState<string[]>(['user_profile']);
  const [selectedFormat, setSelectedFormat] = useState('json');
  const [estimate, setEstimate] = useState<ExportEstimate | null>(null);
  const [estimating, setEstimating] = useState(false);
  const [exportHistory, setExportHistory] = useState<ExportRequest[]>([]);
  const [currentExport, setCurrentExport] = useState<ExportRequest | null>(null);
  const [isExporting, setIsExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const userTier = getTierFromSubscriptionStatus(user?.subscription_status);
  const isUnlimitedExports = quotaStatus?.unlimited || quotaStatus?.exports_limit === null;

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }

    // Load data for authenticated users
    fetchQuotaStatus();
    fetchExportHistory();
  }, [isAuthenticated, userTier, navigate]);

  const fetchQuotaStatus = async () => {
    try {
      const response = await fetch('/api/v1/export/quota-status', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setQuotaStatus(data.quota);
        setSubscriptionStatus(data.subscription);
      } else {
        setError('Failed to fetch quota status');
      }
    } catch (error) {
      console.error('Error fetching quota status:', error);
      setError('Failed to connect to server');
    } finally {
      setLoading(false);
    }
  };

  const fetchExportHistory = async () => {
    try {
      const response = await fetch('/api/v1/export/history', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setExportHistory(data.exports || []);
      }
    } catch (error) {
      console.error('Error fetching export history:', error);
    }
  };

  const estimateExportSize = async () => {
    if (selectedDataTypes.length === 0) return;

    setEstimating(true);
    setError(null);
    try {
      const response = await fetch('/api/v1/export/estimate-size', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          data_types: selectedDataTypes
        })
      });

      if (response.ok) {
        const data = await response.json();
        setEstimate(data);
      } else {
        const errorData = await response.json();
        setError(errorData.detail?.message || 'Failed to estimate export size');
      }
    } catch (error) {
      console.error('Error estimating export size:', error);
      setError('Failed to estimate export size');
    } finally {
      setEstimating(false);
    }
  };

  const initiateExport = async () => {
    if (selectedDataTypes.length === 0) {
      setError('Please select at least one data type to export');
      return;
    }

    setIsExporting(true);
    setError(null);
    try {
      const response = await fetch('/api/v1/export/initiate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          format: selectedFormat,
          data_types: selectedDataTypes
        })
      });

      if (response.ok) {
        const data = await response.json();
        // Start polling for export status
        pollExportStatus(data.export_id);
        // Refresh quota status
        fetchQuotaStatus();
        fetchExportHistory();
      } else {
        let errorMessage = 'Failed to initiate export';
        try {
          const errorData = await response.json();
          const detail = errorData.detail;
          if (typeof detail === 'string') {
            errorMessage = detail;
          } else if (detail?.message) {
            errorMessage = detail.message;
          } else if (detail?.error === 'export_in_progress') {
            errorMessage = 'An export is already running. Please wait for it to finish.';
          }
        } catch (parseError) {
          // ignore JSON parsing errors and use default message
        }
        setError(errorMessage);
        fetchQuotaStatus();
        fetchExportHistory();
      }
    } catch (error) {
      console.error('Error initiating export:', error);
      setError('Failed to initiate export');
    } finally {
      setIsExporting(false);
    }
  };

  const pollExportStatus = async (exportId: string) => {
    const poll = async () => {
      try {
        const response = await fetch(`/api/v1/export/status/${exportId}`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        });

        if (response.ok) {
          const exportData = await response.json();
          setCurrentExport(exportData);

          if (exportData.status === 'completed' || exportData.status === 'failed') {
            fetchExportHistory();
            return;
          }

          // Continue polling if still processing
          if (exportData.status === 'processing' || exportData.status === 'pending') {
            setTimeout(poll, 2000);
          }
        }
      } catch (error) {
        console.error('Error polling export status:', error);
      }
    };

    poll();
  };

  useEffect(() => {
    if (selectedDataTypes.length > 0) {
      estimateExportSize();
    }
  }, [selectedDataTypes]);

  const dataTypeOptions = [
    { 
      key: 'user_profile', 
      label: 'User Profile & Settings', 
      description: 'Account information, preferences, and configuration',
      icon: User,
      estimatedSize: '1 KB'
    },
    { 
      key: 'documents', 
      label: 'Documents & Files', 
      description: 'Uploaded documents, PDFs, and attachments',
      icon: FileText,
      estimatedSize: '~50 MB'
    },
    { 
      key: 'policy_records', 
      label: 'Policy & Compliance Records', 
      description: 'Compliance policies, tracking data, and regulations',
      icon: Shield,
      estimatedSize: '~5 MB'
    },
    { 
      key: 'training_history', 
      label: 'Training & Certifications', 
      description: 'Completed training modules and certification records',
      icon: Database,
      estimatedSize: '~2 MB'
    },
    { 
      key: 'calendar_entries', 
      label: 'Calendar & Events', 
      description: 'Calendar events, reminders, and scheduled activities',
      icon: Calendar,
      estimatedSize: '~1 MB'
    },
    { 
      key: 'chat_logs', 
      label: 'AI Chat History', 
      description: 'Conversation history with AI compliance assistant',
      icon: MessageSquare,
      estimatedSize: '~10 MB'
    },
    { 
      key: 'audit_trail', 
      label: 'Audit Trail & Activity Logs', 
      description: 'System activity logs and audit trail records',
      icon: Activity,
      estimatedSize: '~3 MB'
    },
    { 
      key: 'facility_management', 
      label: 'Facility Management', 
      description: 'Management of facilities and infrastructure',
      icon: Building,
      estimatedSize: '~5 MB'
    },
    { 
      key: 'training_programs', 
      label: 'Training Programs', 
      description: 'Development and implementation of training programs',
      icon: GraduationCap,
      estimatedSize: '~2 MB'
    },
    { 
      key: 'policy_management', 
      label: 'Policy Management', 
      description: 'Management of policies and regulations',
      icon: ClipboardList,
      estimatedSize: '~3 MB'
    },
    { 
      key: 'translation_data', 
      label: 'Translation Data', 
      description: 'Data for language translation and localization',
      icon: Globe,
      estimatedSize: '~10 MB'
    },
    { 
      key: 'calendar_connections', 
      label: 'Calendar Connections', 
      description: 'Connections to external calendar systems',
      icon: Calendar,
      estimatedSize: '~1 MB'
    },
    { 
      key: 'push_subscriptions', 
      label: 'Push Subscriptions', 
      description: 'Subscriptions for push notifications',
      icon: Smartphone,
      estimatedSize: '~500 KB'
    },
    { 
      key: 'export_history', 
      label: 'Export History', 
      description: 'History of data exports',
      icon: ClipboardList,
      estimatedSize: '~5 MB'
    },
    { 
      key: 'notes', 
      label: 'Notes', 
      description: 'Personal notes and reminders',
      icon: StickyNote,
      estimatedSize: '~1 MB'
    }
  ];

  const formatOptions = [
    {
      key: 'csv',
      label: 'CSV (Spreadsheet)',
      description: 'Comma-separated values for Excel/Google Sheets',
      icon: '📊'
    },
    {
      key: 'pdf',
      label: 'PDF (Document)',
      description: 'Formatted document with tables and sections',
      icon: '📄'
    },
    {
      key: 'json',
      label: 'JSON (Structured)',
      description: 'Machine-readable structured data format',
      icon: '🔧'
    }
  ];

  if (loading) {
    return (
      <div className={themeClasses.layout.container}>
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="text-center">
            <Loader2 className={`h-12 w-12 animate-spin ${themeClasses.text.primary} mx-auto mb-4`} />
            <p className={themeClasses.text.secondary}>Loading export dashboard...</p>
          </div>
        </div>
      </div>
    );
  }

  // Preview content for free users
  const previewContent = (
    <div className={themeClasses.layout.container}>
      <div className="space-y-6">
        {/* Header */}
        <div className={themeClasses.layout.header}>
          <h1 className={`text-3xl font-bold ${themeClasses.text.primary} mb-2`}>
            Data Export Dashboard
          </h1>
          <p className={themeClasses.text.secondary}>
            Export your EnCompliance data in multiple formats. Facility administrators now have unlimited exports whenever they need them.
          </p>
        </div>

        {/* Preview Quota Status Card */}
        <div className={themeClasses.components.card}>
          <h2 className={`text-xl font-semibold ${themeClasses.text.primary} mb-4`}>
            Export Quota Status
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                0 / 1
              </div>
              <div className={`text-sm ${themeClasses.text.secondary}`}>
                Exports Used (Q1 2024)
              </div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                Available
              </div>
              <div className={`text-sm ${themeClasses.text.secondary}`}>
                Current Status
              </div>
            </div>
            <div className="text-center">
              <div className={`text-2xl font-bold ${themeClasses.text.secondary}`}>
                Now
              </div>
              <div className={`text-sm ${themeClasses.text.secondary}`}>
                Next Available
              </div>
            </div>
          </div>
        </div>

        {/* Preview Export Configuration */}
        <div className={themeClasses.components.card}>
          <h2 className={`text-xl font-semibold ${themeClasses.text.primary} mb-6`}>
            Configure Export
          </h2>
          
          {/* Format Selection */}
          <div className="mb-6">
            <label className={`block text-sm font-medium ${themeClasses.text.primary} mb-3`}>
              Export Format
            </label>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 border border-blue-500 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                <div className="flex items-center space-x-3 mb-2">
                  <span className="text-2xl">📊</span>
                  <div className={`font-medium ${themeClasses.text.primary}`}>
                    CSV (Spreadsheet)
                  </div>
                </div>
                <div className={`text-sm ${themeClasses.text.secondary}`}>
                  Comma-separated values for Excel/Google Sheets
                </div>
              </div>
              <div className={`p-4 border rounded-lg ${themeClasses.border.primary}`}>
                <div className="flex items-center space-x-3 mb-2">
                  <span className="text-2xl">📄</span>
                  <div className={`font-medium ${themeClasses.text.primary}`}>
                    PDF (Document)
                  </div>
                </div>
                <div className={`text-sm ${themeClasses.text.secondary}`}>
                  Formatted document with tables and sections
                </div>
              </div>
              <div className={`p-4 border rounded-lg ${themeClasses.border.primary}`}>
                <div className="flex items-center space-x-3 mb-2">
                  <span className="text-2xl">🔧</span>
                  <div className={`font-medium ${themeClasses.text.primary}`}>
                    JSON (Structured)
                  </div>
                </div>
                <div className={`text-sm ${themeClasses.text.secondary}`}>
                  Machine-readable structured data format
                </div>
              </div>
            </div>
          </div>

          {/* Data Type Selection Preview */}
          <div className="mb-6">
            <label className={`block text-sm font-medium ${themeClasses.text.primary} mb-3`}>
              Data to Export
            </label>
            <div className="space-y-3">
              <div className="flex items-start space-x-3 p-4 border border-blue-500 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                <input
                  type="checkbox"
                  checked={true}
                  readOnly
                  className="mt-1 h-4 w-4 text-blue-600 border-gray-300 rounded"
                />
                <User className={`h-5 w-5 mt-0.5 ${themeClasses.text.primary}`} />
                <div className="flex-1">
                  <div className={`font-medium ${themeClasses.text.primary}`}>
                    User Profile & Settings
                  </div>
                  <div className={`text-sm ${themeClasses.text.secondary} mt-1`}>
                    Account information, preferences, and configuration
                  </div>
                  <div className="text-xs text-blue-600 dark:text-blue-400 mt-1">
                    Estimated size: 1 KB
                  </div>
                </div>
              </div>
              <div className={`flex items-start space-x-3 p-4 border rounded-lg ${themeClasses.border.primary}`}>
                <input
                  type="checkbox"
                  checked={false}
                  readOnly
                  className="mt-1 h-4 w-4 text-blue-600 border-gray-300 rounded"
                />
                <FileText className={`h-5 w-5 mt-0.5 ${themeClasses.text.primary}`} />
                <div className="flex-1">
                  <div className={`font-medium ${themeClasses.text.primary}`}>
                    Documents & Files
                  </div>
                  <div className={`text-sm ${themeClasses.text.secondary} mt-1`}>
                    Uploaded documents, PDFs, and attachments
                  </div>
                  <div className="text-xs text-blue-600 dark:text-blue-400 mt-1">
                    Estimated size: ~50 MB
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Export Button */}
          <button
            disabled={true}
            className={`w-full ${themeClasses.components.button.primary} py-3 px-4 font-medium flex items-center justify-center space-x-2 opacity-50 cursor-not-allowed`}
          >
            <Download className="h-5 w-5" />
            <span>Start Export</span>
          </button>
        </div>
      </div>
    </div>
  );

  // Main content for Pro users
  const mainContent = (
    <div className={themeClasses.layout.container}>
      <div className="space-y-6">
        {/* Header */}
        <div className={themeClasses.layout.header}>
          <h1 className={`text-3xl font-bold ${themeClasses.text.primary} mb-2`}>
            Data Export Dashboard
          </h1>
          <p className={themeClasses.text.secondary}>
            Export your EnCompliance data in multiple formats. Facility administrators now enjoy unlimited exports with a 72-hour secure download window.
          </p>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-6">
            <div className="flex items-center space-x-2">
              <AlertCircle className="h-5 w-5 text-red-600" />
              <span className="text-red-800 dark:text-red-200">{error}</span>
            </div>
          </div>
        )}

        {/* Current Export Status */}
        {currentExport && (currentExport.status === 'processing' || currentExport.status === 'pending') && (
          <div className={`${themeClasses.components.card} mb-6`}>
            <h2 className={`text-xl font-semibold ${themeClasses.text.primary} mb-4`}>
              Export in Progress
            </h2>
            <div className="flex items-center space-x-4">
              <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
              <div className="flex-1">
                <div className="flex justify-between items-center mb-2">
                  <span className={themeClasses.text.secondary}>
                    Exporting {currentExport.data_types.length} data types as {currentExport.format.toUpperCase()}
                  </span>
                  <span className={`text-sm ${themeClasses.text.secondary}`}>
                    {currentExport.progress_percentage}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <div 
                    className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${currentExport.progress_percentage}%` }}
                  ></div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Export Configuration */}
        {quotaStatus && (
          <div className={themeClasses.components.card}>
            <h2 className={`text-xl font-semibold ${themeClasses.text.primary} mb-6`}>
              Configure Export
            </h2>
            
            {/* Format Selection */}
            <div className="mb-6">
              <label className={`block text-sm font-medium ${themeClasses.text.primary} mb-3`}>
                Export Format
              </label>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {formatOptions.map((format) => (
                  <button
                    key={format.key}
                    onClick={() => setSelectedFormat(format.key)}
                    className={`p-4 border rounded-lg text-left transition-all ${
                      selectedFormat === format.key
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                        : `${themeClasses.border.primary} hover:border-blue-300 dark:hover:border-blue-600`
                    }`}
                  >
                    <div className="flex items-center space-x-3 mb-2">
                      <span className="text-2xl">{format.icon}</span>
                      <div className={`font-medium ${themeClasses.text.primary}`}>
                        {format.label}
                      </div>
                    </div>
                    <div className={`text-sm ${themeClasses.text.secondary}`}>
                      {format.description}
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Data Type Selection */}
            <div className="mb-6">
              <label className={`block text-sm font-medium ${themeClasses.text.primary} mb-3`}>
                Data to Export
              </label>
              <div className="space-y-3">
                {dataTypeOptions.map((option) => {
                  const IconComponent = option.icon;
                  return (
                    <label 
                      key={option.key} 
                      className={`flex items-start space-x-3 p-4 border rounded-lg cursor-pointer transition-all ${
                        selectedDataTypes.includes(option.key)
                          ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                          : `${themeClasses.border.primary} hover:bg-gray-50 dark:hover:bg-gray-700`
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={selectedDataTypes.includes(option.key)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedDataTypes([...selectedDataTypes, option.key]);
                          } else {
                            setSelectedDataTypes(selectedDataTypes.filter(type => type !== option.key));
                          }
                        }}
                        className="mt-1 h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                      />
                      <IconComponent className={`h-5 w-5 mt-0.5 ${themeClasses.text.primary}`} />
                      <div className="flex-1">
                        <div className={`font-medium ${themeClasses.text.primary}`}>
                          {option.label}
                        </div>
                        <div className={`text-sm ${themeClasses.text.secondary} mt-1`}>
                          {option.description}
                        </div>
                        <div className="text-xs text-blue-600 dark:text-blue-400 mt-1">
                          Estimated size: {option.estimatedSize}
                        </div>
                      </div>
                    </label>
                  );
                })}
              </div>
            </div>

            {/* Size Estimate */}
            {estimate && (
              <div className="mb-6 bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
                <h3 className={`font-medium ${themeClasses.text.primary} mb-3 flex items-center space-x-2`}>
                  <Info className="h-5 w-5" />
                  <span>Export Estimate</span>
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <div className={`text-sm ${themeClasses.text.secondary}`}>Estimated Size</div>
                    <div className={`font-medium ${themeClasses.text.primary}`}>
                      {estimate.estimated_size_mb} MB
                    </div>
                  </div>
                  <div>
                    <div className={`text-sm ${themeClasses.text.secondary}`}>Format</div>
                    <div className={`font-medium ${themeClasses.text.primary}`}>
                      {selectedFormat.toUpperCase()}
                    </div>
                  </div>
                  <div>
                    <div className={`text-sm ${themeClasses.text.secondary}`}>Fee</div>
                    <div className={`font-medium ${estimate.requires_fee ? 'text-yellow-600' : 'text-green-600'}`}>
                      {estimate.requires_fee ? `$${estimate.fee_amount}` : 'Included'}
                    </div>
                  </div>
                </div>
                {estimate.requires_fee && (
                  <div className="mt-3 flex items-center space-x-2 text-sm text-yellow-600 dark:text-yellow-400">
                    <DollarSign className="h-4 w-4" />
                    <span>Additional fee applies for exports over 1GB ($5 per GB)</span>
                  </div>
                )}
              </div>
            )}

            {/* Export Button */}
            <button
              onClick={initiateExport}
              disabled={selectedDataTypes.length === 0 || estimating || isExporting}
              className={`w-full ${themeClasses.components.button.primary} py-3 px-4 font-medium flex items-center justify-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              {isExporting ? (
                <>
                  <Loader2 className="h-5 w-5 animate-spin" />
                  <span>Starting Export...</span>
                </>
              ) : estimating ? (
                <>
                  <RefreshCw className="h-5 w-5 animate-spin" />
                  <span>Calculating...</span>
                </>
              ) : (
                <>
                  <Download className="h-5 w-5" />
                  <span>Start Export</span>
                </>
              )}
            </button>
          </div>
        )}

        {/* Export History */}
        {exportHistory.length > 0 && (
          <div className={themeClasses.components.card}>
            <h2 className={`text-xl font-semibold ${themeClasses.text.primary} mb-4`}>
              Export History
            </h2>
            <div className="space-y-3">
              {exportHistory.map((exportItem) => (
                <div 
                  key={exportItem.id}
                  className={`p-4 border rounded-lg ${themeClasses.border.primary}`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className={`p-2 rounded-full ${
                        exportItem.status === 'completed' ? 'bg-green-100 dark:bg-green-900/20' :
                        exportItem.status === 'failed' ? 'bg-red-100 dark:bg-red-900/20' :
                        'bg-blue-100 dark:bg-blue-900/20'
                      }`}>
                        {exportItem.status === 'completed' ? (
                          <CheckCircle className="h-5 w-5 text-green-600" />
                        ) : exportItem.status === 'failed' ? (
                          <AlertCircle className="h-5 w-5 text-red-600" />
                        ) : (
                          <Clock className="h-5 w-5 text-blue-600" />
                        )}
                      </div>
                      <div>
                        <div className={`font-medium ${themeClasses.text.primary}`}>
                          {exportItem.format.toUpperCase()} Export
                        </div>
                        <div className={`text-sm ${themeClasses.text.secondary}`}>
                          {exportItem.data_types.length} data types • {new Date(exportItem.created_at).toLocaleDateString()}
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className={`text-sm font-medium ${
                        exportItem.status === 'completed' ? 'text-green-600' :
                        exportItem.status === 'failed' ? 'text-red-600' :
                        'text-blue-600'
                      }`}>
                        {exportItem.status.charAt(0).toUpperCase() + exportItem.status.slice(1)}
                      </div>
                      {exportItem.status === 'completed' && exportItem.download_expires_at && (
                        <div className={`text-xs ${themeClasses.text.secondary}`}>
                          Expires: {new Date(exportItem.download_expires_at).toLocaleDateString()}
                        </div>
                      )}
                    </div>
                  </div>
                  {exportItem.error_message && (
                    <div className="mt-2 text-sm text-red-600 dark:text-red-400">
                      Error: {exportItem.error_message}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );

  // Custom access control for data export (facility administrators only)
  const canUseDataExport = canUseFeatureWithRole(userTier, 'data_export', user?.user_role, user?.subscription_status);
  
  if (!canUseDataExport) {
    // Show access denied message for team members and upgrade prompt for free users
  return (
      <div className={themeClasses.layout.container}>
        <div className="space-y-6">
          {/* Header */}
          <div className={themeClasses.layout.header}>
            <h1 className={`text-3xl font-bold ${themeClasses.text.primary} mb-2`}>
              Data Export Dashboard
            </h1>
            <p className={themeClasses.text.secondary}>
              Export your EnCompliance data in multiple formats.
            </p>
          </div>

          {/* Access Restriction Message */}
          <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-6 text-center">
            <div className="mb-4">
              <svg className="h-16 w-16 text-yellow-600 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m0 0v2m0-2h2m-2 0H9m11-7V8a4 4 0 00-8 0v1M9 12h6m-6 0a4 4 0 00-4 4v4a4 4 0 004 4h6a4 4 0 004-4v-4a4 4 0 00-4-4" />
              </svg>
            </div>
            
            <>
              <h3 className={`text-xl font-semibold ${themeClasses.text.primary} mb-3`}>
                Facility Administrator Access Required
              </h3>
              <p className={`${themeClasses.text.secondary} mb-4`}>
                For security and compliance reasons, only facility administrators can export organization data.
                Please contact your administrator if you need an export generated on your behalf.
              </p>
            </>
          </div>

          {/* Preview of Feature Benefits */}
          <div className={themeClasses.components.card}>
            <h2 className={`text-xl font-semibold ${themeClasses.text.primary} mb-4`}>
              Data Export Features
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="flex items-start space-x-3">
                <div className="w-8 h-8 bg-blue-100 dark:bg-blue-900/20 rounded-full flex items-center justify-center flex-shrink-0">
                  <svg className="w-4 h-4 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                </div>
                <div>
                  <h3 className={`font-medium ${themeClasses.text.primary}`}>Multiple Export Formats</h3>
                  <p className={`text-sm ${themeClasses.text.secondary}`}>CSV, PDF, and JSON formats available</p>
                </div>
              </div>
              
              <div className="flex items-start space-x-3">
                <div className="w-8 h-8 bg-green-100 dark:bg-green-900/20 rounded-full flex items-center justify-center flex-shrink-0">
                  <svg className="w-4 h-4 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                </div>
                <div>
                  <h3 className={`font-medium ${themeClasses.text.primary}`}>Comprehensive Data Types</h3>
                  <p className={`text-sm ${themeClasses.text.secondary}`}>All your compliance data in one export</p>
                </div>
              </div>
              
              <div className="flex items-start space-x-3">
                <div className="w-8 h-8 bg-purple-100 dark:bg-purple-900/20 rounded-full flex items-center justify-center flex-shrink-0">
                  <svg className="w-4 h-4 text-purple-600" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
                  </svg>
                </div>
                <div>
                  <h3 className={`font-medium ${themeClasses.text.primary}`}>Unlimited Exports</h3>
                  <p className={`text-sm ${themeClasses.text.secondary}`}>Facility administrators can export data whenever needed</p>
                </div>
              </div>
              
              <div className="flex items-start space-x-3">
                <div className="w-8 h-8 bg-orange-100 dark:bg-orange-900/20 rounded-full flex items-center justify-center flex-shrink-0">
                  <svg className="w-4 h-4 text-orange-600" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M2.166 4.999A11.954 11.954 0 0010 1.944 11.954 11.954 0 0017.834 5c.11.65.166 1.32.166 2.001 0 5.225-3.34 9.67-8 11.317C5.34 16.67 2 12.225 2 7c0-.682.057-1.35.166-2.001zm11.541 3.708a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                </div>
                <div>
                  <h3 className={`font-medium ${themeClasses.text.primary}`}>Secure & Compliant</h3>
                  <p className={`text-sm ${themeClasses.text.secondary}`}>72-hour secure download window</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
  );
  }

  return mainContent;
};

export default ExportDashboard; 