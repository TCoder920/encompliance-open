/*
  Description: Data Explorer component for support users. Allows exploration and visualization of database tables and records.
  Purpose: Provides tools for support staff to query, view, and analyze backend data in a secure interface.
*/
import React, { useState, useEffect } from 'react';
import customerSupportApi from '../services/customerSupportApi';
import { Database, Table, Columns, Hash, Server } from 'lucide-react'; // Icons

// Interfaces for the expected API data structure
interface ColumnInfo {
  name: string;
  type: string;
  nullable: boolean;
  primary_key: boolean;
}

interface TableInfo {
  row_count: number;
  columns: ColumnInfo[];
}

interface DatabaseInfo {
  type: string;
  tables: Record<string, TableInfo>;
  error?: string;
}

interface DbData {
  admin_db: DatabaseInfo;
  user_db: DatabaseInfo;
}

// Props interface
interface DataExplorerProps {
  supportToken: string | null;
}

const DataExplorer: React.FC<DataExplorerProps> = ({ supportToken }) => {
    const [dbData, setDbData] = useState<DbData | null>(null);
    const [isLoading, setIsLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);
    const [expandedTables, setExpandedTables] = useState<Record<string, boolean>>({});

    const toggleTable = (tableName: string) => {
        setExpandedTables(prev => ({ ...prev, [tableName]: !prev[tableName] }));
    };

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
                const response = await customerSupportApi.get<DbData>('/support/db-data');
                setDbData(response.data);
            } catch (err: any) {
                console.error("Error fetching DB data:", err);
                let errorMsg = "An unknown error occurred while fetching database information.";
                if (err.response?.status === 401) {
                    errorMsg = "Unauthorized. Please log in again.";
                } else if (err.response?.data?.detail) {
                    errorMsg = err.response.data.detail;
                } else if (err.message) {
                    errorMsg = err.message;
                }
                setError(errorMsg);
            } finally {
                setIsLoading(false);
            }
        };

        fetchData();
    }, [supportToken]);

    const renderDatabase = (dbName: string, dbInfo: DatabaseInfo) => (
        <div key={dbName} className="bg-white dark:bg-dark-surface p-4 rounded-lg shadow-md mb-4 transition-colors duration-1000">
            <h3 className="text-lg font-semibold mb-3 flex items-center text-navy-blue dark:text-white">
                {dbInfo.type === 'SQLite' ? <Database size={20} className="mr-2" /> : <Server size={20} className="mr-2" />}
                {dbName.replace('_db', '').toUpperCase()} Database ({dbInfo.type})
            </h3>
            {dbInfo.error && <p className="text-red-600 dark:text-red-400">Error loading data: {dbInfo.error}</p>}
            {!dbInfo.error && Object.keys(dbInfo.tables).length === 0 && <p className="text-gray-600 dark:text-gray-400">No tables found.</p>}
            <div className="space-y-2">
                {Object.entries(dbInfo.tables).map(([tableName, tableInfo]) => (
                    <div key={tableName} className="border border-gray-200 dark:border-gray-700 rounded">
                        <button
                            onClick={() => toggleTable(`${dbName}-${tableName}`)}
                            className="flex justify-between items-center w-full p-2 text-left bg-gray-50 dark:bg-gray-700 hover:bg-gray-100 dark:hover:bg-gray-600 rounded-t text-gray-800 dark:text-gray-200 transition-colors duration-200"
                        >
                            <span className="font-medium flex items-center">
                                <Table size={16} className="mr-2" /> {tableName}
                            </span>
                            <span className="text-sm text-gray-500 dark:text-gray-400 flex items-center">
                                <Hash size={14} className="mr-1"/> {tableInfo.row_count >= 0 ? `${tableInfo.row_count} rows` : 'Count Error'}
                                <span className="ml-2 text-xl">{expandedTables[`${dbName}-${tableName}`] ? '−' : '+'}</span>
                            </span>
                        </button>
                        {expandedTables[`${dbName}-${tableName}`] && (
                            <div className="p-3 bg-white dark:bg-dark-surface text-xs text-gray-700 dark:text-gray-300">
                                <h4 className="font-semibold mb-1 flex items-center text-gray-800 dark:text-gray-100"><Columns size={14} className="mr-1"/> Columns:</h4>
                                <ul className="list-disc list-inside pl-2 space-y-1">
                                    {tableInfo.columns.map(col => (
                                        <li key={col.name} className="font-mono">
                                            <span className={`${col.primary_key ? 'font-bold text-blue-600 dark:text-blue-400' : ''}`}>{col.name}</span>
                                            <span className="text-gray-500 dark:text-gray-500"> ({col.type}{col.nullable ? ', Nullable' : ''}{col.primary_key ? ', PK' : ''})</span>
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );

    if (isLoading) {
        return <div className="text-center p-4">Loading database information...</div>;
    }

    if (error) {
        return <div className="text-center p-4 text-red-600 dark:text-red-400">Error loading database information: {error}</div>;
    }

    if (!dbData) {
        return <div className="text-center p-4 text-gray-600 dark:text-gray-400">No database data available.</div>;
    }

    return (
        <div className="text-gray-900 dark:text-dark-text">
            {renderDatabase('admin_db', dbData.admin_db)}
            {renderDatabase('user_db', dbData.user_db)}
        </div>
    );
};

export default DataExplorer; 
