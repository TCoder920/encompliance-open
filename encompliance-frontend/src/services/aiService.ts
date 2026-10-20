/*
  Description: AI service for interacting with backend AI endpoints, including chat, streaming, and conversation management.
  Purpose: Provides functions for sending prompts, receiving responses, and managing AI-driven compliance conversations.
*/
import api from './api';
import { ModelSettings } from '../contexts/ModelContext';
import axios, { AxiosError } from 'axios';

export interface ChatMessage {
  role: string;
  content: string;
}

export interface AIConfig {
  selectedModel: string;
  settings: ModelSettings;
  conversationContext?: ChatMessage[];
}

// Track API call timestamps to implement rate limiting
// Using a Map instead of an object for better memory management
let lastApiCallTime: { [key: string]: number } = {};
let apiCallErrorCount: { [key: string]: number } = {};
const MIN_API_CALL_INTERVAL = 1000; // Reduced from 3000ms to 1000ms - minimum between calls to the same endpoint

// Function to reset API call tracking on navigation 
// (this helps prevent throttling issues when navigating between pages)
export const resetApiCallTracking = () => {
  lastApiCallTime = {};
  apiCallErrorCount = {};
};

/**
 * Get a response from the AI.
 */
export const getAIResponse = async (
  prompt: string,
  facilityType: string,
  messageHistory: any[] = [],
  config: AIConfig,
): Promise<string> => {
  try {
    // Include API key from localStorage if needed for cloud models
    const apiKey = localStorage.getItem('model_api_key') || '';
    
    const payload = {
      prompt,
      facility_type: facilityType,
      message_history: messageHistory,
      model: config.selectedModel,
      stream: true,
      api_key: apiKey,
      provider: config.settings.provider,
      otherApiUrl: config.settings.otherApiUrl,
      localModelUrl: config.settings.localModelUrl
    };
    
    const response = await api.post('/chat', payload);
    
    // Add improved error handling to catch potentially undefined responses
    if (!response.data) {
      console.error("API response missing data property");
      throw new Error('API response is missing data');
    }
    
    // Check for the response property (from backend) before returning
    if (response.data.response !== undefined) { 
      return response.data.response;
    } else if (response.data.text !== undefined) {
      return response.data.text;
    } else {
      console.error("API response missing response/text property:", response.data);
      throw new Error('API response is missing response/text field');
    }
  } catch (error) {
    console.error("Error in getAIResponse:", error);
    
    // Extract error message from response if available
    if (axios.isAxiosError(error) && error.response?.data?.error) {
      throw new Error(error.response.data.error);
    }
    
    throw new Error(error instanceof Error ? error.message : 'Failed to get AI response');
  }
};

/**
 * Get a streaming response from the AI.
 * Now includes a callback `onNewConversationId`.
 */
export const getStreamingAIResponse = (
  prompt: string,
  facilityType: string,
  messageHistory: any[] = [],
  config: AIConfig,
  onChunk: (chunk: string) => void,
  onError: (error: string) => void,
  onComplete: () => void,
  onNewConversationId: (newId: number) => void,
  conversationId?: number | null
): (() => void) => {
  const controller = new AbortController();
  
  (async () => {
    try {
      // Include API key from localStorage if needed for cloud models
      const apiKey = localStorage.getItem('model_api_key') || '';
      
      // Clean up message history to ensure backend compatibility
      // Only include role and content as required by the backend
      const cleanedMessageHistory = messageHistory.map(msg => ({
        role: msg.role,
        content: msg.content
      }));
      
      // Add conversation_id to the payload if provided
      const payload: any = {
        prompt,
        facility_type: facilityType,
        message_history: cleanedMessageHistory, // Use cleaned message history
        model: config.selectedModel,
        stream: true,
        api_key: apiKey,
        provider: config.settings.provider,
        otherApiUrl: config.settings.otherApiUrl,
        localModelUrl: config.settings.localModelUrl,
      };

      // Only include conversation_id if it has a value
      if (conversationId) {
        payload.conversation_id = conversationId;
      }
      
      const token = localStorage.getItem('token');
      if (!token) {
        onError('Authentication token missing. Please log in again.');
        return;
      }
      
      // Use API base URL from env or fallback to localhost
      const baseUrl = api.defaults.baseURL || 'http://localhost:8000/api/v1';
      
      try {
        const response = await fetch(`${baseUrl}/chat/stream`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
            'x-token': token 
          },
          body: JSON.stringify(payload),
          signal: controller.signal,
        });
        
        // --- Check for New Conversation ID Header --- 
        if (response.ok) { 
            const newConvIdHeader = response.headers.get('X-Conversation-Id');
            if (newConvIdHeader) {
                try {
                    const newId = parseInt(newConvIdHeader, 10);
                    if (!isNaN(newId)) {
                        onNewConversationId(newId); // Call the callback with the new ID
                    }
                } catch (e) {
                    console.error("Error parsing X-Conversation-Id header:", e);
                }
            }
        }
        
        if (!response.ok) {
          let errorMessage = '';
          try {
            // Try to parse JSON response first
            const errorResponse = await response.json();
            
            // Special handling for 422 errors to show validation details
            if (response.status === 422 && errorResponse.detail) {
              console.error("Validation error details:", errorResponse.detail);
              
              // If the detail is an array of validation errors (FastAPI format)
              if (Array.isArray(errorResponse.detail)) {
                const validationErrors = errorResponse.detail.map((error: any) => 
                  `${error.loc.join('.')}: ${error.msg}`
                ).join('; ');
                
                errorMessage = `Validation error: ${validationErrors}`;
              } else {
                errorMessage = `Validation error: ${errorResponse.detail}`;
              }
            } else {
              errorMessage = errorResponse.error || errorResponse.detail || `API error: ${response.status} ${response.statusText}`;
            }
            
            console.error("Error details:", errorResponse);
          } catch (parseError) {
            // If JSON parsing fails, try to get text
            console.error("Error parsing error response:", parseError);
            const errorText = await response.text().catch(() => '');
            errorMessage = `API error: ${response.status} ${response.statusText}${errorText ? ': ' + errorText : ''}`;
          }
          
          console.error("Streaming API Error:", response.status, response.statusText, errorMessage);
          onError(errorMessage);
          return;
        }
        
        if (!response.body) {
          onError('Response body is null');
          return;
        }
        
        // Create event source reader for server-sent events
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        
        while (true) {
          try {
            const { done, value } = await reader.read();
            
            if (done) {
              onComplete();
              break;
            }
            
            const text = decoder.decode(value, { stream: true });
            buffer += text;
            
            // Process complete events (each event ends with \n\n)
            const events = buffer.split('\n\n');
            buffer = events.pop() || ''; // Keep the last incomplete chunk in the buffer
            
            for (const event of events) {
              if (!event.trim()) continue; // Skip empty events
              
              // Parse SSE format - looking for lines starting with "data: "
              const dataMatch = event.match(/^data: (.+)$/m);
              if (dataMatch && dataMatch[1]) {
                try {
                  const jsonData = JSON.parse(dataMatch[1]);
                  
                  // Handle different types of data - immediately pass each token without accumulation
                  if (jsonData.content !== undefined) {
                    // Process each individual token/character 
                    // No batching, debouncing, or accumulation - pass directly to callback
                    onChunk(jsonData.content);
                  } else if (jsonData.error) {
                    // Error message
                    onError(jsonData.error);
                  }
                } catch (parseError) {
                  console.error("Error parsing SSE JSON data:", parseError, "Raw data:", dataMatch[1]);
                }
              }
            }
          } catch (error: any) {
            if (error.name === 'AbortError') {
              console.log("Streaming aborted by user.");
              break;
            }
            console.error("Error reading stream chunk:", error);
            onError('Error reading stream');
            break;
          }
        }
      } catch (fetchError: any) {
        console.error("Fetch error:", fetchError);
        onError(`Fetch error: ${fetchError.message}`);
      }
    } catch (error: any) {
      console.error("Error in getStreamingAIResponse setup:", error);
      onError(error instanceof Error ? error.message : 'Error in streaming request');
    }
  })().catch(error => {
    console.error("Uncaught error in streaming async function:", error);
    onError(error instanceof Error ? error.message : 'Error setting up streaming');
  });
  
  return () => {
    controller.abort();
  };
};

/**
 * Fetch a list of conversation summaries for the dashboard.
 */
export const getConversationSummaries = async (page: number = 1, limit: number = 10) => {
  const endpoint = 'query-logs';
  const currentTime = Date.now();
  
  // Use a much less aggressive throttling approach - only 500ms between calls
  const MIN_INTERVAL_BETWEEN_CALLS = 500; // Reduced from 5000ms to 500ms
  
  try {
    // Check if we've called this endpoint very recently (within last 500ms)
    if (lastApiCallTime[endpoint] && 
        currentTime - lastApiCallTime[endpoint] < MIN_INTERVAL_BETWEEN_CALLS) {
      console.log(`Mild throttling ${endpoint} API call - last call was ${currentTime - lastApiCallTime[endpoint]}ms ago`);
      
      // Instead of returning empty data, just wait a bit and then make the call anyway
      await new Promise(resolve => setTimeout(resolve, MIN_INTERVAL_BETWEEN_CALLS));
    }
    
    // Apply rate limiting only if we've seen errors
    if (apiCallErrorCount[endpoint] > 3 && 
        lastApiCallTime[endpoint] && 
        currentTime - lastApiCallTime[endpoint] < MIN_API_CALL_INTERVAL) {
      console.warn(`Rate limiting ${endpoint} API call after ${apiCallErrorCount[endpoint]} errors`);
      
      // Return empty result when rate limiting due to errors
      return { 
        conversations: [], 
        total: 0, 
        limit, 
        skip: (page - 1) * limit,
        throttled: true
      };
    }
    
    // Update the last call time
    lastApiCallTime[endpoint] = currentTime;
    
    const skip = (page - 1) * limit;
    const response = await api.get(`/query-logs?limit=${limit}&skip=${skip}`);
    
    // Reset error count on success
    apiCallErrorCount[endpoint] = 0;
    
    // The backend now returns { conversations: [], total: number, limit: number, skip: number }
    return response.data; 
  } catch (error: any) {
    // Increment error count
    apiCallErrorCount[endpoint] = (apiCallErrorCount[endpoint] || 0) + 1;
    
    // Log only occasionally to avoid console spam
    if (apiCallErrorCount[endpoint] <= 3 || apiCallErrorCount[endpoint] % 10 === 0) {
      console.error(`Error fetching conversation summaries (attempt #${apiCallErrorCount[endpoint]})`, error.code || error.message || 'Unknown error');
    }
    
    // Special handling for ERR_INSUFFICIENT_RESOURCES
    if (error.message?.includes('ERR_INSUFFICIENT_RESOURCES') || 
        error.code === 'ERR_NETWORK' || 
        error.code === 'ECONNABORTED') {
      
      // Force a longer cooldown for this endpoint
      lastApiCallTime[endpoint] = currentTime + 5000; // Reduced from 15000ms to 5000ms
      
      // Return empty data rather than throwing
      return { conversations: [], total: 0, limit, skip: (page - 1) * limit, throttled: true };
    }
    
    // For other errors, return empty data to prevent cascading failures
    return { conversations: [], total: 0, limit, skip: (page - 1) * limit, throttled: true };
  }
};

/**
 * Delete a specific conversation and all its messages.
 */
export const deleteConversation = async (conversationId: number): Promise<{ message: string; deleted_count: number }> => {
  try {
    const response = await api.delete(`/conversations/${conversationId}`);
    return response.data; // Expected: { message: string, deleted_count: number }
  } catch (error) {
    console.error("Error deleting conversation:", error);
    // Attempt to get more specific error message
    let detail = 'Failed to delete conversation';
    // Check if it's an AxiosError before accessing response
    if (axios.isAxiosError(error) && error.response?.data?.detail) {
      detail = error.response.data.detail;
    }
    throw new Error(detail);
  }
};

/**
 * Delete all conversations for the current user.
 */
// Note: The backend endpoint `/queries/all` still deletes all *individual logs*. 
// We might want a new backend endpoint `/conversations/all` if we want to delete all conversations distinctly.
// For now, keep using the old endpoint, which effectively deletes all conversations anyway.
export const deleteAllConversations = async (): Promise<{ message: string; count: number }> => {
  try {
    // Reusing the old endpoint as it achieves the same result (deleting all logs)
    const response = await api.delete('/queries/all'); 
    return response.data; // Expected: { message: string, count: number }
  } catch (error) {
    console.error("Error deleting all conversations:", error);
    // Check if it's an AxiosError before potentially accessing properties (though not used here)
    let detail = 'Failed to delete all conversations';
    if (axios.isAxiosError(error) && error.response?.data?.detail) {
      detail = error.response.data.detail; // Example if we needed detail
    }
    throw new Error(detail);
  }
};

// --- DEPRECATED (or keep if used elsewhere) ---
/**
 * @deprecated Use deleteConversation instead.
 * Delete a query from the history.
 */
export const deleteQuery = async (queryId: number): Promise<{ success: boolean }> => {
  try {
    const response = await api.delete(`/query/${queryId}`);
    return response.data;
  } catch (error) {
    throw new Error('Failed to delete query');
  }
};

/**
 * @deprecated Use deleteAllConversations instead.
 * Delete all queries for the current user.
 */
export const deleteAllQueries = async (): Promise<{ success: boolean; count: number }> => {
  try {
    const response = await api.delete('/queries/all');
    return response.data;
  } catch (error) {
    throw new Error('Failed to delete all queries');
  }
};

/**
 * Get the user's query usage statistics
 * Returns the number of queries used and the user's limit based on subscription
 */
export const getQueryUsage = async (): Promise<{ used: number; limit: number; subscription_status: string }> => {
  try {
    const response = await api.get('/chat/query-usage');
    return response.data;
  } catch (error) {
    console.error("Error fetching query usage:", error);
    throw new Error('Failed to fetch query usage statistics');
  }
};

// ---------- Form Assistant / Multimodal / Customer Service ----------

export interface FormBlueprintField {
  name: string;
  label: string;
  data_type: string;
  required: boolean;
  helper_text?: string;
  validations?: string[];
}

export interface FormBlueprintSection {
  title: string;
  description?: string;
  fields: FormBlueprintField[];
}

export interface FormBlueprintResponse {
  summary: string;
  sections: FormBlueprintSection[];
  compliance_notes: string[];
}

export interface FormBlueprintPayload {
  form_name: string;
  form_goal: string;
  facility_type?: string;
  jurisdiction?: string;
  context_summary?: string;
}

export const requestFormBlueprint = async (
  payload: FormBlueprintPayload
): Promise<FormBlueprintResponse> => {
  const response = await api.post<FormBlueprintResponse>('/ai/forms/assist', payload);
  return response.data;
};

export interface MultimodalAttachment {
  kind: 'image' | 'audio';
  filename?: string;
  mime_type?: string;
  content_base64: string;
}

export interface MultimodalChatPayload {
  prompt: string;
  facility_type?: string;
  attachments?: MultimodalAttachment[];
}

export interface MultimodalChatResponse {
  reply: string;
  safety_notes: string[];
}

export const sendMultimodalMessage = async (
  payload: MultimodalChatPayload
): Promise<MultimodalChatResponse> => {
  const response = await api.post<MultimodalChatResponse>('/ai/chat/multimodal', payload);
  return response.data;
};

export interface CustomerServiceTicketPayload {
  subject: string;
  description: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  tags?: string[];
}

export interface CustomerServiceAssistantResponse {
  classification: string;
  suggested_actions: string[];
  auto_resolution_attempted: boolean;
  requires_human_review: boolean;
  customer_facing_summary: string;
  audit_context?: Record<string, unknown>;
}

export const triageCustomerTicket = async (
  payload: CustomerServiceTicketPayload,
  priorAttempts = 0
): Promise<CustomerServiceAssistantResponse> => {
  const response = await api.post<CustomerServiceAssistantResponse>(
    `/ai/customer-service/triage?prior_attempts=${priorAttempts}`,
    payload
  );
  return response.data;
};