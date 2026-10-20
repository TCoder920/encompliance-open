/*
  Description: FileTreeVisualizer component for support users. Visualizes the file structure of the backend or storage system.
  Purpose: Helps support staff explore, audit, and manage files in a hierarchical tree view.
*/
import React, { useState, useEffect } from 'react';
import customerSupportApi from '../services/customerSupportApi';
import axios from 'axios';
// Placeholder: Import a tree library like react-d3-tree if using one
// import Tree from 'react-d3-tree';

// Define interfaces for the expected data structure
interface TreeNode {
    name: string;
    type: 'directory' | 'file' | 'error';
    path: string;
    last_modified?: string;
    size?: number;
    error?: string;
    children?: TreeNode[];
    // Add attributes for the tree library if needed (e.g., _collapsed)
}

interface FileTreeData {
    [rootName: string]: TreeNode; // e.g., { backend: TreeNode, frontend: TreeNode, ... }
}

// Define Props interface
interface FileTreeVisualizerProps {
  supportToken: string | null;
}

// Placeholder: Define API function type
// type ApiFunction = () => Promise<FileTreeData>; 

const FileTreeVisualizer: React.FC<FileTreeVisualizerProps> = ({ supportToken }) => {
    const [treeData, setTreeData] = useState<FileTreeData | null>(null);
    const [isLoading, setIsLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);
    // Track collapse state for directories
    const [collapsed, setCollapsed] = useState<Record<string, boolean>>({});

    const toggleCollapse = (path: string) => {
      setCollapsed(prev => ({ ...prev, [path]: !prev[path] }));
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
                const response = await customerSupportApi.get<FileTreeData>('/support/file-structure');
                setTreeData(response.data);
                // Initialize collapsed state: collapse all directories initially
                const initialCollapsed: Record<string, boolean> = {};
                const setInitialCollapse = (node: TreeNode) => {
                    if (node.type === 'directory') {
                        initialCollapsed[node.path] = true; // Collapse directories
                        if (node.children) {
                            node.children.forEach(setInitialCollapse);
                        }
                    }
                };
                Object.values(response.data).forEach(setInitialCollapse);
                setCollapsed(initialCollapsed);
            } catch (err: any) {
                console.error("Error fetching file tree:", err);
                let errorMsg = "An unknown error occurred while fetching the file structure.";
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

    // Simple recursive renderer function (replace with react-d3-tree or similar)
    const renderNode = (node: TreeNode, depth = 0): React.ReactNode => (
        <div key={node.path || node.name} style={{ marginLeft: `${depth * 20}px` }} className="py-1">
            {/* Expand/collapse button for directories */}
            {node.type === 'directory' && (
              <button onClick={() => toggleCollapse(node.path)} className="mr-1 text-gray-500 dark:text-gray-400 focus:outline-none">
                {collapsed[node.path] ? '▶️' : '▼'}
              </button>
            )}
            <span className={`${node.type === 'directory' ? 'font-semibold text-blue-600 dark:text-blue-400' : 'text-gray-700 dark:text-gray-300'} cursor-pointer`}>
                {node.type === 'directory' ? '📁' : '📄'} {node.name}
            </span>
            {node.size !== undefined && <span className="text-xs text-gray-500 ml-2">({(node.size / 1024).toFixed(1)} KB)</span>}
            {node.error && <span className="text-xs text-red-500 ml-2">Error: {node.error}</span>}
            {/* Only render children if not collapsed */}
            {node.children && node.children.length > 0 && !collapsed[node.path] && (
                <div>{node.children.map(child => renderNode(child, depth + 1))}</div>
            )}
        </div>
    );

    if (isLoading) {
        return <div className="text-center p-4">Loading file structure...</div>;
    }

    if (error) {
        return <div className="text-center p-4 text-red-500">Error: {error}</div>;
    }

    if (!treeData || Object.keys(treeData).length === 0) {
        return <div className="text-center p-4">No file structure data available.</div>;
    }

    return (
        <div className="overflow-auto max-h-96 border dark:border-gray-700 rounded p-2 bg-gray-50 dark:bg-gray-900">
            {/* Placeholder for react-d3-tree or other library */} 
            {/* <Tree data={treeData} orientation="vertical" /> */}
            
            {/* Simple recursive render */}
            {Object.values(treeData).map(rootNode => renderNode(rootNode))}
        </div>
    );
};

export default FileTreeVisualizer; 
