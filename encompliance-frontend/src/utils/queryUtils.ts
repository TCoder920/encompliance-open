/*
  Description: Utility functions for processing, deduplicating, and grouping query logs from AI interactions.
  Purpose: Supports efficient log management and analysis for compliance queries and conversations.
*/

export interface QueryLog {
  id: number;
  query_text?: string;
  response_text?: string;
  created_at?: string;
  query?: string;
  response?: string;
  timestamp?: string;
  document_reference?: string;
  conversation_id?: number;
  full_conversation?: boolean;
}

/**
 * Deduplicates query logs based on query text and creation time
 * Removes logs that have the same query text and were created within 1 minute of each other
 * 
 * @param logs Array of query logs to deduplicate
 * @returns Deduplicated array of query logs
 */
export function deduplicateQueryLogs(logs: QueryLog[]): QueryLog[] {
  if (!logs || logs.length === 0) {
    return [];
  }
  
  console.log(`Deduplicating ${logs.length} query logs`);
  
  // First, normalize the logs to ensure all fields are present
  const normalizedLogs = logs.map(log => ({
    ...log,
    query_text: log.query_text || log.query || '',
    response_text: log.response_text || log.response || '',
    created_at: log.created_at || log.timestamp || new Date().toISOString()
  }));
  
  // Sort logs by creation time (newest first) to ensure we keep the most recent logs
  const sortedLogs = [...normalizedLogs].sort((a, b) => {
    const dateA = new Date(a.created_at || '');
    const dateB = new Date(b.created_at || '');
    return dateB.getTime() - dateA.getTime();
  });
  
  // Deduplicate logs based on query_text and created_at (within 1 minute)
  const deduplicatedLogs = sortedLogs.reduce((acc: QueryLog[], current: QueryLog) => {
    // Check if this log is a duplicate (same query text and created within 1 minute of another log)
    const isDuplicate = acc.some(log => {
      if (log.query_text === current.query_text) {
        // Check if created within 1 minute
        const logDate = new Date(log.created_at || '');
        const currentDate = new Date(current.created_at || '');
        const diffInMs = Math.abs(currentDate.getTime() - logDate.getTime());
        const diffInMinutes = diffInMs / (1000 * 60);
        return diffInMinutes < 1;
      }
      return false;
    });
    
    if (!isDuplicate) {
      acc.push(current);
    } else {
      console.log(`Filtered out duplicate log: ${current.id}`);
    }
    
    return acc;
  }, []);
  
  console.log(`Deduplicated to ${deduplicatedLogs.length} logs`);
  return deduplicatedLogs;
}

/**
 * Groups query logs by conversation
 * Logs with the same conversation_id are grouped together
 * 
 * @param logs Array of query logs to group
 * @returns Object with conversation_id as keys and arrays of logs as values
 */
export function groupQueryLogsByConversation(logs: QueryLog[]): Record<string, QueryLog[]> {
  if (!logs || logs.length === 0) {
    return {};
  }
  
  const groupedLogs: Record<string, QueryLog[]> = {};
  
  logs.forEach(log => {
    const conversationId = log.conversation_id?.toString() || 'unknown';
    if (!groupedLogs[conversationId]) {
      groupedLogs[conversationId] = [];
    }
    groupedLogs[conversationId].push(log);
  });
  
  // Sort logs within each conversation by creation time
  Object.keys(groupedLogs).forEach(conversationId => {
    groupedLogs[conversationId].sort((a, b) => {
      const dateA = new Date(a.created_at || a.timestamp || '');
      const dateB = new Date(b.created_at || b.timestamp || '');
      return dateA.getTime() - dateB.getTime();
    });
  });
  
  return groupedLogs;
} 