/*
  Description: Audit Log Viewer component for support users. Displays a list of audit logs for monitoring user and system activity.
  Purpose: Enables support staff to review, filter, and analyze audit logs for security and compliance oversight.
*/
import React, { useState, useEffect } from 'react';
import StandardTable, { Column } from './StandardTable';
import customerSupportApi from '../services/customerSupportApi';

// Define interface for expected API data
interface AuditLogEntry {
    id: number;
    admin_user_id: number;
    admin_username?: string; // Added by backend query
    action: string;
    target?: string | null;
    timestamp: string; // Assuming ISO string format
    ip_address?: string | null;
    internal_ip_address?: string | null;
    details?: object | null;
}

// Utility function to format timestamp
const formatTimestamp = (isoString: string): string => {
    try {
        return new Date(isoString).toLocaleString();
    } catch (e) {
        return isoString; // Fallback to original string if parsing fails
    }
};

interface AuditLogViewerProps {
    supportToken?: string | null;
}

const AuditLogViewer: React.FC<AuditLogViewerProps> = ({ supportToken }) => {
    // Note: customerSupportApi handles the token internally if set via setAuth, 
    // but here we might need to rely on the interceptor or just assume the token is set globally.
    // Ideally, we shouldn't pass supportToken as prop if the API client is global, 
    // but customerSupportApi stores the token.
    const [logs, setLogs] = useState<AuditLogEntry[]>([]);
    const [isLoading, setIsLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    const fetchLogs = async () => {
        setIsLoading(true);
        setError(null);
        try {
            const { data } = await customerSupportApi.get<AuditLogEntry[]>('/support/audit-logs');
            setLogs(data);
        } catch (err) {
            console.error("Error fetching audit logs:", err);
            setError(err instanceof Error ? err.message : "An unknown error occurred");
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchLogs();
    }, [supportToken]);

    // Build table columns - dynamically include internal_ip_address if available
    const buildColumns = () => {
        const hasInternalIp = logs.length > 0 && 'internal_ip_address' in logs[0];
        
        const columns: Column<AuditLogEntry>[] = [
            { key: 'timestamp', header: 'Timestamp', sortable: true, renderCell: log => formatTimestamp(log.timestamp) },
            { key: 'admin_username', header: 'User', sortable: true, renderCell: log => log.admin_username || `ID: ${log.admin_user_id}` },
            { key: 'action', header: 'Action', sortable: true },
            { key: 'target', header: 'Target', sortable: true, renderCell: log => log.target || '-' },
            { key: 'ip_address', header: 'IP Address', sortable: true, renderCell: log => log.ip_address || '-' },
        ];
        
        // Only add internal_ip_address column if the field exists in the data
        if (hasInternalIp) {
            columns.push({ 
                key: 'internal_ip_address', 
                header: 'Internal IP', 
                sortable: true, 
                renderCell: log => log.internal_ip_address || '-' 
            });
        }
        
        columns.push({ 
            key: 'details', 
            header: 'Details', 
            sortable: false, 
            renderCell: log => log.details ? <pre className="text-xs bg-gray-100 dark:bg-gray-900 p-1 rounded overflow-x-auto max-w-xs">{JSON.stringify(log.details, null, 2)}</pre> : null 
        });
        
        return columns;
    };

    const columns = buildColumns();

    if (isLoading) return <div className="text-center p-4">Loading logs...</div>;
    if (error) return <div className="text-center p-4 text-red-500">Error: {error}</div>;

    return (
        <StandardTable columns={columns} data={logs} pageSize={20} />
    );
};

export default AuditLogViewer; 
