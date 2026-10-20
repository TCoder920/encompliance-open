/*
  Description: DbSchemaVisualizer component for support users. Visualizes the database schema and relationships between tables.
  Purpose: Helps support staff and developers understand and manage the structure of the application's database.
*/
import React, { useState, useEffect } from 'react';
import customerSupportApi from '../services/customerSupportApi';
import axios from 'axios';
import { useCustomerSupportAuth } from '../contexts/CustomerSupportAuthContext';
// Placeholder: Import a library like react-flow if using one
// import ReactFlow, { MiniMap, Controls, Background } from 'reactflow';
// import 'reactflow/dist/style.css';

// Define interfaces for expected API response
interface ColumnInfo {
    name: string;
    type: string;
    nullable: boolean;
    default: string | null;
    primary_key: boolean;
}

interface TableInfo {
    [tableName: string]: ColumnInfo[];
}

interface DbSchemaData {
    tables: TableInfo;
    // Potentially add relationships/foreign keys here if API provides them
}

const DbSchemaVisualizer: React.FC = () => {
    const { supportToken } = useCustomerSupportAuth();
    const [schemaData, setSchemaData] = useState<DbSchemaData | null>(null);
    const [isLoading, setIsLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    // Placeholder: State for React Flow nodes/edges if used
    // const [nodes, setNodes] = useState([]);
    // const [edges, setEdges] = useState([]);

    useEffect(() => {
        const fetchData = async () => {
            if (!supportToken) {
                setError("Authentication token is missing.");
                setIsLoading(false);
                return;
            }
            
            setIsLoading(true);
            setError(null);
            try {
                const response = await customerSupportApi.get<DbSchemaData>('/support/db-schema');
                setSchemaData(response.data);
            } catch (err: any) {
                console.error("Error fetching DB schema:", err);
                let errorMsg = "An unknown error occurred while fetching the DB schema.";
                if (axios.isAxiosError(err)) {
                    if (err.response?.status === 401) {
                        errorMsg = "Unauthorized. Please log in again.";
                    } else if (err.response?.data?.detail) {
                        errorMsg = err.response.data.detail;
                    } else if (err.message) {
                         errorMsg = err.message;
                    }
                }
                setError(errorMsg);
            } finally {
                setIsLoading(false);
            }
        };
        fetchData();
    }, [supportToken]); // Re-fetch if token changes

    // Placeholder: Simple text renderer for schema
    const renderSimpleSchema = (data: DbSchemaData) => {
        return Object.entries(data.tables).map(([tableName, columns]) => (
            <div key={tableName} className="mb-4 p-3 border dark:border-gray-600 rounded bg-gray-100 dark:bg-gray-800">
                <h4 className="font-semibold text-lg mb-2 text-purple-700 dark:text-purple-400">{tableName}</h4>
                <ul>
                    {columns.map(col => (
                        <li key={col.name} className="text-sm text-gray-700 dark:text-gray-300">
                            <span className={col.primary_key ? 'font-bold text-yellow-600 dark:text-yellow-400' : ''}>{col.primary_key ? '🔑 ' : ''}{col.name}</span>: {col.type} {col.nullable ? '(nullable)' : ''}
                        </li>
                    ))}
                </ul>
            </div>
        ));
    };

    if (isLoading) return <div className="text-center p-4">Loading DB Schema...</div>;
    if (error) return <div className="text-center p-4 text-red-500">Error: {error}</div>;
    if (!schemaData) return <div className="text-center p-4">No schema data found.</div>;

    return (
        <div className="overflow-auto max-h-96">
            {/* Placeholder for React Flow */}
            {/* <div style={{ height: '400px' }}> */}
            {/*     <ReactFlow nodes={nodes} edges={edges} fitView> */}
            {/*         <MiniMap /> */}
            {/*         <Controls /> */}
            {/*         <Background /> */}
            {/*     </ReactFlow> */}
            {/* </div> */}
            
            {/* Simple text render fallback */}
            {renderSimpleSchema(schemaData)}
        </div>
    );
};

// Placeholder: Function to transform schema to React Flow nodes/edges
// function transformSchemaToFlow(schemaData: DbSchemaData) { ... return { nodes, edges }; }

export default DbSchemaVisualizer; 
