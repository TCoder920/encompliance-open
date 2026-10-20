/*
  Description: Dashboard page component for authenticated users. Displays key metrics, recent activity, and navigation to core features.
  Purpose: Serves as the main landing page after login, providing users with an overview and access to essential tools.
*/
import React, { useState, useEffect, useCallback } from 'react';
import { Clock, Search, Eye, Trash2, MessageSquare, RefreshCw, CheckCircle, XCircle, File, Upload, Calendar, AlertTriangle, FileType, Building2 } from 'lucide-react';
import ErrorMessage from '../components/ErrorMessage';
import { useAuth } from '../contexts/AuthContext';
import documentService from '../services/documentService';
import DocumentUploader from '../components/DocumentUploader';
import DocumentLabelEditor from '../components/DocumentLabelEditor';
import { formatDateTime } from '../utils/dateUtils';
import { 
  getConversationSummaries, 
  deleteConversation, 
  deleteAllConversations,
  resetApiCallTracking
} from '../services/aiService';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { Tooltip } from 'react-tooltip';
import { getTierFromSubscriptionStatus } from '../utils/tiers';
import { canAccessFeature } from '../utils/accessControl';
import QuickAccessLinks from '../components/QuickAccessLinks';
import { realtimeSyncService } from '../services/realtimeSync';
import api from '../services/api';

// Define the structure of the conversation summary from the backend
interface ConversationSummary {
  conversation_id: number;
  first_query_text: string | null;
  last_updated_at: string; // ISO string date
  message_count: number;
  document_reference: string | null;
  operation_type: string | null;
}

interface DashboardProps {
  preloadedDocuments?: any[];
}

// Add these utility functions outside the component
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

// Maximum retry attempts - we'll keep this but reduce to 2
const MAX_RETRIES = 2;

// Add this helper function outside the Dashboard component
function formatFileSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' bytes';
  else if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
  else return (bytes / 1048576).toFixed(1) + ' MB';
}

// Helper function to format expiration date and determine status
function getExpirationStatus(expirationDate?: string, daysUntilExpiry?: number) {
  if (!expirationDate) return null;

  const expDate = new Date(expirationDate);
  const today = new Date();
  const timeDiff = expDate.getTime() - today.getTime();
  const daysLeft = Math.ceil(timeDiff / (1000 * 3600 * 24));

  let status: 'expired' | 'warning' | 'normal' = 'normal';
  let color = 'text-green-600 dark:text-green-400';
  let bgColor = 'bg-green-50 dark:bg-green-900/20';
  let message = `Expires ${expDate.toLocaleDateString()}`;

  if (daysLeft < 0) {
    status = 'expired';
    color = 'text-red-600 dark:text-red-400';
    bgColor = 'bg-red-50 dark:bg-red-900/20';
    message = `Expired ${Math.abs(daysLeft)} day${Math.abs(daysLeft) !== 1 ? 's' : ''} ago`;
  } else if (daysLeft <= 30) {
    status = 'warning';
    color = 'text-amber-600 dark:text-amber-400';
    bgColor = 'bg-amber-50 dark:bg-amber-900/20';
    message = daysLeft === 0 ? 'Expires today' : `Expires in ${daysLeft} day${daysLeft !== 1 ? 's' : ''}`;
  }

  return { status, color, bgColor, message, daysLeft };
}

// Helper function to get document type display name
function getDocumentTypeDisplay(documentType?: string) {
  if (!documentType) return null;
  
  const typeMap: { [key: string]: string } = {
    'license': 'License',
    'certification': 'Certification',
    'permit': 'Permit',
    'policy': 'Policy',
    'insurance': 'Insurance',
    'contract': 'Contract',
    'other': 'Other'
  };
  
  return typeMap[documentType] || documentType;
}



const Dashboard: React.FC<DashboardProps> = ({ preloadedDocuments = [] }) => {
  const { error: authError, clearError, user, refreshAuthState } = useAuth();
  const [localError, setLocalError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalConversations, setTotalConversations] = useState(0);
  const itemsPerPage = 5; // Number of conversations per page in the recent queries list
  const [documents, setDocuments] = useState<any[]>(preloadedDocuments || []);
  const [showUploadPrompt, setShowUploadPrompt] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [refreshStatus, setRefreshStatus] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [dataLoadAttempted, setDataLoadAttempted] = useState(false);
  const [isLoadingPage, setIsLoadingPage] = useState(false);
  const [syncedUser, setSyncedUser] = useState(user);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [paymentVerificationFailed, setPaymentVerificationFailed] = useState(false);
  const [pendingSessionId, setPendingSessionId] = useState<string | null>(null);
  const navigate = useNavigate();

  // Function to fetch conversation summaries - simplify to remove retry logic since we handle that in the service
  const fetchConversations = useCallback(async (currentPage: number) => {
    try {
      const data = await getConversationSummaries(currentPage, itemsPerPage);
      
      // Handle throttled responses differently - don't update state if the response was throttled
      if (data && data.throttled) {
        console.log('Received throttled response, keeping existing conversation data');
        return; // Don't update state with empty data from throttling
      }
      
      if (data && data.conversations) {
        const calculatedTotalPages = Math.ceil((data.total || 0) / itemsPerPage);
        
        // Set conversations directly from the initial fetch
        setConversations(data.conversations);
        setTotalPages(calculatedTotalPages);
        setTotalConversations(data.total || 0);
        
        // Reset to page 1 if we're on a page that no longer exists
        if (currentPage > calculatedTotalPages && calculatedTotalPages > 0 && currentPage !== 1) {
          setPage(1); 
        }
      } else {
        setConversations([]);
        setTotalPages(1);
        setTotalConversations(0);
      }
    } catch (err) {
      console.error("Error in fetchConversations:", err);
      setConversations([]);
      setTotalPages(1);
      setTotalConversations(0);
    }
  }, [itemsPerPage]); // Dependency: itemsPerPage

  const refreshDocuments = useCallback(async () => {
    try {
      const docs = await documentService.listDocuments();
      setDocuments(docs);
    } catch (error) {
      console.error('Error refreshing documents:', error);
    }
  }, []);

  const handleLabelUpdate = useCallback((documentId: number, newLabel?: string) => {
    setDocuments(prevDocs => 
      prevDocs.map(doc => 
        doc.id === documentId 
          ? { ...doc, custom_label: newLabel } 
          : doc
      )
    );
  }, []);

  // Subscribe to real-time sync events for team members
  useEffect(() => {
    if (user?.user_role === 'team_member' && user?.facility_id) {
      // Force sync on component mount to get latest data
      const performInitialSync = async () => {
        try {
          console.log('Forcing initial account sync for team member');
          await realtimeSyncService.forceSync('account');
          await realtimeSyncService.forceSync('documents');
        } catch (error) {
          console.error('Failed to perform initial sync:', error);
        }
      };
      
      performInitialSync();

      const unsubscribeAccount = realtimeSyncService.subscribe('account_update', (event) => {
        console.log('Received account update:', event.data);
        // Update the synced user data
        setSyncedUser(prev => ({
          ...prev,
          state: event.data.state,
          facility_type: event.data.facility_types ? event.data.facility_types.join(', ') : prev?.facility_type,
          operation_name: event.data.operation_name || prev?.operation_name,
          subscription_status: event.data.subscription_status || prev?.subscription_status
        }));
      });

      const unsubscribeDocuments = realtimeSyncService.subscribe('document_update', async (event) => {
        console.log('Received document update:', event.data);
        // Refresh documents when admin makes changes
        await refreshDocuments();
      });

      return () => {
        unsubscribeAccount();
        unsubscribeDocuments();
      };
    }
  }, [user?.user_role, user?.facility_id, refreshDocuments]);

  // Update syncedUser when user prop changes
  useEffect(() => {
    setSyncedUser(user);
  }, [user]);

  // Handle upgrade success/cancellation messages
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const upgradeStatus = urlParams.get('upgrade');
    
    if (upgradeStatus === 'success') {
      // Check if we have a session_id to verify
      const sessionId = urlParams.get('session_id');
      
      if (sessionId) {
        setPendingSessionId(sessionId); // Store for potential manual retry
        
        const verifyUpgrade = async (retryCount = 0) => {
          const maxRetries = 3;
          const retryDelay = 2000; // 2 seconds
          
          try {
            console.log(`Verifying checkout session (attempt ${retryCount + 1}):`, sessionId);
            const verifyResponse = await api.post(`/payments/verify-payment?session_id=${sessionId}`);
            
            if (verifyResponse.data.success) {
              // Success cases
              if (verifyResponse.data.action === 'already_upgraded' || verifyResponse.data.action === 'already_processed') {
                setSuccessMessage('🎉 Welcome to EnCompliance Pro! Your subscription is already active.');
              } else {
              setSuccessMessage('🎉 Welcome to EnCompliance Pro! Your subscription has been activated and your facility is ready.');
              }
              
              console.log('Checkout session verified successfully:', verifyResponse.data);
              
              // Clear retry states on success
              setPaymentVerificationFailed(false);
              setPendingSessionId(null);
              
              // Refresh user data with a small delay
              setTimeout(async () => {
                try {
                  const refreshed = await refreshAuthState();
                  if (refreshed) {
                    console.log('User data refreshed after verification success');
                  }
                } catch (error) {
                  console.error('Failed to refresh user data after verification:', error);
                }
              }, 1000);
              
            } else {
              // Handle different failure scenarios
              console.error('Checkout session verification failed:', verifyResponse.data);
              
              if (verifyResponse.data.status === 'payment_incomplete') {
                // Payment not yet processed - this might be temporary
                if (retryCount < maxRetries) {
                  console.log(`Payment incomplete, retrying in ${retryDelay}ms...`);
                  setTimeout(() => verifyUpgrade(retryCount + 1), retryDelay);
                  return;
                } else {
                  setPaymentVerificationFailed(true);
                  setLocalError('Payment is still being processed. Please wait a few minutes and try the "Retry Payment Verification" button below, or contact support if the issue persists.');
                }
              } else if (verifyResponse.data.status === 'upgrade_incomplete') {
                setPaymentVerificationFailed(true);
                setLocalError('Payment was processed but account upgrade is incomplete. Please try the "Retry Payment Verification" button below or contact support for assistance.');
              } else {
                setPaymentVerificationFailed(true);
                setLocalError(`Payment verification failed: ${verifyResponse.data.message || 'Unknown error'}. Please try the "Retry Payment Verification" button below or contact support if your payment was processed.`);
              }
            }
          } catch (error: any) {
            console.error('Error verifying checkout session:', error);
            
            // Check if this is a network/temporary error that we should retry
            const isRetryableError = error.code === 'NETWORK_ERROR' || 
                                   error.response?.status >= 500 || 
                                   error.response?.status === 429;
            
            if (isRetryableError && retryCount < maxRetries) {
              console.log(`Retryable error, attempting retry ${retryCount + 1} in ${retryDelay}ms...`);
              setTimeout(() => verifyUpgrade(retryCount + 1), retryDelay);
              return;
            }
            
            // Final error handling
            setPaymentVerificationFailed(true);
            if (error.response?.data?.detail) {
              setLocalError(`Payment verification failed: ${error.response.data.detail}. Please try the "Retry Payment Verification" button below or contact support if your payment was processed.`);
            } else {
              setLocalError('Payment verification failed. Please try the "Retry Payment Verification" button below or contact support if your payment was processed.');
            }
          }
        };
        
        verifyUpgrade();
      } else {
        // Fallback for old URLs without session_id - webhook should have handled this
        setSuccessMessage('🎉 Welcome to EnCompliance Pro! Your subscription has been activated and your facility is ready.');
        
        // Still try to refresh user data
        setTimeout(async () => {
          try {
            await refreshAuthState();
          } catch (error) {
            console.error('Failed to refresh user data:', error);
          }
        }, 500);
      }
      
      // Clear the URL parameter
      window.history.replaceState({}, '', window.location.pathname);
    } else if (upgradeStatus === 'cancelled') {
      setLocalError('Payment was cancelled. You can try upgrading again anytime from your settings.');
      // Clear the URL parameter
      window.history.replaceState({}, '', window.location.pathname);
    }
  }, [refreshAuthState]);

  // Use a separate useEffect for initial loading with sequential API calls
  useEffect(() => {
    // Reset API call tracking on component mount to prevent throttling issues
    resetApiCallTracking();
    
    // Skip if we've already attempted to load data
    if (dataLoadAttempted) return;
    
    const loadInitialData = async () => {
      setIsLoading(true);
      setDataLoadAttempted(true);
      
      try {
        // Load data sequentially with a delay between calls to reduce server load
        await fetchConversations(page);
        // Add a delay between API calls
        await delay(1000);
        await refreshDocuments();
        setLocalError(null);
      } catch (err) {
        setLocalError('Failed to load dashboard data. Please try again later.');
        console.error("Dashboard data load error:", err);
      } finally {
        setIsLoading(false);
      }
    };
    
    loadInitialData();
    
    return () => {
      if (authError) clearError();
    };
  }, [authError, clearError, dataLoadAttempted, fetchConversations, refreshDocuments]);

  const handleNavigation = (page: string) => {
    try {
      if (page.startsWith('document/')) {
          // const docId = page.split('/')[1];
          // Perform navigation or validation logic if needed
      }
      navigate(page);
    } catch (err) {
      setLocalError('Unable to navigate to the requested page. Please try again.');
    }
  };
  
  const handleViewConversation = (conversationId: number) => {
    navigate(`/chat/${conversationId}`);
  };
  
  const handleDeleteConversation = async (conversationId: number, event: React.MouseEvent) => {
    event.stopPropagation();
    
    if (!window.confirm('Are you sure you want to delete this entire conversation?')) {
      return;
    }
    
    setIsLoading(true);
    setLocalError(null);
    try {
      await deleteConversation(conversationId);
      
      // Calculate expected total and pages after deletion using state
      const newTotalConversations = Math.max(0, totalConversations - 1);
      const newTotalPages = Math.ceil(newTotalConversations / itemsPerPage);

      // Update the total count state immediately
      setTotalConversations(newTotalConversations);

      // Logic identical to AllQueriesPage:
      // If this was the last item on the page and not the first page, go to the previous page
      if (conversations.length === 1 && page > 1) {
        setPage(page - 1);
      }
      // If current page is now beyond the new total pages, go to the last page
      else if (page > newTotalPages && newTotalPages > 0) {
        setPage(newTotalPages);
      }
      // Otherwise, refetch the current page's data
      else {
        await fetchConversations(page);
      }

      // Optional: Display success message (removed in previous step, can be added back if needed)
      // alert(`Successfully deleted conversation (${result.deleted_count} messages).`);

    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Failed to delete the conversation. Please try again.';
      setLocalError(errorMsg);
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleUploadComplete = async (file: File) => {
    try {
      setIsLoading(true); 
      await documentService.uploadDocument(file);
      setUploadSuccess(true);
      setShowUploadPrompt(false);
      setShowUploadModal(false);
      
      try {
        const refreshedDocs = await documentService.refreshDocumentCache(true);
        setDocuments(refreshedDocs);
      } catch (refreshError) {
        setLocalError('Document uploaded, but failed to refresh the list. Please refresh the page manually.');
      }
    } catch (uploadErr) {
      let errorMessage = 'Failed to upload document. Please try again.';
      if (axios.isAxiosError(uploadErr) && uploadErr.response?.data?.detail) {
          errorMessage = `Upload failed: ${uploadErr.response.data.detail}`;
      } else if (uploadErr instanceof Error) {
          errorMessage = `Upload failed: ${uploadErr.message}`;
      }
      setLocalError(errorMessage);
      setUploadSuccess(false);
    } finally {
      setIsLoading(false); 
      setTimeout(() => setUploadSuccess(false), 5000);
    }
  };
  
  const handleViewDocument = (documentId: number) => {
    const docIdStr = documentId.toString();
    documentService.openDocumentInNewTab(docIdStr);
  };
  
  const handleDeleteDocument = async (documentId: number) => {
    try {
      await documentService.deleteDocument(documentId);
      const userDocuments = await documentService.listDocuments();
      setDocuments(userDocuments);
    } catch (err) {
      setLocalError('Failed to delete document. Please try again.');
    }
  };
  
  const handlePageChange = (newPage: number) => {
    // Validate page bounds
    if (newPage < 1 || newPage > totalPages) {
      return;
    }
    
    // Only update if the page is different
    if (newPage !== page) {
      setPage(newPage);
      
      // Fetch conversations for the new page
      setIsLoadingPage(true);
      fetchConversations(newPage)
        .then(() => {
          setLocalError(null);
        })
        .catch((err) => {
          console.error("Error loading page data:", err);
          setLocalError('Failed to load conversations. Please try again later.');
        })
        .finally(() => {
          setIsLoadingPage(false);
        });
    }
  };
  
  const handleDeleteAll = async () => {
    if (window.confirm('Are you sure you want to delete ALL conversation history? This action cannot be undone.')) {
      setIsLoading(true);
      setLocalError(null);
      try {
        const result = await deleteAllConversations();
        setConversations([]);
        setPage(1);
        setTotalPages(1);
        alert(`Successfully deleted ${result.count} log entries across all conversations.`);
      } catch (error) {
        const errorMsg = error instanceof Error ? error.message : 'Failed to delete all conversations.';
        setLocalError(errorMsg);
      } finally {
        setIsLoading(false);
      }
    }
  };
  
  const handleRetryPaymentVerification = async () => {
    if (!pendingSessionId) {
      setLocalError('No payment session to retry. Please contact support.');
      return;
    }
    
    setLocalError(null);
    setPaymentVerificationFailed(false);
    
    try {
      console.log('Manually retrying payment verification for session:', pendingSessionId);
      const verifyResponse = await api.post(`/payments/verify-payment?session_id=${pendingSessionId}`);
      
      if (verifyResponse.data.success) {
        // Success cases
        if (verifyResponse.data.action === 'already_upgraded' || verifyResponse.data.action === 'already_processed') {
          setSuccessMessage('🎉 Welcome to EnCompliance Pro! Your subscription is already active.');
        } else {
          setSuccessMessage('🎉 Welcome to EnCompliance Pro! Your subscription has been activated and your facility is ready.');
        }
        
        console.log('Manual payment verification successful:', verifyResponse.data);
        
        // Clear retry states on success
        setPaymentVerificationFailed(false);
        setPendingSessionId(null);
        
        // Refresh user data
        setTimeout(async () => {
          try {
            const refreshed = await refreshAuthState();
            if (refreshed) {
              console.log('User data refreshed after manual verification success');
            }
          } catch (error) {
            console.error('Failed to refresh user data after manual verification:', error);
          }
        }, 1000);
        
      } else {
        console.error('Manual payment verification failed:', verifyResponse.data);
        setPaymentVerificationFailed(true);
        
        if (verifyResponse.data.status === 'payment_incomplete') {
          setLocalError('Payment is still being processed. Please wait a few more minutes before trying again, or contact support if the issue persists.');
        } else if (verifyResponse.data.status === 'upgrade_incomplete') {
          setLocalError('Payment was processed but account upgrade is incomplete. Please contact support for assistance.');
        } else {
          setLocalError(`Payment verification failed: ${verifyResponse.data.message || 'Unknown error'}. Please contact support if your payment was processed.`);
        }
      }
    } catch (error: any) {
      console.error('Error in manual payment verification:', error);
      setPaymentVerificationFailed(true);
      
      if (error.response?.data?.detail) {
        setLocalError(`Payment verification failed: ${error.response.data.detail}. Please contact support if your payment was processed.`);
      } else {
        setLocalError('Payment verification failed. Please contact support if your payment was processed.');
      }
    }
  };
  
  const handleRefreshClick = async () => {
    setIsRefreshing(true);
    setRefreshStatus(null);
    try {
      const result = await documentService.refreshVectorStore();

      if (result.success) {
        setRefreshStatus({ message: result.message, type: 'success' });
        try {
          const userDocuments = await documentService.listDocuments();
          setDocuments(userDocuments);
        } catch (listError) {
           console.error("[DEBUG] Dashboard: Failed to refresh document list display after successful vector store refresh:", listError);
           setRefreshStatus({
             message: `${result.message} (List refresh failed, please try again.)`,
             type: 'success'
           });
        }
      } else {
        setRefreshStatus({ message: result.message || 'Refresh failed.', type: 'error' });
      }
    } catch (err: any) {
      console.error("[DEBUG] Dashboard: Unexpected error during refresh click handler:", err);
      setRefreshStatus({ message: err.message || 'An unexpected error occurred during refresh.', type: 'error' });
    } finally {
      setIsRefreshing(false);
      setTimeout(() => setRefreshStatus(null), 7000); 
    }
  };
  
  // Calculate user tier from subscription status
  const userTier = getTierFromSubscriptionStatus(user?.subscription_status);
  const canAccessCalendar = canAccessFeature(userTier, 'calendar');
  
  // Instead of loading state, provide a stable UI state with error feedback
  if (isLoading && !dataLoadAttempted) {
    return (
      <div className="container mx-auto px-4 py-8 flex justify-center items-center h-64">
        <div className="animate-pulse text-navy-blue dark:text-white">Loading dashboard...</div>
      </div>
    );
  }
  
  return (
    <div className="container mx-auto px-4 py-6">
      {(localError || authError) && (
        <div className="mb-4">
          <ErrorMessage message={localError || authError} />
          {paymentVerificationFailed && pendingSessionId && (
            <div className="mt-3 text-center">
              <button
                onClick={handleRetryPaymentVerification}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors duration-200"
              >
                Retry Payment Verification
              </button>
            </div>
          )}
        </div>
      )}
      
      {successMessage && (
        <div className="mb-6 bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded flex justify-between items-center">
          <span>{successMessage}</span>
          <button 
            onClick={() => setSuccessMessage(null)}
            className="text-green-500 hover:text-green-700"
          >
            ×
          </button>
        </div>
      )}
      
      <div>
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-800 dark:text-white mb-4">
            Dashboard
          </h1>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white dark:bg-dark-surface p-6 rounded-lg shadow-md">
            <QuickAccessLinks canAccessCalendar={canAccessCalendar} />
          </div>
          
          <div className="bg-white dark:bg-dark-surface p-6 rounded-lg shadow-md md:col-span-2">
            <h2 className="text-xl font-bold text-navy-blue dark:text-white mb-4">Account Overview</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              <div className="border border-gray-200 dark:border-gray-700 rounded p-4 dark:bg-gray-800 min-w-0">
                <h3 className="font-bold text-gray-700 dark:text-gray-300 mb-2 text-sm">Name</h3>
                <p className="dark:text-white text-sm break-words overflow-hidden">{syncedUser?.full_name || user?.full_name || 'N/A'}</p>
              </div>
              <div className="border border-gray-200 dark:border-gray-700 rounded p-4 dark:bg-gray-800 min-w-0">
                <h3 className="font-bold text-gray-700 dark:text-gray-300 mb-2 text-sm">Operation Name</h3>
                <p className="dark:text-white text-sm break-words overflow-hidden">{syncedUser?.operation_name || user?.operation_name || 'N/A'}</p>
              </div>
              <div className="border border-gray-200 dark:border-gray-700 rounded p-4 dark:bg-gray-800 min-w-0">
                <h3 className="font-bold text-gray-700 dark:text-gray-300 mb-2 text-sm">Email</h3>
                <p className="dark:text-white text-sm break-words overflow-hidden">{syncedUser?.email || user?.email || 'N/A'}</p>
              </div>
              <div className="border border-gray-200 dark:border-gray-700 rounded p-4 dark:bg-gray-800 min-w-0">
                <h3 className="font-bold text-gray-700 dark:text-gray-300 mb-2 text-sm">State</h3>
                <p className="dark:text-white text-sm break-words overflow-hidden">{syncedUser?.state || user?.state || 'N/A'}</p>
              </div>
              <div className="border border-gray-200 dark:border-gray-700 rounded p-4 dark:bg-gray-800 min-w-0">
                <h3 className="font-bold text-gray-700 dark:text-gray-300 mb-2 text-sm">Facility Type(s)</h3>
                <p className="dark:text-white text-sm break-words overflow-hidden">{syncedUser?.facility_type || user?.facility_type || 'N/A'}</p>
              </div>
              <div className="border border-gray-200 dark:border-gray-700 rounded p-4 dark:bg-gray-800 min-w-0">
                <h3 className="font-bold text-gray-700 dark:text-gray-300 mb-2 text-sm">Subscription</h3>
                <p className="dark:text-white text-sm capitalize break-words overflow-hidden">
                  {syncedUser?.subscription_status === 'team_member' ? 'Team Member (Pro Access)' :
                   syncedUser?.subscription_status === 'pro' ? 'Pro' :
                   syncedUser?.subscription_status || user?.subscription_status || 'Free'}
                </p>
              </div>
            </div>
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <div className="bg-white dark:bg-dark-surface p-6 rounded-lg shadow-md">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold text-navy-blue dark:text-white">Recent Chat Sessions</h2>
              <div className="flex items-center space-x-3">
                {conversations.length > 0 && (
                  <button
                    onClick={handleDeleteAll}
                    className="p-2 text-red-600 dark:text-red-400 rounded-full hover:bg-red-100 dark:hover:bg-red-800"
                    disabled={isLoading}
                    data-tooltip-id="tooltip-delete-all-convos"
                    data-tooltip-content="Delete all conversation history"
                    data-tooltip-delay-show={0}
                    data-tooltip-float={true}
                  >
                    <Trash2 size={18} />
                  </button>
                )}
                <button
                  onClick={() => navigate('/allQueriesPage')}
                  className="p-2 text-navy-blue dark:text-blue-400 rounded-full hover:bg-blue-100 dark:hover:bg-blue-800"
                  data-tooltip-id="tooltip-view-all-convos"
                  data-tooltip-content="View all conversations"
                  data-tooltip-delay-show={0}
                  data-tooltip-float={true}
                >
                  <Eye size={18} />
                </button>
              </div>
            </div>
            
            {isLoading && conversations.length === 0 ? (
              <div className="text-center py-6 text-gray-500 dark:text-gray-400">Loading conversations...</div>
            ) : conversations.length > 0 ? (
              <div className="space-y-4">
                {conversations.map((conv) => (
                  <div 
                    key={conv.conversation_id} 
                    className="border-b border-gray-200 dark:border-gray-700 pb-3 last:border-b-0 last:pb-0 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 px-2 py-1 rounded transition-colors duration-150"
                    onClick={() => handleViewConversation(conv.conversation_id)}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center text-sm text-gray-500 dark:text-gray-400">
                        <Clock className="h-4 w-4 mr-1" />
                        <span>Updated {formatDateTime(conv.last_updated_at || '')}</span>
                      </div>
                      <button
                        onClick={(e) => handleDeleteConversation(conv.conversation_id, e)}
                        className="text-gray-400 dark:text-gray-500 hover:text-red-500 dark:hover:text-red-400 z-10 p-1 rounded-full hover:bg-gray-200 dark:hover:bg-gray-600 transition duration-150 transform hover:scale-110"
                        title="Delete conversation"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                    <p className="font-medium truncate dark:text-white mb-1">
                      {conv.first_query_text ? `"${conv.first_query_text}"` : 'Chat session started'}
                    </p>
                    <div className="text-sm text-gray-500">
                      <MessageSquare className="inline-block h-3 w-3 mr-1" />
                      <span>{conv.message_count} messages</span>
                    </div>
                  </div>
                ))}
                {totalPages > 1 && (
                  <div className="flex justify-center mt-4 space-x-2">
                    <button 
                      onClick={() => handlePageChange(page - 1)}
                      disabled={page <= 1}
                      className="px-3 py-1 text-sm rounded bg-gray-200 dark:bg-gray-700 disabled:opacity-50"
                    >
                      Previous
                    </button>
                    <span className="text-sm self-center">Page {page} of {totalPages}</span>
                    <button 
                      onClick={() => handlePageChange(page + 1)}
                      disabled={page >= totalPages}
                      className="px-3 py-1 text-sm rounded bg-gray-200 dark:bg-gray-700 disabled:opacity-50"
                    >
                      Next
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-6">
                <p className="text-gray-500 dark:text-gray-400 mb-3">No chat history found</p>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">Start a chat with the AI assistant to see your history here.</p>
                <button 
                  onClick={() => handleNavigation('/search')}
                  className="bg-navy-blue dark:bg-blue-700 text-white py-2 px-4 rounded hover:bg-blue-800 dark:hover:bg-blue-600 transition-colors duration-200"
                >
                  <Search className="h-4 w-4 inline mr-2" />
                  Ask AI Assistant
                </button>
              </div>
            )}
          </div>
          
          <div className="bg-white dark:bg-dark-surface p-6 rounded-lg shadow-md">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold text-navy-blue dark:text-white">Document Library</h2>
              <div className="flex items-center space-x-3">
                <button
                  onClick={() => setShowUploadModal(true)}
                  className="p-2 text-navy-blue dark:text-blue-400 rounded-full hover:bg-blue-100 dark:hover:bg-blue-800"
                  data-tooltip-id="tooltip-upload-doc"
                  data-tooltip-content="Upload Document"
                  data-tooltip-delay-show={0}
                  data-tooltip-float={true}
                >
                  <Upload size={18} />
                </button>
                {documents.length > 0 && (
                  <button
                    onClick={handleRefreshClick}
                    className={`p-2 text-navy-blue dark:text-blue-400 rounded-full hover:bg-blue-100 dark:hover:bg-blue-800 ${isRefreshing ? 'opacity-50 cursor-not-allowed' : ''}`}
                    disabled={isRefreshing}
                    data-tooltip-id="tooltip-refresh-sync"
                    data-tooltip-content={isRefreshing ? 'Refreshing Sync...' : 'Refresh Document Sync'}
                    data-tooltip-delay-show={0}
                    data-tooltip-float={true}
                  >
                    {isRefreshing ? (
                      <RefreshCw size={18} className="animate-spin" />
                    ) : (
                      <RefreshCw size={18} />
                    )}
                  </button>
                )}
              </div>
            </div>
            {refreshStatus && (
              <div className={`mt-2 p-2 rounded text-sm flex items-center ${refreshStatus.type === 'success' ? 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200' : 'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200'}`}>
                {refreshStatus.type === 'success' ? <CheckCircle className="h-4 w-4 mr-2 flex-shrink-0" /> : <XCircle className="h-4 w-4 mr-2 flex-shrink-0" />}
                {refreshStatus.message}
              </div>
            )}
            <p className="text-xs text-gray-500 dark:text-gray-400 my-4">
              These are your state compliance documents relative to your state and facility type(s).
            </p>
            {documents.length > 0 && (
              <div 
                className="mb-2 flex items-center space-x-2 text-sm text-gray-700 dark:text-gray-200 font-medium"
                data-tooltip-id="tooltip-total-doc-size"
                data-tooltip-content="Total size of all documents"
                data-tooltip-delay-show={0}
                data-tooltip-float={true}
              >
                <File size={18} className="text-gray-500 dark:text-gray-400 flex-shrink-0" />
                <span>{formatFileSize(documents.reduce((sum, doc) => sum + (doc.file_size || 0), 0))}</span>
              </div>
            )}
            <div className="grid grid-cols-1 gap-4 mt-4">
              {documents.map((doc) => {
                const expirationStatus = getExpirationStatus(doc.expiration_date, doc.days_until_expiry);
                const documentTypeDisplay = getDocumentTypeDisplay(doc.document_type);
                
                return (
                  <div key={doc.id} className="bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
                    <div className="flex justify-between items-start">
                      <div className="flex-1 mr-4 overflow-hidden">
                        {(doc as any).document_source === "manual_upload" ? (
                          <DocumentLabelEditor
                            documentId={doc.id}
                            currentLabel={doc.custom_label}
                            filename={doc.filename}
                            onLabelUpdate={(newLabel) => handleLabelUpdate(doc.id, newLabel)}
                            onTitleClick={() => handleViewDocument(doc.id)}
                          />
                        ) : (
                          <div>
                            <h3 
                              className="text-md font-semibold truncate text-blue-600 hover:text-blue-800 cursor-pointer"
                              onClick={() => handleViewDocument(doc.id)}
                            >
                              {(doc as any).regulation_title || doc.filename}
                            </h3>
                            <div className="text-sm text-gray-600 mt-1 truncate">
                              {doc.filename}
                            </div>
                            <div className="text-xs text-orange-600 mt-1">
                              Regulatory Document - Labels cannot be modified
                            </div>
                          </div>
                        )}
                        
                        <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                          {(doc as any).document_source === "manual_upload" && `Uploaded: ${formatDateTime(doc.uploaded_at)}`}
                        </div>

                        {/* Expiration Information Section - Only for manual uploads with expiration data */}
                        {(doc as any).document_source === "manual_upload" && (documentTypeDisplay || doc.expiration_date || doc.issuing_authority) && (
                          <div className="mt-3 pt-2 border-t border-gray-200 dark:border-gray-600">
                            <div className="flex flex-wrap gap-3 text-xs">
                              {/* Document Type */}
                              {documentTypeDisplay && (
                                <div className="flex items-center space-x-1 text-navy-blue dark:text-blue-400">
                                  <FileType size={12} />
                                  <span>{documentTypeDisplay}</span>
                                </div>
                              )}
                              
                              {/* Expiration Date with Status */}
                              {expirationStatus && (
                                <div className={`flex items-center space-x-1 px-2 py-1 rounded-full ${expirationStatus.bgColor}`}>
                                  {expirationStatus.status === 'expired' ? (
                                    <AlertTriangle size={12} className={expirationStatus.color} />
                                  ) : (
                                    <Calendar size={12} className={expirationStatus.color} />
                                  )}
                                  <span className={expirationStatus.color}>{expirationStatus.message}</span>
                                </div>
                              )}
                              
                              {/* Issuing Authority */}
                              {doc.issuing_authority && (
                                <div className="flex items-center space-x-1 text-gray-600 dark:text-gray-400">
                                  <Building2 size={12} />
                                  <span>{doc.issuing_authority}</span>
                                </div>
                              )}
                              
                              {/* Renewal Required Badge */}
                              {doc.renewal_required && (
                                <div className="flex items-center space-x-1 px-2 py-1 rounded-full bg-blue-50 dark:bg-blue-900/20">
                                  <RefreshCw size={12} className="text-blue-600 dark:text-blue-400" />
                                  <span className="text-blue-600 dark:text-blue-400">Renewal Required</span>
                                </div>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                      
                      <div className="flex space-x-2 flex-shrink-0">
                        <button 
                          onClick={() => handleViewDocument(doc.id)}
                          className="p-2 bg-blue-50 dark:bg-blue-900 text-blue-600 dark:text-blue-400 rounded-full hover:bg-blue-100 dark:hover:bg-blue-800"
                          data-tooltip-id="tooltip-view-doc"
                          data-tooltip-content="View Document"
                          data-tooltip-delay-show={0}
                          data-tooltip-float={true}
                        >
                          <Eye size={18} />
                        </button>
                        {(doc as any).document_source === "manual_upload" && (
                          <button
                            onClick={() => handleDeleteDocument(doc.id)}
                            className="p-2 bg-red-50 dark:bg-red-900 text-red-600 dark:text-red-400 rounded-full hover:bg-red-100 dark:hover:bg-red-800"
                            data-tooltip-id="tooltip-delete-doc"
                            data-tooltip-content="Delete Document"
                            data-tooltip-delay-show={0}
                            data-tooltip-float={true}
                          >
                            <Trash2 size={18} />
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Upload Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-dark-surface rounded-lg shadow-xl p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold text-navy-blue dark:text-white">Upload Document</h2>
              <button
                onClick={() => setShowUploadModal(false)}
                className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
              >
                <XCircle size={24} />
              </button>
            </div>
            <DocumentUploader 
              onUploadComplete={handleUploadComplete}
              allowedFileTypes={['.pdf', '.docx', '.doc', '.txt']}
              maxSizeMB={50}
              enableCustomLabel={true}
              enableExpirationTracking={user?.subscription_status === 'pro' && user?.user_role === 'facility_admin'}
            />
          </div>
        </div>
      )}

      <Tooltip id="tooltip-delete-all-convos" place="top" />
      <Tooltip id="tooltip-view-all-convos" place="top" />
      <Tooltip id="tooltip-upload-doc" place="top" />
      <Tooltip id="tooltip-refresh-sync" place="top" />
      <Tooltip id="tooltip-view-doc" place="top" />
      <Tooltip id="tooltip-delete-doc" place="top" />
      <Tooltip id="tooltip-total-doc-size" place="top" />
    </div>
  );
};

export default Dashboard;