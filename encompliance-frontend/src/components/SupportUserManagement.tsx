/*
  Description: SupportUserManagement component for support users. Provides tools to manage user accounts, roles, and permissions.
  Purpose: Enables support staff to view, edit, and control user access within the platform.
*/
import React, { useState, useEffect } from 'react';
import { ShieldEllipsis } from 'lucide-react';
import customerSupportApi from '../services/customerSupportApi';
import { useCustomerSupportAuth } from '../contexts/CustomerSupportAuthContext';

// Define interfaces for expected API data
interface SupportUser {
    id: number;
    username: string;
    email: string;
    roles: string[];
    created_at?: string; // Assuming ISO string format
    updated_at?: string;
}

interface SupportUserManagementProps {
    isAdmin: boolean;
}

const roleOptions = [
    { value: 'support_agent', label: 'Support Agent' },
    { value: 'support_admin', label: 'Support Admin' },
];

const SupportUserManagement: React.FC<SupportUserManagementProps> = ({ isAdmin }) => {
    const { supportToken } = useCustomerSupportAuth();
    const [users, setUsers] = useState<SupportUser[]>([]);
    const [isLoading, setIsLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);
    const [isManagerOpen, setIsManagerOpen] = useState<boolean>(false);
    const [managerMode, setManagerMode] = useState<'add' | 'update' | 'remove'>('add');
    const [newAgent, setNewAgent] = useState({ username: '', email: '', password: '', role: 'support_agent' });
    const [selectedAgentId, setSelectedAgentId] = useState<number | null>(null);
    const [selectedRole, setSelectedRole] = useState<string>('support_agent');

    const fetchUsers = async () => {
        // customerSupportApi handles token
        setIsLoading(true);
        setError(null);
        try {
            const response = await customerSupportApi.get<SupportUser[]>('/support/users');
            setUsers(response.data);
        } catch (err: any) {
            console.error("Error fetching support users:", err);
            let errorMsg = "An unknown error occurred while fetching users.";
            if (err.response?.status === 401 || err.response?.status === 403) {
                 errorMsg = "Unauthorized. Please log in again or check permissions.";
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

    useEffect(() => {
        if (isAdmin) {
            fetchUsers();
        } else {
            setUsers([]);
        }
    }, [supportToken, isAdmin]);

    useEffect(() => {
        if (users.length > 0 && selectedAgentId === null) {
            setSelectedAgentId(users[0].id);
        }
    }, [users, selectedAgentId]);

    const handleAddAgent = async (event: React.FormEvent) => {
        event.preventDefault();
        if (!newAgent.username || !newAgent.email || !newAgent.password) {
            setError("All fields are required to create an agent.");
            return;
        }
        setError(null);
        try {
            await customerSupportApi.post(
                '/support/users',
                {
                    username: newAgent.username,
                    email: newAgent.email,
                    password: newAgent.password,
                    roles: [newAgent.role],
                }
            );
            setNewAgent({ username: '', email: '', password: '', role: 'support_agent' });
            await fetchUsers();
            setIsManagerOpen(false);
            alert("Support agent added successfully.");
        } catch (err: any) {
            console.error("Error creating support user:", err);
            const errorMsg = err.response?.data?.detail
                ? err.response.data.detail
                : err.message || "Failed to create support agent.";
            setError(errorMsg);
        }
    };

    const handleRoleUpdate = async (event: React.FormEvent) => {
        event.preventDefault();
        if (!selectedAgentId) {
            setError("Select an agent to update.");
            return;
        }
        setError(null);
        try {
            await customerSupportApi.put(
                `/support/users/${selectedAgentId}`,
                { roles: [selectedRole] }
            );
            await fetchUsers();
            setIsManagerOpen(false);
            alert("Agent role updated successfully.");
        } catch (err: any) {
            console.error("Error updating support user:", err);
            const errorMsg = err.response?.data?.detail
                ? err.response.data.detail
                : err.message || "Failed to update support agent.";
            setError(errorMsg);
        }
    };

    const handleRemoveAgent = async (event: React.FormEvent) => {
        event.preventDefault();
        if (!selectedAgentId) {
            setError("Select an agent to remove.");
            return;
        }
        if (!window.confirm("Are you sure you want to remove this support agent?")) {
            return;
        }
        setError(null);
        try {
            await customerSupportApi.delete(`/support/users/${selectedAgentId}`);
            await fetchUsers();
            setIsManagerOpen(false);
            alert("Support agent removed successfully.");
        } catch (err: any) {
            console.error("Error removing support user:", err);
            const errorMsg = err.response?.data?.detail
                ? err.response.data.detail
                : err.message || "Failed to remove support agent.";
            setError(errorMsg);
        }
    };

    if (!isAdmin) {
        return (
            <div className="text-center text-gray-500">
                You do not have permission to manage support agents.
            </div>
        );
    }

    if (isLoading) return <div className="text-center p-4">Loading users...</div>;
    if (error && users.length === 0) return <div className="text-center p-4 text-red-500">Error: {error}</div>; // Show error only if no users loaded

    return (
        <div>
             {/* Display error above table if users are already loaded */} 
             {error && users.length > 0 && <div className="text-center p-2 text-red-500 text-sm">Error during operation: {error}</div>}
            
             <div className="flex justify-end mb-4">
                 <button
                     onClick={() => setIsManagerOpen(prev => !prev)}
                     className="flex items-center bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
                 >
                     <ShieldEllipsis className="w-4 h-4 mr-2" />
                     {isManagerOpen ? 'Close Agent Manager' : 'Manage Agents'}
                 </button>
             </div>

             {isManagerOpen && (
                 <div className="bg-gray-50 dark:bg-gray-900 border dark:border-gray-700 rounded-lg p-4 mb-6">
                     <div className="flex flex-wrap gap-2 mb-4">
                         {(['add', 'update', 'remove'] as const).map(mode => (
                             <button
                                 key={mode}
                                 onClick={() => setManagerMode(mode)}
                                 className={`px-3 py-1 rounded text-sm font-semibold ${
                                     managerMode === mode ? 'bg-blue-600 text-white' : 'bg-gray-200 dark:bg-gray-800 text-gray-700 dark:text-gray-300'
                                 }`}
                             >
                                 {mode === 'add' && 'Add Agent'}
                                 {mode === 'update' && 'Update Role'}
                                 {mode === 'remove' && 'Remove Agent'}
                             </button>
                         ))}
                     </div>

                     {managerMode === 'add' && (
                         <form className="grid grid-cols-1 md:grid-cols-2 gap-4" onSubmit={handleAddAgent}>
                             <input
                                 type="text"
                                 placeholder="Username"
                                 value={newAgent.username}
                                 onChange={(e) => setNewAgent({ ...newAgent, username: e.target.value })}
                                 className="border rounded px-3 py-2 dark:bg-gray-800 dark:border-gray-700"
                                 required
                             />
                             <input
                                 type="email"
                                 placeholder="Email"
                                 value={newAgent.email}
                                 onChange={(e) => setNewAgent({ ...newAgent, email: e.target.value })}
                                 className="border rounded px-3 py-2 dark:bg-gray-800 dark:border-gray-700"
                                 required
                             />
                             <input
                                 type="password"
                                 placeholder="Temporary Password"
                                 value={newAgent.password}
                                 onChange={(e) => setNewAgent({ ...newAgent, password: e.target.value })}
                                 className="border rounded px-3 py-2 dark:bg-gray-800 dark:border-gray-700"
                                 required
                             />
                             <select
                                 value={newAgent.role}
                                 onChange={(e) => setNewAgent({ ...newAgent, role: e.target.value })}
                                 className="border rounded px-3 py-2 dark:bg-gray-800 dark:border-gray-700"
                             >
                                 {roleOptions.map(option => (
                                     <option key={option.value} value={option.value}>
                                         {option.label}
                                     </option>
                                 ))}
                             </select>
                             <button
                                 type="submit"
                                 className="md:col-span-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 rounded"
                             >
                                 Invite Support Agent
                             </button>
                         </form>
                     )}

                    {managerMode === 'update' && (
                        users.length === 0 ? (
                            <p className="text-sm text-gray-500 dark:text-gray-400">No agents available to update.</p>
                        ) : (
                            <form className="grid grid-cols-1 md:grid-cols-2 gap-4" onSubmit={handleRoleUpdate}>
                                <select
                                    value={selectedAgentId ?? ''}
                                    onChange={(e) => setSelectedAgentId(Number(e.target.value))}
                                    className="border rounded px-3 py-2 dark:bg-gray-800 dark:border-gray-700"
                                >
                                    {users.map(user => (
                                        <option key={user.id} value={user.id}>
                                            {user.username}
                                        </option>
                                    ))}
                                </select>
                                <select
                                    value={selectedRole}
                                    onChange={(e) => setSelectedRole(e.target.value)}
                                    className="border rounded px-3 py-2 dark:bg-gray-800 dark:border-gray-700"
                                >
                                    {roleOptions.map(option => (
                                        <option key={option.value} value={option.value}>
                                            {option.label}
                                        </option>
                                    ))}
                                </select>
                                <button
                                    type="submit"
                                    className="md:col-span-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 rounded"
                                >
                                    Update Agent Role
                                </button>
                            </form>
                        )
                    )}

                    {managerMode === 'remove' && (
                        users.length === 0 ? (
                            <p className="text-sm text-gray-500 dark:text-gray-400">No agents available to remove.</p>
                        ) : (
                            <form className="grid grid-cols-1 md:grid-cols-2 gap-4" onSubmit={handleRemoveAgent}>
                                <select
                                    value={selectedAgentId ?? ''}
                                    onChange={(e) => setSelectedAgentId(Number(e.target.value))}
                                    className="border rounded px-3 py-2 dark:bg-gray-800 dark:border-gray-700"
                                >
                                    {users.map(user => (
                                        <option key={user.id} value={user.id}>
                                            {user.username}
                                        </option>
                                    ))}
                                </select>
                                <div className="text-sm text-gray-600 dark:text-gray-400 flex items-center">
                                    Removing an agent revokes their support portal access immediately.
                                </div>
                                <button
                                    type="submit"
                                    className="md:col-span-2 bg-red-600 hover:bg-red-700 text-white font-semibold py-2 rounded"
                                >
                                    Remove Agent
                                </button>
                            </form>
                        )
                    )}
                 </div>
             )}

             <div className="overflow-x-auto">
                <table className="min-w-full bg-white dark:bg-gray-800 border dark:border-gray-700">
                    <thead>
                        <tr className="bg-gray-100 dark:bg-gray-700">
                            <th className="py-2 px-4 border-b dark:border-gray-600 text-left">ID</th>
                            <th className="py-2 px-4 border-b dark:border-gray-600 text-left">Username</th>
                            <th className="py-2 px-4 border-b dark:border-gray-600 text-left">Email</th>
                            <th className="py-2 px-4 border-b dark:border-gray-600 text-left">Roles</th>
                            <th className="py-2 px-4 border-b dark:border-gray-600 text-left">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {users.map(user => (
                            <tr key={user.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                                <td className="py-2 px-4 border-b dark:border-gray-600">{user.id}</td>
                                <td className="py-2 px-4 border-b dark:border-gray-600">{user.username}</td>
                                <td className="py-2 px-4 border-b dark:border-gray-600">{user.email}</td>
                                <td className="py-2 px-4 border-b dark:border-gray-600">
                                    {user.roles.map(role => (
                                        <span key={role} className="bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 text-xs font-medium mr-2 px-2.5 py-0.5 rounded">
                                            {role}
                                        </span>
                                    ))}
                                </td>
                                <td className="py-2 px-4 border-b dark:border-gray-600 text-sm text-gray-500">
                                    Managed via the control panel above
                                </td>
                            </tr>
                        ))}
                        {users.length === 0 && !isLoading && (
                            <tr>
                                <td colSpan={5} className="text-center py-4 text-gray-500">No support users found.</td>
                            </tr>
                        )}
                    </tbody>
                </table>
             </div>
             {/* Placeholder for Create/Edit Modals */}
         </div>
    );
};

export default SupportUserManagement; 
