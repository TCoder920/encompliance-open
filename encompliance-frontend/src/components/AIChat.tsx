/*
  Description: AI-powered chat component for compliance assistance. Handles user queries, document context, and conversation management with streaming AI responses.
  Purpose: Provides an interactive chat interface for users to ask compliance questions, analyze documents, and receive real-time AI guidance.
*/
import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Send, Loader2, Cpu, Cloud, BrainCircuit, FileText, ArrowUpRight, ChevronDown, ChevronUp, FilePlus } from 'lucide-react';
import { getAIResponse, getStreamingAIResponse, AIConfig, getQueryUsage } from '../services/aiService';
import documentService from '../services/documentService';
import ErrorMessage from '../components/ErrorMessage';
import { useModel } from '../contexts/ModelContext';
import { useAuth } from '../contexts/AuthContext';
import { Tier, getTierFromSubscriptionStatus } from '../utils/tiers';
import AiModeSelection from './AiModeSelection';
import AiModeTooltip from './ui/AiModeTooltip';
import tooltipManager from '../utils/tooltipManager';
import api from '../services/api';
import { formatDateTime } from '../utils/dateUtils';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import createCitationRenderer from './CitationRenderer';
import { extractCitations, parseWebSearchResults, WebSearchResult } from '../utils/citationUtils';

interface Message {
  id: number;
  text: string;
  sender: 'user' | 'ai';
  timestamp: Date;
  isLoading?: boolean;
  isStreaming?: boolean;
  role?: 'user' | 'assistant'; // Add role for OpenAI API compatibility
  conversation_id?: number;
  isCollapsed?: boolean; // Add property to track collapse state
}

interface Document {
  id: number;
  filename: string;
  // Add other relevant fields if needed from documentService.listDocuments response
}

interface AIChatProps {
  operationType: string;
  initialConversationIdProp?: number;
  initialQuery?: string;
  initialConversation?: any; // Conversation history
  showFullConversation?: boolean;
  navigateTo: (page: string, params?: any) => void; // Add navigateTo prop
  className?: string; // Add optional className prop
}

// Define the interface for a token animation
interface TokenAnimationState {
  messageId: number;
  text: string;
  isComplete: boolean;
}

// Token Fade Typer Component
const TokenFadeTyper: React.FC<{
  text: string;
  isStreaming: boolean;
  components: any;
}> = ({ text, isStreaming, components }) => {
  const [animationComplete, setAnimationComplete] = useState(false);
  const previousTextRef = useRef("");
  const wrapperRef = useRef<HTMLDivElement>(null);
  
  // Process text to properly handle incomplete markdown
  const processMarkdown = (text: string): string => {
    let processedText = text;
    
    // Handle incomplete markdown syntax
    const backtickCount = (processedText.match(/`/g) || []).length;
    if (backtickCount % 2 !== 0) processedText += '`';
    
    const asteriskCount = (processedText.match(/\*/g) || []).length;
    if (asteriskCount % 2 !== 0) processedText += '*';
    
    if ((processedText.match(/\[/g) || []).length > (processedText.match(/\]/g) || []).length) 
      processedText += ']';
    
    if ((processedText.match(/\(/g) || []).length > (processedText.match(/\)/g) || []).length)
      processedText += ')';
    
    return processedText;
  };
  
  // Add fade-in animations when text changes
  useEffect(() => {
    // Handle complete streaming
    if (isStreaming && text === previousTextRef.current && text.length > 0) {
      setTimeout(() => setAnimationComplete(true), 300);
    }
    
    if (!isStreaming) {
      setAnimationComplete(true);
      previousTextRef.current = text;
      return;
    }
    
    // If this is new text content
    if (text !== previousTextRef.current) {
      // Update our reference for next comparison
      previousTextRef.current = text;
    }
  }, [text, isStreaming]);
  
  // No text, render nothing
  if (!text) return null;
  
  // Process markdown syntax for rendering
  const processedText = processMarkdown(text);
  
  return (
    <div className="streaming-text markdown-content" ref={wrapperRef}>
      <style>{`
        /* Base text styles */
        .streaming-text {
          transition: color 0.15s ease;
        }
        
        /* Apply fade-in effect to entire component */
        .streaming-text {
          animation: fadeIn 0.3s ease-out;
        }
        
        @keyframes fadeIn {
          from { opacity: 0.5; }
          to { opacity: 1; }
        }
        
        /* Fix Markdown paragraph display */
        .streaming-text > div > p:last-of-type {
          display: inline;
          margin-bottom: 0;
        }
      `}</style>
      
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={components}
      >
        {processedText}
      </ReactMarkdown>
    </div>
  );
};

const AIChat: React.FC<AIChatProps> = ({ 
  operationType, 
  initialConversationIdProp,
  initialQuery = '',
  initialConversation = null,
  showFullConversation = false,
  navigateTo,
  className = ''
}) => {
  const { selectedModel, modelSettings } = useModel();
  const { user } = useAuth();
  const [messages, setMessages] = useState<Message[]>([]);
  const [currentTokenCount, setCurrentTokenCount] = useState<number>(0);
  const MAX_TOKENS = 1000000; // 1 million tokens context window
  const [collapsedMessageIds, setCollapsedMessageIds] = useState<Set<number>>(new Set());
  const [collapseThreshold, setCollapseThreshold] = useState<{chars: number, tokens: number}>({
    chars: 1753,
    tokens: 440
  });
  
  const [inputValue, setInputValue] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useAutoResizeTextarea(inputValue);
  const abortControllerRef = useRef<(() => void) | null>(null);
  const [currentConversationId, setCurrentConversationId] = useState<number | null>(initialConversationIdProp || null);
  const [useTypingEffect, setUseTypingEffect] = useState(true);
  const typingTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const typewriterQueueRef = useRef<{text: string, messageId: number} | null>(null);
  const isTypingRef = useRef(false);
  const abortStreamingRef = useRef<(() => void) | null>(null);
  const [cursorPosition, setCursorPosition] = useState({ x: 0, y: 0 });
  const [showCursorCloud, setShowCursorCloud] = useState(false);
  const [userDocuments, setUserDocuments] = useState<Document[]>([]);
  const [queryUsage, setQueryUsage] = useState<{ 
    used: number; 
    limit: number; 
    subscription_status: string;
    reset_time?: string;
  } | null>(null);
  
  // AI Mode Tooltip state
  const [showAiModeTooltip, setShowAiModeTooltip] = useState(false);
  const aiModeButtonRef = useRef<HTMLButtonElement>(null);
  
  const currentAiMessageIdRef = useRef<number | null>(null);

  // Add context window management
  const MAX_TOKENS_PER_MESSAGE = 4096;

  const userTier = getTierFromSubscriptionStatus(user?.subscription_status);
  const shouldShowTooltipForUser = userTier === Tier.PRO || userTier === Tier.ENTERPRISE;

  // Check if AI mode tooltip should be shown
  useEffect(() => {
    if (shouldShowTooltipForUser && messages.length === 0) {
      // Show tooltip only on empty chat for Pro/Enterprise users
      const shouldShow = tooltipManager.shouldShowTooltip('ai_mode_selection');
      if (shouldShow) {
        // Delay showing tooltip to ensure component is mounted
        const timer = setTimeout(() => {
          setShowAiModeTooltip(true);
          tooltipManager.markTooltipShown('ai_mode_selection');
        }, 2000); // Show after 2 seconds
        
        return () => clearTimeout(timer);
      }
    }
  }, [shouldShowTooltipForUser, messages.length]);

  const handleDismissTooltip = () => {
    setShowAiModeTooltip(false);
    tooltipManager.dismissTooltip('ai_mode_selection');
  };

  const formatMessageForAPI = (message: Message) => ({
    role: message.sender === 'user' ? 'user' : 'assistant',
    content: message.text,
    conversation_id: currentConversationId
  });

  // Cache conversation ID to localStorage to ensure persistency
  const saveConversationToCache = useCallback((convoId: number) => {
    // Remove localStorage caching to limit conversations to current session only
    // Conversations will no longer persist across page reloads
  }, []);
  
  // Load conversation ID from cache if available
  const loadConversationFromCache = useCallback((): number | undefined => {
    // No longer load from cache - always return undefined to force new conversation
    return undefined;
  }, []);

  useEffect(() => {
    // Generate a new conversation ID if none exists or load from props
    if (!currentConversationId) {
      // First try to get from props
      if (initialConversationIdProp) {
        setCurrentConversationId(initialConversationIdProp);
      } else {
        // Always generate a new conversation ID for a new session
        const newId = Date.now();
        setCurrentConversationId(newId);
      }
    }
  }, [initialConversationIdProp]);

  useEffect(() => {
    const fetchDocs = async () => {
      if (user) {
        try {
          const docs = await documentService.listDocuments();
          setUserDocuments(docs);
          // console.log("AIChat: Fetched user documents:", docs); // Removed for security/cleanliness
        } catch (err) {
          console.error("AIChat: Error fetching user documents:", err);
          setError("Could not load user documents for context.");
        }
      }
    };
    fetchDocs();
  }, [user]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  
  useEffect(() => {
    scrollToBottom();
  }, [messages]);
  
  useEffect(() => {
    return () => {
      if (abortStreamingRef.current) {
        abortStreamingRef.current();
        abortStreamingRef.current = null;
      }
    };
  }, []);
  
  useEffect(() => {
    const loadConversation = async () => {
      if (!initialConversationIdProp) return;
      
      // Important: Override any cached conversation ID with the one from props
      setCurrentConversationId(initialConversationIdProp);
      
      try {
        setIsProcessing(true);
        setError(null);
        
        if (initialConversation && Array.isArray(initialConversation) && initialConversation.length > 0) {
          const mappedMessages = initialConversation
            .map((msg: any, index: number) => {
              if (!msg || !msg.content) return null;
              let timestamp;
              try {
                timestamp = msg.timestamp ? new Date(msg.timestamp) : new Date();
                if (isNaN(timestamp.getTime())) timestamp = new Date();
              } catch (error) { timestamp = new Date(); }
              
              return {
                id: msg.id || (Date.now() + index),
                text: msg.content,
                sender: msg.role === 'user' ? 'user' : 'ai',
                timestamp: timestamp,
                isLoading: false,
                isStreaming: false,
                role: msg.role === 'user' ? 'user' : 'assistant'
              } as Message;
            });
          
          const formattedMessages = mappedMessages.filter((msg): msg is Message => msg !== null);
          
          if (formattedMessages.length > 0) {
            setMessages(formattedMessages);
            setTimeout(scrollToBottom, 100);
            setIsProcessing(false);
            return;
          }
        }
        
        const response = await api.get(`/conversations/${initialConversationIdProp}`);
        
        if (response.status !== 200) {
          throw new Error(`Failed to load conversation: ${response.statusText}`);
        }
        
        const data = response.data;
        
        if (data && data.messages && Array.isArray(data.messages)) {
          const loadedMessages = data.messages.map((msg: any, index: number) => {
            let timestamp;
            try {
              timestamp = msg.timestamp ? new Date(msg.timestamp) : new Date();
              if (isNaN(timestamp.getTime())) timestamp = new Date();
            } catch (error) { timestamp = new Date(); }
            
            return {
              id: msg.id || (Date.now() + index),
              text: msg.content || '', 
              sender: msg.role === 'user' ? 'user' : 'ai',
              timestamp: timestamp,
              isLoading: false
            };
          });
          
          setMessages(loadedMessages);
          setTimeout(scrollToBottom, 100);
        }
      } catch (err) {
        console.error("Error loading conversation");
        if (!initialConversation || !Array.isArray(initialConversation) || initialConversation.length === 0) {
          setError('Failed to load the conversation history. Starting a new conversation instead.');
          setMessages([]);
        }
      } finally {
        setIsProcessing(false);
      }
    };
    
    loadConversation();
  }, [initialConversationIdProp, operationType, initialConversation]);

  useEffect(() => {
    if (!initialConversation && initialQuery && initialQuery.trim() !== '' && messages.length <= 1) {
      setInputValue(initialQuery);
    }
  }, [initialQuery, initialConversation, messages.length]);

  useEffect(() => {
    if (inputValue && initialQuery && inputValue === initialQuery && !showFullConversation) {
       if(messages.length <= 1) {
           handleSendMessage();
       }
    }
  }, [inputValue, initialQuery, showFullConversation, messages]);

  // Fetch query usage on component mount
  useEffect(() => {
    const fetchQueryUsage = async () => {
      if (user) {
        try {
          const usage = await getQueryUsage();
          setQueryUsage(usage);
        } catch (err) {
          console.error("Error fetching query usage:", err);
        }
      }
    };
    
    fetchQueryUsage();
  }, [user]);
  
  // Refresh query usage after sending a message
  const refreshQueryUsage = async () => {
    if (user && user.subscription_status !== "enterprise") {
      try {
        const usage = await getQueryUsage();
        setQueryUsage(usage);
      } catch (err) {
        console.error("Error refreshing query usage:", err);
      }
    }
  };

  // Define a debug function to help track conversation flow
  const debugConversationState = (stage: string, messageHistory: any[]) => {
    // Debug function is now empty to prevent logging
  };

  // Update the getRecentMessageHistory function to ensure we're handling context properly
  const getRecentMessageHistory = () => {
    if (messages.length === 0) {
      return [];
    }
    
    // Get all messages without limiting
    const recentMessages = messages;
    
    // Format messages for the API and ensure all messages have text content
    // This needs to match the backend's expected format - only role and content
    const formattedMessages = recentMessages
      .filter(msg => msg.text && msg.text.trim() !== '') // Filter out empty messages
      .map(msg => ({
        role: msg.sender === 'user' ? 'user' : 'assistant',
        content: msg.text,
      }));
    
    return formattedMessages;
  };

  // Modify the handleSendMessage function to ensure context is being sent consistently
  const handleSendMessage = async () => {
    const trimmedInput = inputValue.trim();
    if (!trimmedInput || isProcessing) return;

    setError(null);
    setIsProcessing(true);
    setInputValue('');

    // Create the user message
    const userMessage: Message = {
      id: Date.now(),
      text: trimmedInput,
      sender: 'user',
      timestamp: new Date(),
      role: 'user',
      conversation_id: currentConversationId || undefined
    };
    
    // Add the user's message to the conversation state
    setMessages(prev => [...prev, userMessage]);

    // Add placeholder for AI response
    const aiMessageId = Date.now() + 1;
    currentAiMessageIdRef.current = aiMessageId; 
    
    const aiLoadingMessage: Message = {
      id: aiMessageId,
      text: '',
      sender: 'ai',
      timestamp: new Date(),
      isLoading: true,
      isStreaming: false,
      role: 'assistant',
      conversation_id: currentConversationId || undefined
    };
    
    // Update messages state with the AI loading placeholder
    setMessages(prev => [...prev, aiLoadingMessage]);

    // IMPORTANT: Wait for messages state to update before getting message history
    // This ensures we capture the latest state for the API call
    setTimeout(() => {
      try {
        // Get updated conversation history AFTER adding the new user message
        // This ensures the user's message is included in context
        const messageHistory = getRecentMessageHistory();
        
        // Debug the conversation state
        debugConversationState('Before API call', messageHistory);
        
        const config: AIConfig = {
          selectedModel: selectedModel,
          settings: modelSettings,
          conversationContext: messageHistory // Pass the full conversation context
        };

        // Call the streaming service with direct token updates
        abortStreamingRef.current = getStreamingAIResponse(
          trimmedInput,
          operationType,
          messageHistory, // Use the updated message history
          config,
          (token) => {
            setMessages(prevMessages => 
              prevMessages.map(msg => 
                msg.id === aiMessageId 
                  ? { 
                      ...msg, 
                      text: msg.text + token, 
                      isLoading: false,
                      isStreaming: true
                    } 
                  : msg
              )
            );
          },
          (errorMsg) => {
            console.error("Streaming Error Callback:", errorMsg);
            
            // Process error message - check if it contains a reset time
            let formattedErrorMsg = errorMsg;
            if (errorMsg.includes("You have reached your daily limit")) {
              // Extract the reset time if present
              const resetTimeMatch = errorMsg.match(/assistant again at ([\d-]+T[\d:]+)/i);
              if (resetTimeMatch && resetTimeMatch[1]) {
                const resetTimeIso = resetTimeMatch[1];
                try {
                  // Format the date using the app's standard formatter
                  const resetDate = new Date(resetTimeIso);
                  const formattedDate = formatDateTime(resetDate);
                  
                  // Replace the ISO date with the formatted date
                  formattedErrorMsg = errorMsg.replace(/assistant again at [\d-]+T[\d:]+/i, 
                                                      `assistant again at ${formattedDate}`);
                  
                  // Remove "Assistant Error:" prefix if present
                  formattedErrorMsg = formattedErrorMsg.replace("Assistant Error: ", "");
                } catch (e) {
                  console.error("Error formatting reset date:", e);
                }
              }
              
              // Display the error in the chat bubble for limit errors, not in the notification
              setMessages(prevMessages => 
                prevMessages.map(msg => 
                  msg.id === aiMessageId 
                    ? { ...msg, text: formattedErrorMsg, isLoading: false, isStreaming: false } 
                    : msg
                )
              );
            } else if (
              errorMsg.includes("Incorrect API key") ||
              errorMsg.includes("invalid_api_key")
            ) {
              // Show a user-friendly API key error
              const apiKeyMsg = 'Please contact support, there was an error with the API key.';
              setError(apiKeyMsg);
              setMessages(prevMessages => 
                prevMessages.map(msg => 
                  msg.id === aiMessageId 
                    ? { ...msg, text: apiKeyMsg, isLoading: false, isStreaming: false } 
                    : msg
                )
              );
            } else {
              // For other errors, show a generic user-friendly message
              const userFriendlyMsg = 'Sorry, there was a problem processing your request. Please try again later or contact support.';
              setError(userFriendlyMsg);
              setMessages(prevMessages => 
                prevMessages.map(msg => 
                  msg.id === aiMessageId 
                    ? { ...msg, text: userFriendlyMsg, isLoading: false, isStreaming: false } 
                    : msg
                )
              );
            }
            
            currentAiMessageIdRef.current = null; // Clear message ID ref
            setIsProcessing(false);
          },
          () => {
            setMessages(prevMessages =>
              prevMessages.map(msg =>
                msg.id === aiMessageId
                  ? { ...msg, isLoading: false, isStreaming: false }
                  : msg
              )
            );
            
            const userMessage = messages.find(m => m.id === aiMessageId - 1);
            const aiMessage = messages.find(m => m.id === aiMessageId);
            if (userMessage && aiMessage) {
              saveChatHistory(userMessage.text, aiMessage.text);
            }
            
            if (user && user.subscription_status !== "enterprise") {
              refreshQueryUsage();
            }
            
            currentAiMessageIdRef.current = null;
            setIsProcessing(false);
          },
          (newId) => {
            setCurrentConversationId(newId);
            // No longer cache the conversation ID
          },
          currentConversationId
        );
      } catch (error) {
        console.error("Error in handleSendMessage:", error);
        setError("Failed to send message. Please try again.");
        setIsProcessing(false);
      }
    }, 0); // Use setTimeout with 0ms to ensure state update has completed
  };
  
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };
  
  const getActiveModelDisplayName = () => {
    if (selectedModel === 'basic') {
      return "Basic Mode";
    } else if (selectedModel === 'pro') {
      return "Pro Mode";
    } else {
      return 'Default Mode'; 
    }
  };
  
  const ModelIcon = selectedModel === 'local-model' ? Cpu : selectedModel === 'basic' ? null : Cloud;

  const getFormattedOperationType = (type: string): string => {
    if (!type) return 'Daycare';
    
    const opType = type.toLowerCase();
    if (opType === 'daycare') {
      return 'Daycare';
    } else if (opType === 'gro' || opType === 'rtc' || opType === 'gro/rtc') {
      return 'Residential';
    } else {
      return type;
    }
  };

  // Save chat history to backend
  const saveChatHistory = async (userMessageText: string, aiResponseText: string) => {
    if (!currentConversationId) {
      console.error("Cannot save chat history without a conversation ID.");
      return;
    }
    try {
      await api.post('/chat/history', {
        user_message: userMessageText,
        ai_response: aiResponseText,
        operation_type: operationType,
        conversation_id: currentConversationId,
      });
    } catch (error) {
      console.error('Failed to save chat history:', error);
      // Optionally notify the user or retry?
    }
  };

  const handleUpgradeClick = () => {
    // Navigate to subscription page
    window.location.href = '/userSettings?tab=subscription';
  };

  // Add the handleStopResponse function
  const handleStopResponse = () => {
    if (abortStreamingRef.current) {
      abortStreamingRef.current();
      abortStreamingRef.current = null;
    }
    
    // Mark the current message as complete
    if (currentAiMessageIdRef.current) {
      setMessages(prevMessages =>
        prevMessages.map(msg =>
          msg.id === currentAiMessageIdRef.current
            ? { ...msg, isLoading: false, isStreaming: false }
            : msg
        )
      );
      currentAiMessageIdRef.current = null;
    }
    
    setIsProcessing(false);
  };

  // Extract web search results from conversation messages
  const extractWebSearchResults = useCallback((): WebSearchResult[] => {
    const allResults: WebSearchResult[] = [];
    
    // Look through all AI messages for web search results
    messages.forEach(message => {
      if (message.sender === 'ai' && message.text) {
        // Look for the web search results pattern in the message
        // More flexible regex to handle different formatting
        const searchResultsMatch = message.text.match(/Web Search Results:\s*([\s\S]*?)(?=\n\n(?![0-9])|$)/);
        if (searchResultsMatch) {
          const searchResultsText = searchResultsMatch[1];
          const results = parseWebSearchResults(searchResultsText);
          if (results.length > 0) {
            allResults.push(...results);
          }
        }
      }
    });
    
    return allResults;
  }, [messages]);

  // Function to clean message text by removing the "Web Search Results:" section
  const cleanMessageText = (text: string): string => {
    // Remove the "Web Search Results:" section and everything after it
    const webSearchPattern = /\n\nWeb Search Results:\s*[\s\S]*$/;
    return text.replace(webSearchPattern, '').trim();
  };

  // Create the memoized renderer components instance
  const citationComponents = React.useMemo(() => {
    const webSearchResults = extractWebSearchResults();
    // Pass navigateTo, userDocuments, and webSearchResults
    return createCitationRenderer(navigateTo, userDocuments, webSearchResults);
  }, [navigateTo, userDocuments, extractWebSearchResults]); // Recreate if any dependencies change

  // Add a more accurate token counting function
  const countTokens = (text: string): number => {
    if (!text) return 0;
    
    // Improved token estimation for English text
    // Different models have different tokenization schemes, but this is a reasonable approximation
    
    // Count by characters (4 chars ≈ 1 token for English text in most models)
    const charTokens = Math.ceil(text.length / 4);
    
    // Count by words (1.3 tokens per word for English is a common estimate)
    const wordCount = text.trim().split(/\s+/).length;
    const wordTokens = Math.ceil(wordCount * 1.3);
    
    // Take the average of the two methods for a more balanced estimate
    return Math.ceil((charTokens + wordTokens) / 2);
  };

  // Update token count when messages change
  useEffect(() => {
    if (!messages || messages.length === 0) {
      setCurrentTokenCount(0);
      return;
    }
    
    // Calculate tokens for each message
    const messagesTotalTokens = messages.reduce((acc, msg) => {
      const tokenCount = countTokens(msg.text || '');
      return acc + tokenCount;
    }, 0);
    
    // Add estimates for overhead:
    // 1. System prompt (compliance instructions): ~1000 tokens
    // 2. Message formatting overhead: ~2 tokens per message
    // 3. Special instructions: ~200 tokens
    const systemPromptTokens = 1000;
    const messageFormatTokens = messages.length * 2;
    const specialInstructionsTokens = 200;
    
    const totalTokens = messagesTotalTokens + systemPromptTokens + messageFormatTokens + specialInstructionsTokens;
    
    // Update the state with the total token count
    setCurrentTokenCount(totalTokens);
    
    // Log token usage when approaching limits
    const percentUsed = (totalTokens / MAX_TOKENS) * 100;
    if (percentUsed > 80) {
      setError("Context window for this chat is almost full. Start a new chat session soon.");
    } else if (error && error.includes("Context window")) {
      // Clear the context window warning if it exists and we're now below the threshold
      setError(null);
    }
  }, [messages]);

  // Add a function to display token usage in a more user-friendly way
  const getTokenUsageDisplay = () => {
    const percentUsed = (currentTokenCount / MAX_TOKENS) * 100;
    let statusColor = 'bg-navy-blue dark:bg-blue-400';
    
    if (percentUsed > 90) {
      statusColor = 'bg-red-500';
    } else if (percentUsed > 70) {
      statusColor = 'bg-orange-500';
    }
    
    return {
      statusColor,
      percentUsed
    };
  };

  // Update collapse threshold based on screen size
  useEffect(() => {
    const updateCollapseThreshold = () => {
      const width = window.innerWidth;
      
      // Responsive breakpoints for different screen sizes
      if (width < 640) { // Small mobile
        setCollapseThreshold({ chars: 800, tokens: 200 });
      } else if (width < 768) { // Large mobile
        setCollapseThreshold({ chars: 1000, tokens: 250 });
      } else if (width < 1024) { // Tablet
        setCollapseThreshold({ chars: 1200, tokens: 300 });
      } else if (width < 1280) { // Small laptop
        setCollapseThreshold({ chars: 1500, tokens: 375 });
      } else if (width < 1536) { // 16" laptop
        setCollapseThreshold({ chars: 1753, tokens: 440 });
      } else if (width < 1920) { // Large screen
        setCollapseThreshold({ chars: 2200, tokens: 550 });
      } else { // Ultra wide
        setCollapseThreshold({ chars: 2800, tokens: 700 });
      }
    };
    
    // Set initial threshold
    updateCollapseThreshold();
    
    // Update on resize
    window.addEventListener('resize', updateCollapseThreshold);
    
    // Cleanup
    return () => {
      window.removeEventListener('resize', updateCollapseThreshold);
    };
  }, []);

  // Reset conversation when component unmounts to ensure session-only chat
  useEffect(() => {
    return () => {
      // Clean up any streaming responses
      if (abortStreamingRef.current) {
        abortStreamingRef.current();
        abortStreamingRef.current = null;
      }
      
      // The next time the component mounts, it will start a new conversation
      // since we're not saving to localStorage anymore
    };
  }, []);

  // Determine if a message should be collapsible based on dynamic thresholds
  const isMessageCollapsible = (message: Message): boolean => {
    if (message.sender !== 'ai') return false;
    
    // Messages with code blocks are always collapsible
    const containsCodeBlock = message.text.includes('```');
    if (containsCodeBlock) return true;
    
    // Check character length against dynamic threshold
    return message.text.length > collapseThreshold.chars;
  };

  // Toggle message collapse state
  const toggleMessageCollapse = (messageId: number) => {
    setCollapsedMessageIds(prevCollapsed => {
      const newCollapsed = new Set(prevCollapsed);
      if (newCollapsed.has(messageId)) {
        newCollapsed.delete(messageId);
      } else {
        newCollapsed.add(messageId);
      }
      return newCollapsed;
    });
  };

  return (
    <div className={`flex flex-col h-full bg-white dark:bg-gray-900 shadow-md rounded-lg overflow-hidden ${className}`}>
      <div className="p-4 border-b dark:border-gray-700 flex justify-between items-center bg-gray-50 dark:bg-gray-800">
        <h2 className="text-lg font-semibold text-navy-blue dark:text-white">
          AI Assistant - {getFormattedOperationType(operationType)}
        </h2>
        <div className="flex items-center space-x-4">
          <button
            onClick={() => {
              navigateTo('/search');
            }}
            className="p-2 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
            aria-label="New Chat"
            title="Start a new chat"
          >
            <FilePlus size={20} className="text-gray-600 dark:text-gray-400" />
          </button>
          <AiModeSelection ref={aiModeButtonRef} />
          <div className="h-6 w-px bg-gray-300 dark:bg-gray-600 mx-2"></div>
          <div className="flex flex-col items-end">
            <div className="relative group">
              <span className="text-sm text-gray-600 dark:text-gray-400 mb-1">Context Window</span>
              <div className="absolute top-full left-0 right-0 bg-gray-800 text-white text-xs p-2 rounded-md opacity-0 group-hover:opacity-100 transition-opacity duration-200 z-10 mt-1">
                Shows how much of the AI's memory capacity is being used in this conversation. As this fills up, the AI may forget earlier parts of the conversation.
              </div>
            </div>
            <div className="w-24 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
              <div 
                className={`h-full ${getTokenUsageDisplay().statusColor}`}
                style={{ width: `${Math.min(getTokenUsageDisplay().percentUsed, 100)}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      {messages.length === 0 && (
        <div className="flex-1 flex flex-col items-center justify-center p-8 bg-gradient-to-b from-gray-50 to-white dark:from-gray-800 dark:to-gray-900 overflow-y-auto">
          <div className="text-center max-w-md">
            <div className="mb-4">
              <BrainCircuit className="h-12 w-12 mx-auto text-navy-blue dark:text-blue-400 animate-pulse rotate-90" />
            </div>
            <h3 className="text-xl font-semibold text-navy-blue dark:text-white mb-2">
              Greetings {user?.full_name || 'there'}, I am your AI Compliance Assistant. How can I help you today?
            </h3>
          </div>
        </div>
      )}

      <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin scrollbar-thumb-gray-300 dark:scrollbar-thumb-gray-600 scrollbar-track-gray-100 dark:scrollbar-track-gray-800">
        {messages.map((message) => (
          <div key={message.id} data-message-id={`${message.sender}-${message.id}`} className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`min-w-0 max-w-xl lg:max-w-2xl px-4 py-2 rounded-lg shadow ${message.sender === 'user' ? 'bg-blue-500 text-white' : 'bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-white'}`}>
              {message.isLoading && !message.text && message.sender === 'ai' ? (
                <div className="flex items-center space-x-2" data-testid="loading-brain">
                  <BrainCircuit className="animate-pulse h-5 w-5 text-gray-400 rotate-90" />
                  <span className="text-gray-500 dark:text-gray-400">Processing...</span>
                </div>
              ) : (
                <div className="break-words message-content">
                  <div className={collapsedMessageIds.has(message.id) ? "max-h-32 overflow-hidden relative" : ""}>
                    {message.sender === 'ai' ? (
                      <TokenFadeTyper 
                        text={cleanMessageText(message.text)} 
                        isStreaming={!!message.isStreaming}
                        components={citationComponents} 
                      />
                    ) : (
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={citationComponents}
                      >
                        {message.text}
                      </ReactMarkdown>
                    )}
                    
                    {collapsedMessageIds.has(message.id) && (
                      <div className="absolute bottom-0 inset-x-0 h-12 bg-gradient-to-t from-gray-200 dark:from-gray-700 to-transparent pointer-events-none" />
                    )}
                  </div>
                  
                  {message.sender === 'ai' && message.isStreaming && (
                     <span className="inline-block ml-1 align-bottom">
                       <BrainCircuit className="animate-pulse h-4 w-4 text-gray-400 inline-block rotate-90" />
                     </span>
                   )}
                </div>
              )}
              
              <div className="flex justify-between items-center mt-1 text-xs">
                {isMessageCollapsible(message) && message.sender === 'ai' && !message.isLoading ? (
                  <div 
                    className="cursor-pointer text-gray-500 dark:text-gray-400 flex items-center"
                    onClick={() => toggleMessageCollapse(message.id)}
                  >
                    {collapsedMessageIds.has(message.id) ? (
                      <>
                        <ChevronDown className="h-3 w-3 mr-1" />
                        <span>Show full message</span>
                      </>
                    ) : (
                      <>
                        <ChevronUp className="h-3 w-3 mr-1" />
                        <span>Collapse message</span>
                      </>
                    )}
                  </div>
                ) : (
                  <div></div> // Empty div to maintain flex layout when no collapse button
                )}
                
                <div className={`${message.sender === 'user' ? 'text-blue-200' : 'text-gray-500 dark:text-gray-400'}`}>
                  {formatDateTime(message.timestamp)}
                </div>
              </div>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {error && <ErrorMessage message={error} onClose={() => setError(null)} />}

      <div className="p-4 border-t dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
        <div className="relative flex items-center">
          <textarea
            ref={textareaRef}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask anything about compliance..."
            className="flex-1 p-2 pr-10 border rounded-md shadow-sm focus:ring-navy-blue focus:border-navy-blue resize-none dark:bg-gray-700 dark:border-gray-600 dark:text-white scrollbar-thin scrollbar-thumb-gray-400 dark:scrollbar-thumb-gray-600"
            rows={1}
            style={{ maxHeight: '150px' }}
            disabled={isProcessing}
          />
          <button
            onClick={handleSendMessage}
            disabled={isProcessing || !inputValue.trim()}
            className="absolute right-2 top-1/2 transform -translate-y-1/2 p-2 text-navy-blue dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 disabled:text-gray-400 dark:disabled:text-gray-500 transition-colors"
            aria-label="Send message"
          >
            {isProcessing ? <Loader2 className="animate-spin h-5 w-5" /> : <Send size={20} />}
          </button>
        </div>
        {isProcessing && (
          <button 
            onClick={handleStopResponse}
            className="mt-2 text-xs text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-300"
          >
            Stop Response
          </button>
        )}
      </div>

      {user && user.subscription_status !== "enterprise" && queryUsage && (
        <div className="px-4 py-2 text-xs text-gray-600 dark:text-gray-300 border-t border-gray-200 dark:border-gray-700 transition-colors duration-300">
          <div className="flex justify-between items-center">
            <span>
              Daily AI Queries: <span className="font-medium">{queryUsage.used} / {queryUsage.limit}</span>
              {queryUsage.reset_time && (
                <span className="ml-2 text-gray-500">
                  (Resets at {formatDateTime(new Date(queryUsage.reset_time))})
                </span>
              )}
            </span>
            <span className="capitalize">
              {queryUsage.subscription_status === "pro" ? "Pro" : "Free"} Plan
            </span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1 mt-1 overflow-hidden">
            <div 
              className={`h-full rounded-full ${
                queryUsage.used >= queryUsage.limit 
                  ? 'bg-red-500' 
                  : queryUsage.used > queryUsage.limit * 0.8 
                    ? 'bg-orange-500' 
                    : 'bg-green-500'
              }`} 
              style={{ width: `${Math.min((queryUsage.used / queryUsage.limit) * 100, 100)}%` }}
            />
          </div>
          
          {queryUsage.used >= queryUsage.limit && queryUsage.subscription_status === "free" && (
            <div className="mt-2 flex justify-end">
              <button
                onClick={handleUpgradeClick}
                className="flex items-center text-xs bg-blue-500 hover:bg-blue-600 text-white py-1 px-2 rounded transition-colors duration-200"
              >
                Upgrade Subscription <ArrowUpRight className="ml-1 h-3 w-3" />
              </button>
            </div>
          )}
        </div>
      )}

      {/* AI Mode Tooltip */}
      <AiModeTooltip
        isVisible={showAiModeTooltip}
        onDismiss={handleDismissTooltip}
        targetRef={aiModeButtonRef}
      />
    </div>
  );
};

const useAutoResizeTextarea = (value: string) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${textarea.scrollHeight}px`;
    }
  }, [value]);

  return textareaRef;
};

export default AIChat;