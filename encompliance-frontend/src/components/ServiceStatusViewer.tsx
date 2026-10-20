/*
  Description: ServiceStatusViewer component for support users. Displays the status of backend services and dependencies.
  Purpose: Allows support staff to monitor the health and availability of critical system services.
*/
import React, { useState, useEffect } from 'react';
import customerSupportApi from '../services/customerSupportApi';
import axios from 'axios';
import { CheckCircle, XCircle, HelpCircle } from 'lucide-react'; // Icons for status
import { useCustomerSupportAuth } from '../contexts/CustomerSupportAuthContext';

interface StatusData {
    [serviceName: string]: string; // e.g., { support_api_status: "Running", support_database_status: "Connected" }
}

const ServiceStatusViewer: React.FC = () => {
    const { supportToken } = useCustomerSupportAuth();
    const [statusData, setStatusData] = useState<StatusData | null>(null);
    const [isLoading, setIsLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchData = async () => {
            // Don't set loading true on interval refreshes, only initial
            if (!statusData) setIsLoading(true);
            setError(null);
            
            if (!supportToken) {
                setError("Authentication token is missing.");
                setIsLoading(false);
                return;
            }

            try {
                const response = await customerSupportApi.get<StatusData>('/support/service-status');
                setStatusData(response.data);
            } catch (err: any) {
                console.error("Error fetching service status:", err);
                let errorMsg = "An unknown error occurred while fetching service status.";
                if (axios.isAxiosError(err)) {
                     if (err.response?.status === 401) {
                        errorMsg = "Unauthorized. Please log in again.";
                    } else if (err.response?.data?.detail) {
                        errorMsg = err.response.data.detail;
                    } else if (err.message) {
                         errorMsg = err.message;
                    }
                    // Set status data to show error for specific service if possible?
                    // Or just show a general error for the component.
                    setStatusData(null); // Clear potentially stale data on error
                }
                setError(errorMsg);
            } finally {
                setIsLoading(false);
            }
        };

        // Fetch data initially and set up polling (e.g., every 30 seconds)
        fetchData();
        const intervalId = setInterval(fetchData, 30000);

        return () => clearInterval(intervalId); // Cleanup interval on unmount
    }, [supportToken]); // Only depend on token to avoid multiple intervals

    const renderStatus = (serviceName: string, statusValue: string) => {
        let IconComponent = HelpCircle;
        let textColor = 'text-gray-500';
        let statusText = statusValue;

        if (statusValue.toLowerCase().includes('running') || statusValue.toLowerCase().includes('connected') || statusValue.toLowerCase().includes('active')) {
            IconComponent = CheckCircle;
            textColor = 'text-green-600 dark:text-green-400';
        } else if (statusValue.toLowerCase().includes('error') || statusValue.toLowerCase().includes('failed') || statusValue.toLowerCase().includes('stopped')) {
            IconComponent = XCircle;
            textColor = 'text-red-600 dark:text-red-400';
        } else if (statusValue.toLowerCase().includes('unknown') || statusValue.toLowerCase().includes('not active')) {
            IconComponent = HelpCircle;
             textColor = 'text-yellow-600 dark:text-yellow-400';
        }
        // Add more conditions as needed

        return (
            <div key={serviceName} className="flex items-center justify-between p-2 border-b dark:border-gray-700 last:border-b-0">
                <span className="text-gray-800 dark:text-gray-200 capitalize">{serviceName.replace(/_/g, ' ')}</span>
                <div className={`flex items-center space-x-1 font-medium ${textColor}`}>
                    <IconComponent size={16} />
                    <span>{statusText}</span>
                </div>
            </div>
        );
    };

    if (isLoading && !statusData) { // Show loading only on initial load
        return <div className="text-center p-4">Loading service status...</div>;
    }

    if (error && !statusData) { // Only show full error if no data is present
        return <div className="text-center p-4 text-red-500">Error loading service status: {error}</div>;
    }

    if (!statusData || Object.keys(statusData).length === 0) {
        // Avoid showing this if there's a general error message already
        if (!error) return <div className="text-center p-4">No service status data available.</div>;
    }

    return (
        <div className="space-y-2">
            {/* Show general error above the list if data *is* present but refresh failed */} 
            {error && statusData && <div className="text-center p-2 text-red-500 text-sm">Error refreshing status: {error}</div>}
            {statusData && Object.entries(statusData).map(([key, value]) => renderStatus(key, value))}
        </div>
    );
};

export default ServiceStatusViewer; 
