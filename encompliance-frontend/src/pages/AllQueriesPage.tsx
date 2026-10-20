/*
  Description: Page component displaying all user queries and their statuses.
  Purpose: Allows users to review, filter, and manage their compliance-related queries in one place.
*/
import React, { useState, useEffect } from 'react';
import { Clock, MessageSquare, Trash2, ChevronLeft, ChevronRight, FileText, RefreshCw } from 'lucide-react';
import ErrorMessage from '../components/ErrorMessage';
import { formatDateTime } from '../utils/dateUtils';
import { deleteConversation, deleteAllConversations, getConversationSummaries, resetApiCallTracking } from '../services/aiService';
import { useNavigate } from 'react-router-dom';

interface ConversationSummary {
  conversation_id: number;
  first_query_text: string | null;
  last_updated_at: string; // ISO string date
  message_count: number;
  document_reference: string | null;
  operation_type: string | null;
}

const AllQueriesPage: React.FC = () => {
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalConversations, setTotalConversations] = useState(0);
  const [conversationsPerPage] = useState(10);
  const [manualPage, setManualPage] = useState('');
  const navigate = useNavigate();

  const fetchConversations = async () => {
    try {
      setLoading(true);
      
      const data = await getConversationSummaries(page, conversationsPerPage);
      
      // Set total logs and calculate total pages
      setTotalConversations(data.total || 0);
      const calculatedTotalPages = Math.ceil((data.total || 0) / conversationsPerPage);
      setTotalPages(calculatedTotalPages);
      
      // Set conversations directly from the API response
      if (data && data.conversations) {
        setConversations(data.conversations);
      } else {
        setConversations([]);
      }
      
      // Only reset to page 1 if we're on a page that no longer exists AND it's not a user-initiated page change
      if (page > calculatedTotalPages && calculatedTotalPages > 0 && page !== 1) {
        setPage(1); 
        // Don't refetch here - let the page change trigger the refetch
      }
    } catch (err) {
      console.error('Error fetching conversations:', err);
      setError('Failed to load conversations.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Reset API call tracking on component mount to prevent throttling issues
    resetApiCallTracking();
    
    // Only fetch on initial load
    if (conversations.length === 0) {
      fetchConversations();
    }
  }, []); // Remove page dependency to prevent automatic refetching

  const handleRefreshClick = () => {
    fetchConversations();
  };

  const handleDeleteConversation = async (conversationId: number, event: React.MouseEvent) => {
    // Prevent click from bubbling up to the parent container
    event.stopPropagation();
    
    // Confirm deletion
    if (!window.confirm('Are you sure you want to delete this entire conversation?')) {
      return;
    }
    
    try {
      setLoading(true);
      await deleteConversation(conversationId);
      
      // Calculate if we need to update pagination
      const newTotalPages = Math.ceil((totalConversations - 1) / conversationsPerPage);
      
      // If this was the last item on the page and not the first page, go to the previous page
      if (conversations.length === 1 && page > 1) {
        setPage(page - 1);
      }
      // If current page is now beyond the new total pages, go to the last page
      else if (page > newTotalPages && newTotalPages > 0) {
        setPage(newTotalPages);
      }
      // Otherwise, refetch the current page
      else {
        const data = await getConversationSummaries(page, conversationsPerPage);
        setTotalConversations(data.total || 0);
        setTotalPages(Math.ceil((data.total || 0) / conversationsPerPage));
        setConversations(data.conversations || []);
      }
      
      // Display success message
      alert(`Successfully deleted conversation.`);
      setError('');
    } catch (err) {
      console.error('Error deleting conversation:', err);
      setError('Failed to delete the conversation. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteAllConversations = async () => {
    // Confirm deletion
    if (!window.confirm('Are you sure you want to delete ALL conversations? This action cannot be undone.')) {
      return;
    }
    
    try {
      setLoading(true);
      
      await deleteAllConversations();
      
      // Clear the conversations from state
      setConversations([]);
      setTotalConversations(0);
      setTotalPages(1);
      setPage(1);
      setError('');
    } catch (err) {
      console.error('Error deleting all conversations:', err);
      setError('Failed to delete all conversations. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handlePageChange = (newPage: number) => {
    // Make sure we don't go below page 1
    if (newPage < 1) {
      newPage = 1;
    }
    
    // Make sure we don't go beyond the last page
    if (newPage > totalPages && totalPages > 0) {
      newPage = totalPages;
    }
    
    // Only update if the page is different
    if (newPage !== page) {
      setPage(newPage);
      
      // Fetch conversations for the new page
      setLoading(true);
      getConversationSummaries(newPage, conversationsPerPage)
        .then((data) => {
          setTotalConversations(data.total || 0);
          const calculatedTotalPages = Math.ceil((data.total || 0) / conversationsPerPage);
          setTotalPages(calculatedTotalPages);
          
          if (data && data.conversations) {
            setConversations(data.conversations);
          } else {
            setConversations([]);
          }
          setError('');
        })
        .catch((err) => {
          console.error('Error fetching conversations for page:', err);
          setError('Failed to load conversations.');
        })
        .finally(() => {
          setLoading(false);
        });
    }
  };

  const handleManualPageChange = (e: React.FormEvent) => {
    e.preventDefault();
    const pageNum = parseInt(manualPage);
    if (!isNaN(pageNum) && pageNum >= 1 && pageNum <= totalPages) {
      setPage(pageNum);
      setManualPage('');
    }
  };

  const handleViewConversation = (conversationId: number) => {
    navigate(`/chat/${conversationId}`);
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-navy-blue dark:text-white transition-colors duration-300">All Chat Sessions</h1>
        
        <div className="flex space-x-4">
          <button
            onClick={handleDeleteAllConversations}
            disabled={loading || conversations.length === 0}
            className={`px-4 py-2 rounded flex items-center ${
              loading || conversations.length === 0
                ? 'bg-gray-300 dark:bg-gray-700 text-gray-500 dark:text-gray-400 cursor-not-allowed'
                : 'bg-red-600 dark:bg-red-700 text-white hover:bg-red-700 dark:hover:bg-red-800'
            } transition-colors duration-300`}
          >
            <Trash2 className="h-4 w-4 mr-2" />
            Delete All
          </button>
          <button
            onClick={handleRefreshClick}
            className="bg-blue-500 hover:bg-blue-600 text-white py-1 px-3 rounded-md flex items-center"
            disabled={loading}
          >
            <RefreshCw className="w-4 h-4 mr-1" />
            Refresh
          </button>
        </div>
      </div>
      
      {loading && conversations.length === 0 ? (
        <div className="text-center py-8">
          <div className="animate-spin h-8 w-8 border-4 border-navy-blue dark:border-blue-500 border-t-transparent rounded-full mx-auto mb-4 transition-colors duration-300"></div>
          <p className="text-gray-600 dark:text-gray-300 transition-colors duration-300">Loading conversations...</p>
        </div>
      ) : error ? (
        <ErrorMessage message={error} type="error" onClose={() => setError('')} />
      ) : (
        <>
          {conversations.length === 0 ? (
            <div className="text-center py-8 border border-dashed border-gray-300 dark:border-gray-600 rounded-lg transition-colors duration-300">
              <MessageSquare className="h-12 w-12 mx-auto text-gray-400 dark:text-gray-500 transition-colors duration-300 mb-3" />
              <p className="text-gray-600 dark:text-gray-300 transition-colors duration-300 mb-2">No chat sessions found</p>
            </div>
          ) : (
            <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6 transition-colors duration-300">
              <div className="divide-y divide-gray-200 dark:divide-gray-700 transition-colors duration-300">
                {conversations.length > 0 ? (
                  conversations.map((conv) => (
                    <div 
                      key={conv.conversation_id} 
                      className="py-4 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors duration-150"
                      onClick={() => handleViewConversation(conv.conversation_id)}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <div className="flex items-center text-sm text-gray-500 dark:text-gray-400 transition-colors duration-300">
                          <Clock className="h-4 w-4 mr-1" />
                          <span>Updated {formatDateTime(conv.last_updated_at || '')}</span>
                        </div>
                        <button
                          onClick={(e) => handleDeleteConversation(conv.conversation_id, e)}
                          className="text-gray-400 dark:text-gray-500 hover:text-red-500 dark:hover:text-red-400 transition-colors duration-300 flex items-center transform hover:scale-110"
                          title="Delete conversation"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                      <p className="font-medium mb-2 text-gray-800 dark:text-gray-200 transition-colors duration-300">
                        {conv.first_query_text ? `"${conv.first_query_text}"` : 'Chat session started'}
                      </p>
                      <div className="text-sm text-gray-500">
                          <MessageSquare className="inline-block h-3 w-3 mr-1" />
                          <span>{conv.message_count} messages</span>
                          {conv.document_reference && 
                            <span className="ml-3 inline-flex items-center truncate" title={conv.document_reference}>
                              <FileText className="h-3 w-3 mr-1 flex-shrink-0"/> 
                              <span className="truncate">{conv.document_reference}</span>
                            </span>
                          }
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-8 border border-dashed border-gray-300 dark:border-gray-600 rounded-lg transition-colors duration-300">
                    <MessageSquare className="h-12 w-12 mx-auto text-gray-400 dark:text-gray-500 transition-colors duration-300 mb-3" />
                    <p className="text-gray-600 dark:text-gray-300 transition-colors duration-300 mb-2">No chat sessions found</p>
                  </div>
                )}
              </div>
            </div>
          )}
          
          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex flex-col items-center mt-6 space-y-3">
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => handlePageChange(page - 1)}
                  disabled={page === 1}
                  className={`p-2 rounded transition-colors duration-300 ${
                    page === 1 
                      ? 'bg-gray-100 dark:bg-gray-700 text-gray-400 dark:text-gray-500 cursor-not-allowed' 
                      : 'bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-500'
                  }`}
                >
                  <ChevronLeft className="h-5 w-5" />
                </button>
                
                <div className="text-sm text-gray-700 dark:text-gray-300 transition-colors duration-300">
                  Page {page} of {totalPages} {/* Total: {totalConversations} */}
                </div>
                
                <button
                  onClick={() => handlePageChange(page + 1)}
                  disabled={page === totalPages}
                  className={`p-2 rounded transition-colors duration-300 ${
                    page === totalPages 
                      ? 'bg-gray-100 dark:bg-gray-700 text-gray-400 dark:text-gray-500 cursor-not-allowed' 
                      : 'bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-500'
                  }`}
                >
                  <ChevronRight className="h-5 w-5" />
                </button>
              </div>
              
              {/* Manual page selection - only show if there are 3 or more pages */}
              {totalPages >= 3 && (
                <form onSubmit={handleManualPageChange} className="flex items-center space-x-2">
                  <label htmlFor="pageNumber" className="text-sm text-gray-600 dark:text-gray-400 transition-colors duration-300">Go to page:</label>
                  <input
                    id="pageNumber"
                    type="number"
                    min="1"
                    max={totalPages}
                    value={manualPage}
                    onChange={(e) => setManualPage(e.target.value)}
                    className="w-16 px-2 py-1 border border-gray-300 dark:border-gray-600 rounded text-sm bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-200 transition-colors duration-300"
                  />
                  <button
                    type="submit"
                    className="px-3 py-1 bg-navy-blue dark:bg-blue-600 text-white rounded text-sm hover:bg-blue-700 dark:hover:bg-blue-700 transition-colors duration-300"
                  >
                    Go
                  </button>
                </form>
              )}
            </div>
          )}
        </>
      )}
      
      <button
        onClick={() => navigate('/dashboard')}
        className="mt-6 px-4 py-2 bg-navy-blue dark:bg-blue-600 text-white rounded hover:bg-blue-700 dark:hover:bg-blue-700 transition-colors duration-300"
      >
        Back to Dashboard
      </button>
    </div>
  );
};

export default AllQueriesPage; 