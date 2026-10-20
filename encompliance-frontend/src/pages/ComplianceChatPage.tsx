/*
  Description: Compliance chat page component. Provides an AI-powered chat interface for compliance-related questions and document analysis.
  Purpose: Enables users to interact with the compliance assistant and receive guidance or document insights in real time.
*/
import React, { useState, useEffect, useCallback } from 'react';
import { FileText, ArrowLeft } from 'lucide-react';
import pdfService, { PDF } from '../services/pdfService';
import AIChat from '../components/AIChat';
import ErrorMessage from '../components/ErrorMessage';
import documentService from '../services/documentService';
import api from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate, useParams, useLocation } from 'react-router-dom';

// Define a unified interface for display
interface DisplayDocument {
    id: number;
    filename: string;
    type: 'standard' | 'user';
    filepath?: string; // From standard PDF
    url?: string;      // From user document
    uploaded_at?: string; // From user document
}

interface ComplianceChatPageProps {
  initialQueryId?: number;
  initialConversationId?: number;
  showFullConversation?: boolean;
}

const ComplianceChatPage: React.FC<ComplianceChatPageProps> = ({ 
  initialQueryId,
  initialConversationId,
  showFullConversation = false
}) => {
  const { user } = useAuth(); // Get user from context
  const navigate = useNavigate();
  const location = useLocation();
  const params = useParams();
  const conversationIdFromRoute = params.conversationId ? Number(params.conversationId) : undefined;
  const effectiveConversationId = initialConversationId || conversationIdFromRoute;
  const [pdfs, setPdfs] = useState<DisplayDocument[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedPDF, setSelectedPDF] = useState<DisplayDocument | null>(null);
  const [userDocuments, setUserDocuments] = useState<DisplayDocument[]>([]);
  const [initialQueryData, setInitialQueryData] = useState<any>(null);
  const [conversationData, setConversationData] = useState<any>(null);
  const [chatKey, setChatKey] = useState<string>(() => `chat-${Date.now()}`);

  // Determine operation type from user context, default to 'daycare' if not found
  const currentOperationType = user?.operation_type || 'daycare';

  // Reset chat when navigating to /search without a conversation ID (new chat)
  useEffect(() => {
    if (location.pathname === '/search' && !effectiveConversationId) {
      // This is a new chat - generate a new key to force AIChat to remount
      setChatKey(`chat-${Date.now()}`);
      // Clear any existing conversation data
      setConversationData(null);
      setInitialQueryData(null);
    }
  }, [location.pathname, effectiveConversationId]);

  // Load initial conversation data if provided
  useEffect(() => {
    if (effectiveConversationId) {
      const fetchConversationData = async () => {
        try {
          const response = await api.get(`/conversations/${effectiveConversationId}`);
          
          if (!response.data || !response.data.messages) {
            setError('Failed to load the conversation data.');
            return;
          }
          
          const data = response.data;
          
          // Format messages for AIChat
          const messages = data.messages.map((msg: any) => ({
            role: msg.role || (msg.sender === 'user' ? 'user' : 'assistant'),
            content: msg.content || msg.text || '',
            timestamp: msg.timestamp || msg.created_at
          }));
          
          setConversationData({
            conversationId: effectiveConversationId,
            initialConversation: messages,
            initialQuery: '',  // Don't auto-send when viewing conversation
          });
          
        } catch (err) {
          setError('An error occurred while loading the conversation.');
        }
      };
      
      fetchConversationData();
    }
  }, [effectiveConversationId]);

  // Load documents (both standard PDFs and user uploads)
  useEffect(() => {
    const loadDocuments = async () => {
      try {
        setIsLoading(true);
        // Fetch standard PDFs (now part of listDocuments)
        // const standardPdfList = await pdfService.listPDFs(); 
        // setPdfs(standardPdfList.map(pdf => ({ ...pdf, type: 'standard' })));
        // const standardPdfIds = standardPdfList.map(pdf => pdf.id);
        
        // Fetch all user-accessible documents (includes manual uploads and associated regulations)
        const userDocsResponse = await documentService.listDocuments(); // Use the service function
        // Assuming listDocuments returns the combined list as DisplayDocument[]
        const allDocs: DisplayDocument[] = userDocsResponse.map(doc => ({ // Ensure mapping matches DisplayDocument
            id: doc.id,
            filename: doc.filename,
            type: doc.uploaded_by ? 'user' : 'standard', // Example: Determine type based on if it was uploaded by a user
            filepath: doc.filepath,
            uploaded_at: doc.uploaded_at,
        })); 
        
        // Update state with combined documents
        setUserDocuments(allDocs); 
        setPdfs(allDocs.filter(doc => doc.type === 'standard')); // Keep pdfs state for potential filtering later if needed
        
        // No longer need to set allDocumentIds or default selectedPDFs
        // const userDocIds = userDocs.map(doc => doc.id);
        // const allIds = [...standardPdfIds, ...userDocIds];
        // const uniqueValidIds = Array.from(new Set(allIds))
        //   .filter(id => id !== undefined && id !== null && !isNaN(id));
        // setAllDocumentIds(uniqueValidIds);
        // if (!initialQueryId) {
        //      setSelectedPDFs(uniqueValidIds);
        // }
        
      } catch (err) {
        setError('Failed to load documents. Please try again later.');
      } finally {
        setIsLoading(false);
      }
    };
    
    loadDocuments();
  }, []);
  
  // Combine and sort documents for display, explicitly typing the result
  const combinedDocuments: DisplayDocument[] = userDocuments // Now source from userDocuments state
  // Add filtering to remove duplicates based on filename (optional, listDocuments might handle this)
  .filter((doc, index, self) => 
    index === self.findIndex((d) => d.filename === doc.filename)
  )
  .sort((a, b) => {
      if (a.type === 'standard' && b.type !== 'standard') return -1;
      if (a.type !== 'standard' && b.type === 'standard') return 1;
      return a.filename.localeCompare(b.filename);
  });

  // Update handler parameter type
  const handlePDFClick = (doc: DisplayDocument) => {
    const docId = doc.id.toString();
    
    // Always use the document service to open in a new tab, regardless of type
    import('../services/documentService').then(module => {
      const documentService = module.default;
      documentService.openDocumentInNewTab(docId);
    });
    
    // No longer setting selectedPDF state
  };
  
  const handleBackToList = () => {
    // This state is no longer used, but keep the function in case needed later
    setSelectedPDF(null);
  };

  // Load initial query data if needed
  useEffect(() => {
    if (initialQueryId) {
      // Don't log query details
      const fetchInitialQueryData = async () => {
        try {
          const response = await api.get(`/query/${initialQueryId}`);
          const data = response.data;
          
          // Set the initial state based on the query data
          if (data.query) {
            // setInitialQueryData({ id: initialQueryId, query_text: data.query, documentIds: data.documentIds || [] }); // REMOVED documentIds
            setInitialQueryData({ id: initialQueryId, query_text: data.query });
          }
          
          if (data.conversation_id) {
            // setConversationData({ conversationId: data.conversation_id, initialConversation: [], initialQuery: '', activePdfIds: data.documentIds || [] }); // REMOVED activePdfIds
            setConversationData({ conversationId: data.conversation_id, initialConversation: [], initialQuery: '' });
          }
          
          // if (data.documentIds && Array.isArray(data.documentIds)) { // REMOVED
          //   setSelectedPDFs(data.documentIds); // REMOVED
          // }
        } catch (error) {
          setError("Failed to load saved query");
        }
      };
      
      fetchInitialQueryData();
    }
  }, [initialQueryId]);

  useEffect(() => {
    // Load user documents
    const fetchDocuments = async () => {
      try {
        const response = await api.get('/documents/list');
        
        if (response.data && response.data.documents) {
          const documents = response.data.documents;
          setUserDocuments(documents);
        }
      } catch (error) {
        setError("Failed to load documents");
      }
    };
    
    fetchDocuments();
  }, []);

  // Prevent body scrolling
  useEffect(() => {
    // Save original body styles
    const originalOverflow = document.body.style.overflow;
    const originalHeight = document.body.style.height;
    
    // Apply fixed positioning
    document.body.style.overflow = 'hidden';
    document.body.style.height = '100vh';
    
    // Cleanup
    return () => {
      document.body.style.overflow = originalOverflow;
      document.body.style.height = originalHeight;
    };
  }, []);

  return (
    <div className="container mx-auto px-4 pt-4 pb-0 h-[calc(100vh-4rem)] flex flex-col overflow-hidden">
      <h1 className="text-3xl font-bold text-navy-blue dark:text-white mb-4 font-times transition-colors duration-300"></h1>
      
      {error && (
        <ErrorMessage 
          message={error}
          type="error"
          onClose={() => setError(null)}
        />
      )}
      
      {/* Use a persistent two-column layout */} 
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 flex-1 overflow-hidden">
        
        {/* --- Left Column (Document List / Viewer) --- */} 
        <div className="md:col-span-1 overflow-hidden flex flex-col">
          <div className="bg-white dark:bg-dark-surface p-6 rounded-lg shadow-md transition-colors duration-300 flex-1 flex flex-col overflow-hidden">
            {/* Always show the document list now */}
            <>
              <h2 className="text-xl font-bold text-navy-blue dark:text-white mb-4 transition-colors duration-300">Reference Documents</h2>
              {isLoading ? (
                <div className="text-center py-8 flex-1 flex flex-col justify-center items-center">
                  <div className="animate-spin h-8 w-8 border-4 border-navy-blue dark:border-blue-400 border-t-transparent rounded-full mx-auto mb-4 transition-colors duration-300"></div>
                  <p className="text-gray-600 dark:text-gray-300 transition-colors duration-300">Loading documents...</p>
                </div>
              ) : combinedDocuments.length === 0 ? (
                <div className="text-center py-8 border border-dashed border-gray-300 dark:border-gray-600 rounded-lg transition-colors duration-300 flex-1 flex flex-col justify-center items-center">
                  <FileText className="h-12 w-12 mx-auto text-gray-400 dark:text-gray-500 mb-3 transition-colors duration-300" />
                  <p className="text-gray-600 dark:text-gray-300 mb-2 transition-colors duration-300">No documents found</p>
                </div>
              ) : (
                <ul className="space-y-2 overflow-y-auto flex-1 pr-2 min-h-0">
                  {combinedDocuments.map((doc) => (
                    <li key={`${doc.type}-${doc.id}`} 
                        className={`flex items-center p-3 rounded-lg cursor-pointer transition-all duration-200 ease-in-out 
                                    hover:bg-blue-100 dark:hover:bg-dark-hover 
                                    ${selectedPDF?.id === doc.id ? 'bg-blue-200 dark:bg-blue-800' : ''}`}
                        onClick={() => handlePDFClick(doc)}
                    >
                      <FileText className={`h-5 w-5 mr-3 flex-shrink-0 ${doc.type === 'standard' ? 'text-blue-600 dark:text-blue-400' : 'text-green-600 dark:text-green-400'} transition-colors duration-300`} />
                      <span className="text-sm font-medium text-gray-800 dark:text-gray-200 truncate transition-colors duration-300" title={doc.filename}>{doc.filename}</span>
                    </li>
                  ))}
                </ul>
              )}
            </>
          </div>
        </div>
        
        {/* --- Right Column (AIChat) --- */} 
        <div className="md:col-span-2 overflow-hidden flex flex-col">
          <div className="h-full flex-1 overflow-hidden">
            <AIChat 
              key={chatKey}
              initialQuery={initialQueryData?.query_text || ''}
              operationType={currentOperationType} 
              initialConversation={conversationData?.initialConversation}
              initialConversationIdProp={conversationData?.conversationId}
              navigateTo={navigate}
              className="h-full"
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default ComplianceChatPage; 