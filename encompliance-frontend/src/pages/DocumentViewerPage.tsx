/*
  Description: Document viewer page component. Allows users to view, annotate, and interact with uploaded compliance documents.
  Purpose: Provides a user interface for document navigation, annotation, and compliance insights.
*/
import React, { useState, useEffect, useCallback } from 'react';
import { Search, ZoomIn, ZoomOut, ChevronLeft, ChevronRight, MessageSquare, X, Upload, Settings } from 'lucide-react';
import AIChat from '../components/AIChat';
import DocumentUploader from '../components/DocumentUploader';
import ErrorMessage from '../components/ErrorMessage';
import { useModel } from '../contexts/ModelContext';
import { useAuth } from '../contexts/AuthContext';
import documentService from '../services/documentService';
import InlineDocumentViewer from '../components/InlineDocumentViewer';

interface DocumentViewerPageProps {
  documentId?: string;
  navigateTo: (page: string) => void;
  operationType?: string;
  isMinimumStandards?: boolean;
  location?: {
    search?: string;
  };
}

const DocumentViewerPage: React.FC<DocumentViewerPageProps> = ({ 
  operationType = 'daycare', 
  navigateTo, 
  documentId: propDocumentId,
  isMinimumStandards = false,
  location
}) => {
  const [currentPage, setCurrentPage] = useState(1);
  const [zoomLevel, setZoomLevel] = useState(100);
  const [searchQuery, setSearchQuery] = useState('');
  const [isChatOpen, setIsChatOpen] = useState(true); // Set to true by default
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [showAISettings, setShowAISettings] = useState(false);
  const [activePdfIds, setActivePdfIds] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [userDocuments, setUserDocuments] = useState<any[]>([]);
  const [documentTitle, setDocumentTitle] = useState('Document Viewer');
  const { selectedModel } = useModel();
  const { user } = useAuth();
  
  // Parse query parameters from location or URL
  const getQueryParams = () => {
    try {
      // Get query string either from props or window location
      const queryString = location?.search || window.location.search;
      const urlParams = new URLSearchParams(queryString);
      const type = urlParams.get('type');
      const id = urlParams.get('id');
      
      console.log(`Parsed query params - type: ${type}, id: ${id}`);
      
      return {
        type,
        id
      };
    } catch (err) {
      console.error('Error parsing URL query params:', err);
      return { type: null, id: null };
    }
  };
  
  // Load PDF when component mounts
  useEffect(() => {
    const preparePdf = async () => {
      try {
        setIsLoading(true);
        setError(null); // Clear any previous errors
        
        console.log('DocumentViewerPage: Starting PDF preparation');
        // First check if the URL path contains a document ID (for direct navigation)
        const urlPath = window.location.pathname;
        const directDocMatch = urlPath.match(/\/document\/(\w+)/);
        
        // Determine which document to show based on direct navigation, props, or defaults
        if (directDocMatch) {
          const directDocId = directDocMatch[1];
          console.log(`Found direct document navigation: ${directDocId}`);
          
          // General case - try to render the specified document
          try {
            console.log(`Loading document with ID: ${directDocId}`);
            const documentUrl = documentService.getEmbeddableDocumentUrl(directDocId);
            console.log(`Generated document URL: ${documentUrl}`);
            setPdfUrl(documentUrl);
            
            // Try to get document details for the title
            try {
              const documents = await documentService.listDocuments();
              const doc = documents.find(d => d.id.toString() === directDocId);
              if (doc) {
                console.log(`Found document details:`, doc);
                setDocumentTitle(doc.filename);
              } else {
                console.warn(`Could not find document with ID ${directDocId} in document list`);
                setDocumentTitle(`Document #${directDocId}`);
              }
            } catch (err) {
              console.error('Error getting document details:', err);
              setDocumentTitle(`Document #${directDocId}`);
            }
            
            // Set this as the active PDF for AI chat
            setActivePdfIds([directDocId]);
          } catch (err) {
            console.error(`Error loading document ${directDocId}:`, err);
            setError(`Failed to load document #${directDocId}. Please check if the document exists and try again.`);
          }
        } else if (propDocumentId) {
          // Viewing specific document by prop
          console.log(`Loading document with prop ID: ${propDocumentId}`);
          const documentUrl = documentService.getEmbeddableDocumentUrl(propDocumentId);
          console.log(`Generated document URL: ${documentUrl}`);
          setPdfUrl(documentUrl);
          
          // Try to get document details for the title
          try {
            const documents = await documentService.listDocuments();
            const doc = documents.find(d => d.id.toString() === propDocumentId);
            if (doc) {
              console.log(`Found document details:`, doc);
              setDocumentTitle(doc.filename);
            } else {
              console.warn(`Could not find document with ID ${propDocumentId} in document list`);
              setDocumentTitle(`Document #${propDocumentId}`);
            }
          } catch (err) {
            console.error('Error getting document details:', err);
            setDocumentTitle(`Document #${propDocumentId}`);
          }
          
          // Set this as the active PDF for AI chat
          setActivePdfIds([propDocumentId]);
        } else {
          // No document specified, show error or placeholder
          console.log('No document specified');
          setError('No document specified. Please select a document to view.');
        }
      } catch (err) {
        console.error('Error preparing PDF:', err);
        setError('Failed to load document. Please try again.');
      } finally {
        setIsLoading(false);
      }
    };
    
    preparePdf();
  }, [propDocumentId, window.location.pathname]);
  
  const totalPages = 150; // Placeholder value
  
  const handleZoomIn = () => {
    if (zoomLevel < 200) {
      setZoomLevel(zoomLevel + 10);
    }
  };
  
  const handleZoomOut = () => {
    if (zoomLevel > 50) {
      setZoomLevel(zoomLevel - 10);
    }
  };
  
  const handleSearch = () => {
    if (!searchQuery.trim()) {
      setError('Please enter a search term');
      return;
    }
    
    setError(null);
    // In a real application, this would trigger a search request
    console.log('Searching for:', searchQuery);
  };
  
  const toggleUploadModal = () => {
    setIsUploadModalOpen(!isUploadModalOpen);
  };

  const handleUploadComplete = (file: File) => {
    try {
      setUploadedFile(file);
      setError(null);
      // In a real application, you would process the file here
    } catch (err) {
      console.error('Upload error:', err);
      setError('Failed to process the uploaded file. Please try again.');
    }
  };
  
  // Handle PDF loading error
  const handlePdfError = () => {
    console.error(`Failed to load PDF at: ${pdfUrl}`);
    
    // If we're already showing an error or we can't generate a URL, show an error
    if (error || !pdfUrl) {
      setError(`Failed to load ${documentTitle}. Please check if the document exists and try again.`);
      return;
    }
    
    // Show error for any document
    setError(`Failed to load document. Please try again.`);
  };
  
  // Reload the current document (used by the Try Again button)
  const reloadDocument = () => {
    setError(null);
    setIsLoading(true);
    
    // Check if this is a direct document navigation
    const urlPath = window.location.pathname;
    const directDocMatch = urlPath.match(/\/document\/(\w+)/);
    
    console.log(`Reloading document from path: ${urlPath}`);
    
    // Clear the URL to force a reload
    setPdfUrl(null);
    
    // Set a timeout to reapply the URL to trigger a reload
    setTimeout(() => {
      if (directDocMatch) {
        const directDocId = directDocMatch[1];
        console.log(`Regenerating URL for document (direct): ${directDocId}`);
        setPdfUrl(documentService.getEmbeddableDocumentUrl(directDocId));
      } else if (propDocumentId) {
        console.log(`Regenerating URL for document (prop): ${propDocumentId}`);
        setPdfUrl(documentService.getEmbeddableDocumentUrl(propDocumentId));
      } else {
        console.log(`No document context found, showing error`);
        setError('No document specified. Please select a document to view.');
      }
      setIsLoading(false);
    }, 500);
  };
  
  const regenerateAuthenticatedUrls = useCallback(() => {
    try {
      console.log('Regenerating authenticated URLs');
      // Check if this is direct navigation or prop-based
      const urlPath = window.location.pathname;
      const directDocMatch = urlPath.match(/\/document\/(\w+)/);
      
      if (directDocMatch) {
        const directDocId = directDocMatch[1];
        console.log(`Regenerating URL for document (direct): ${directDocId}`);
        setPdfUrl(documentService.getEmbeddableDocumentUrl(directDocId));
      } else if (propDocumentId) {
        console.log(`Regenerating URL for document (prop): ${propDocumentId}`);
        setPdfUrl(documentService.getEmbeddableDocumentUrl(propDocumentId));
      }
    } catch (err) {
      console.error('Error regenerating URLs:', err);
    }
  }, [propDocumentId]);
  
  // Show loading state
  if (isLoading) {
    return (
      <div className="flex flex-col h-screen justify-center items-center">
        <div className="animate-pulse text-navy-blue text-xl">Loading document...</div>
      </div>
    );
  }
  
  return (
    <div className="container mx-auto px-4 py-6">
      <div className="flex flex-col">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold text-navy-blue">{documentTitle}</h1>
          <div className="flex space-x-2">
            <button 
              onClick={handleZoomOut}
              className="bg-gray-200 hover:bg-gray-300 p-2 rounded"
              aria-label="Zoom out"
            >
              <ZoomOut className="h-5 w-5 text-gray-700" />
            </button>
            <div className="bg-gray-100 px-3 py-2 rounded text-sm">
              {zoomLevel}%
            </div>
            <button 
              onClick={handleZoomIn}
              className="bg-gray-200 hover:bg-gray-300 p-2 rounded"
              aria-label="Zoom in"
            >
              <ZoomIn className="h-5 w-5 text-gray-700" />
            </button>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-1">
          {isLoading ? (
            <div className="flex justify-center items-center h-[600px]">
              <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
            </div>
          ) : error ? (
            <div className="text-center p-10">
              <div className="text-red-500 mb-4">{error}</div>
              <button 
                onClick={reloadDocument}
                className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
              >
                Try Again
              </button>
            </div>
          ) : pdfUrl ? (
            <InlineDocumentViewer
              documentUrl={pdfUrl}
              title={documentTitle}
              className="h-[600px] w-full"
              onError={handlePdfError}
            />
          ) : (
            <div className="text-center p-10">
              <div className="text-gray-500 mb-4">No document selected</div>
              <button 
                onClick={() => navigateTo('dashboard')}
                className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
              >
                Go to Dashboard
              </button>
            </div>
          )}
        </div>

        {/* AI Chat interface */}
        <div className={`fixed right-0 top-0 bottom-0 transform transition-transform ${isChatOpen ? 'translate-x-0' : 'translate-x-full'} bg-white shadow-lg z-10 w-96 flex flex-col`}>
          <div className="p-4 border-b border-gray-200 flex justify-between items-center">
            <h2 className="text-lg font-medium">AI Assistant</h2>
            <button 
              onClick={() => setIsChatOpen(false)}
              className="text-gray-500 hover:text-gray-700"
              aria-label="Close chat"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
          <div className="flex-1 overflow-auto">
            <AIChat 
              operationType={operationType}
              showFullConversation={true}
              navigateTo={navigateTo}
            />
          </div>
        </div>

        {/* Chat toggle button (visible when chat is hidden) */}
        {!isChatOpen && (
          <button
            onClick={() => setIsChatOpen(true)}
            className="fixed right-6 bottom-6 bg-navy-blue text-white p-3 rounded-full shadow-lg hover:bg-blue-800 z-10"
            aria-label="Open chat"
          >
            <MessageSquare className="h-6 w-6" />
          </button>
        )}
      </div>
    </div>
  );
};

export default DocumentViewerPage;