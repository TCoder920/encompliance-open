/*
  Description: Customer Support Portal - Ticket-centric workspace for support agents.
  Purpose: Provides comprehensive ticket management, customer context, and support analytics.
*/
import React, { useEffect, useState, useRef } from 'react';

import { 
  Ticket, Search, Filter, User, BarChart3, Settings, LogOut,
  AlertCircle, Clock, CheckCircle, XCircle, ArrowUp, Users
} from 'lucide-react';
import ThemeToggle from '../components/ThemeToggle';
import AuditLogViewer from '../components/AuditLogViewer';
import SupportUserManagement from '../components/SupportUserManagement';
import SupportTicketList from '../components/SupportTicketList';
import SupportTicketDetail from '../components/SupportTicketDetail';
import SupportAnalyticsDashboard from '../components/SupportAnalyticsDashboard';
import RealtimeNotificationToast from '../components/RealtimeNotificationToast';
import { useCustomerSupportAuth } from '../contexts/CustomerSupportAuthContext';
import { supportWebSocketService, TicketEvent } from '../services/supportWebSocket';
import customerSupportApi from '../services/customerSupportApi';

interface CustomerSupportPortalProps {
    onLogout: () => void;
}

type ViewMode = 'tickets' | 'users' | 'agents' | 'analytics' | 'audit';

interface SupportAccount {
    id: number;
    username: string;
    email: string;
    roles?: string[];
}

const CustomerSupportPortal: React.FC<CustomerSupportPortalProps> = ({ onLogout }) => {
    const { supportToken, logout } = useCustomerSupportAuth();
    const isMountedRef = useRef(true);
    const [viewMode, setViewMode] = useState<ViewMode>('tickets');
    const viewModeRef = useRef(viewMode);

    useEffect(() => {
        viewModeRef.current = viewMode;
    }, [viewMode]);
    const [ticketRefreshTrigger, setTicketRefreshTrigger] = useState(0);
    const [selectedTicketId, setSelectedTicketId] = useState<number | null>(null);
    const [ticketFilters, setTicketFilters] = useState({
        status: '',
        priority: '',
        category: '',
        assignedToMe: false,
        unassigned: false,
    });
    const [analytics, setAnalytics] = useState<any>(null);
    const [currentAccount, setCurrentAccount] = useState<SupportAccount | null>(null);
    const [isSupportAdmin, setIsSupportAdmin] = useState<boolean>(false);
    const [accountLoading, setAccountLoading] = useState<boolean>(false);
    const [sessionExpired, setSessionExpired] = useState<boolean>(false);

    useEffect(() => {
        document.documentElement.classList.add('dark');
    }, []);

    useEffect(() => {
        supportWebSocketService.setAuthFailureHandler(() => {
            setSessionExpired(true);
            logout();
        });
    }, [logout]);

    useEffect(() => {
        if (supportToken) {
            setSessionExpired(false);
        }
    }, [supportToken]);

    // WebSocket connection for real-time notifications
    useEffect(() => {
        isMountedRef.current = true;

        if (supportToken) {
            // GUARD: Check if service is already active to prevent Strict Mode duplicates
            if (!supportWebSocketService.isConnected() && !supportWebSocketService.isConnectingState) {
                supportWebSocketService.connect(supportToken);
            }

            // Subscribe to ticket events
            const unsubscribe = supportWebSocketService.subscribe('all', (event: TicketEvent) => {
                if (!isMountedRef.current) return;

                console.log('Received ticket event:', event);
                
                // Refresh ticket list if viewing tickets
                if (viewModeRef.current === 'tickets') {
                    // Trigger a refresh by updating a state that causes re-render
                    handleTicketUpdate();
                }
                
                // Show notification toast (optional)
                if (event.type === 'ticket_assigned' && event.data.assigned_to_account_id) {
                    // Could show a toast notification here
                }
            });

            return () => {
                isMountedRef.current = false;
                unsubscribe();
                
                // Delay disconnect to avoid Strict Mode double-mount issues
                setTimeout(() => {
                    if (!isMountedRef.current) {
                        supportWebSocketService.disconnect();
                    }
                }, 100);
            };
        }
    }, [supportToken]);

    useEffect(() => {
        let isMounted = true;

        const loadAccount = async () => {
            if (!supportToken) {
                setCurrentAccount(null);
                setIsSupportAdmin(false);
                return;
            }

            setAccountLoading(true);
            try {
                const { data } = await customerSupportApi.get('/auth/me');
                if (!isMounted) {
                    return;
                }
                setCurrentAccount(data);
                const hasAdminRole = Array.isArray(data.roles) && data.roles.includes('support_admin');
                setIsSupportAdmin(hasAdminRole);
            } catch (error) {
                if (isMounted) {
                    console.error('Failed to load support account profile:', error);
                    setCurrentAccount(null);
                    setIsSupportAdmin(false);
                }
            } finally {
                if (isMounted) {
                    setAccountLoading(false);
                }
            }
        };

        loadAccount();
        return () => {
            isMounted = false;
        };
    }, [supportToken]);

    useEffect(() => {
        if (viewMode === 'analytics' && supportToken) {
            const fetchAnalytics = async () => {
                try {
                    const response = await customerSupportApi.get('/api/v1/support/analytics');
                    setAnalytics(response.data);
                } catch (err) {
                    console.error('Error fetching analytics:', err);
                }
            };
            fetchAnalytics();
        }
    }, [viewMode, supportToken]);

    const handleTicketSelect = (ticket: any) => {
        setSelectedTicketId(ticket.id);
    };

    const handleTicketUpdate = () => {
        // Refresh ticket list if needed
        setTicketRefreshTrigger(prev => prev + 1);
    };

    const renderContent = () => {
        if (!supportToken) {
            return <div className="text-center p-8 text-gray-400">Authenticating...</div>;
        }

        if (accountLoading) {
            return <div className="text-center p-8 text-gray-400">Loading workspace...</div>;
        }

        switch (viewMode) {
            case 'tickets':
                return (
                    <div className="space-y-4">
                        {/* Ticket Filters */}
                        <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-4">
                            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                                <div>
                                    <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">
                                        Status
                                    </label>
                                    <select
                                        value={ticketFilters.status}
                                        onChange={(e) => setTicketFilters({ ...ticketFilters, status: e.target.value })}
                                        className="w-full border rounded px-3 py-2 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                                    >
                                        <option value="">All</option>
                                        <option value="open">Open</option>
                                        <option value="in_progress">In Progress</option>
                                        <option value="escalated">Escalated</option>
                                        <option value="resolved">Resolved</option>
                                        <option value="closed">Closed</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">
                                        Priority
                                    </label>
                                    <select
                                        value={ticketFilters.priority}
                                        onChange={(e) => setTicketFilters({ ...ticketFilters, priority: e.target.value })}
                                        className="w-full border rounded px-3 py-2 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                                    >
                                        <option value="">All</option>
                                        <option value="low">Low</option>
                                        <option value="medium">Medium</option>
                                        <option value="high">High</option>
                                        <option value="urgent">Urgent</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">
                                        Category
                                    </label>
                                    <select
                                        value={ticketFilters.category}
                                        onChange={(e) => setTicketFilters({ ...ticketFilters, category: e.target.value })}
                                        className="w-full border rounded px-3 py-2 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                                    >
                                        <option value="">All</option>
                                        <option value="billing">Billing</option>
                                        <option value="technical">Technical</option>
                                        <option value="training">Training</option>
                                        <option value="account">Account</option>
                                        <option value="documentation">Documentation</option>
                                        <option value="other">Other</option>
                                    </select>
                                </div>
                                <div className="flex items-end gap-2">
                                    <label className="flex items-center gap-2 text-sm">
                                        <input
                                            type="checkbox"
                                            checked={ticketFilters.assignedToMe}
                                            onChange={(e) => setTicketFilters({ ...ticketFilters, assignedToMe: e.target.checked, unassigned: false })}
                                            className="rounded"
                                        />
                                        <span>My Tickets</span>
                                    </label>
                                    <label className="flex items-center gap-2 text-sm">
                                        <input
                                            type="checkbox"
                                            checked={ticketFilters.unassigned}
                                            onChange={(e) => setTicketFilters({ ...ticketFilters, unassigned: e.target.checked, assignedToMe: false })}
                                            className="rounded"
                                        />
                                        <span>Unassigned</span>
                                    </label>
                                </div>
                            </div>
                        </div>

                        {/* Ticket List */}
                        <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6">
                            <SupportTicketList
                                supportToken={supportToken}
                                onTicketSelect={handleTicketSelect}
                                statusFilter={ticketFilters.status || undefined}
                                priorityFilter={ticketFilters.priority || undefined}
                                categoryFilter={ticketFilters.category || undefined}
                                assignedToMe={ticketFilters.assignedToMe}
                                unassigned={ticketFilters.unassigned}
                                refreshTrigger={ticketRefreshTrigger}
                            />
                        </div>

                        {/* Ticket Detail Modal */}
                        {selectedTicketId && (
                            <SupportTicketDetail
                                ticketId={selectedTicketId}
                                supportToken={supportToken}
                                onClose={() => setSelectedTicketId(null)}
                                onUpdate={handleTicketUpdate}
                                currentAccountId={currentAccount?.id ?? null}
                                isSupportAdmin={isSupportAdmin}
                            />
                        )}
                    </div>
                );

            case 'users':
                if (!isSupportAdmin) {
                    return (
                        <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6 text-center text-gray-500">
                            User overviews are restricted to support administrators.
                        </div>
                    );
                }
                return (
                    <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6">
                        <h2 className="text-xl font-bold text-navy-blue dark:text-white mb-4">User Overview</h2>
                        <UserOverview supportToken={supportToken} />
                    </div>
                );

            case 'agents':
                if (!isSupportAdmin) {
                    return (
                        <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6 text-center text-gray-500">
                            Only support administrators can manage other agents.
                        </div>
                    );
                }
                return (
                    <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6">
                        <h2 className="text-xl font-bold text-navy-blue dark:text-white mb-4">Support Agent Management</h2>
                        <SupportUserManagement isAdmin={isSupportAdmin} />
                    </div>
                );

            case 'analytics':
                return <SupportAnalyticsDashboard />;

            case 'audit':
                if (!isSupportAdmin) {
                    return (
                        <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6 text-center text-gray-500">
                            Audit logs are available to support administrators only.
                        </div>
                    );
                }
                return (
                    <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6">
                        <h2 className="text-xl font-bold text-navy-blue dark:text-white mb-4">Audit Logs</h2>
                        <AuditLogViewer supportToken={supportToken} />
                    </div>
                );

            default:
                return null;
        }
    };

    // UserOverview component (simplified version)
    const UserOverview: React.FC<{ supportToken: string | null }> = ({ supportToken }) => {
        const [users, setUsers] = useState<any[]>([]);
        const [loading, setLoading] = useState<boolean>(true);

        useEffect(() => {
            if (!supportToken) return;

            const fetchUsers = async () => {
                try {
                    const response = await customerSupportApi.get(
                        '/support/user-data'
                    );
                    setUsers(response.data || []);
                } catch (err) {
                    console.error('Error fetching users:', err);
                } finally {
                    setLoading(false);
                }
            };
            fetchUsers();
        }, [supportToken]);

        if (loading) return <div>Loading users...</div>;
        if (users.length === 0) return <div className="text-gray-500">No users found</div>;

        return (
            <div className="overflow-x-auto">
                <table className="min-w-full">
                    <thead>
                        <tr className="border-b dark:border-gray-700">
                            <th className="text-left p-2">ID</th>
                            <th className="text-left p-2">Email</th>
                            <th className="text-left p-2">Title</th>
                            <th className="text-left p-2">Status</th>
                            <th className="text-left p-2">Subscription</th>
                        </tr>
                    </thead>
                    <tbody>
                        {users.slice(0, 20).map((user) => (
                            <tr key={user.id} className="border-b dark:border-gray-700">
                                <td className="p-2">{user.id}</td>
                                <td className="p-2 break-all">{user.email}</td>
                                <td className="p-2">
                                    {user.title || user.user_role || 'Not specified'}
                                </td>
                                <td className="p-2">{user.is_active ? 'Active' : 'Inactive'}</td>
                                <td className="p-2">{user.subscription_status || 'Free'}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
                    </div>
        );
    };

    return (
        <div className="flex flex-col min-h-screen bg-gray-50 dark:bg-dark-bg dark:text-dark-text transition-colors duration-1000">
            {sessionExpired && (
                <div className="bg-red-50 text-red-700 px-4 py-3 text-center text-sm">
                    Your support session expired. Please log in again to receive live notifications.
                </div>
            )}
            {/* Header */}
            <div className="bg-white dark:bg-dark-surface border-b dark:border-gray-700 shadow-sm">
                <div className="container mx-auto px-4 py-4">
                    <div className="flex justify-between items-center">
                        <h1 className="text-2xl font-bold text-navy-blue dark:text-white">
                            Customer Support Portal
                        </h1>
                        <div className="flex items-center gap-4">
                        <ThemeToggle />
                        <button
                                onClick={onLogout}
                                className="flex items-center gap-2 px-4 py-2 bg-navy-blue hover:bg-blue-800 text-white font-bold rounded transition duration-200"
                        >
                                <LogOut className="w-4 h-4" />
                            Logout
                        </button>
                        </div>
                    </div>
                </div>
            </div>

            {/* Navigation */}
            <div className="bg-white dark:bg-dark-surface border-b dark:border-gray-700">
                <div className="container mx-auto px-4">
                    <nav className="flex gap-1">
                        {[
                            { id: 'tickets', label: 'Tickets', icon: Ticket },
                            ...(isSupportAdmin ? [{ id: 'users', label: 'Users', icon: Users }] : []),
                            ...(isSupportAdmin ? [{ id: 'agents', label: 'Agents', icon: User }] : []),
                            { id: 'analytics', label: 'Analytics', icon: BarChart3 },
                            ...(isSupportAdmin ? [{ id: 'audit', label: 'Audit Logs', icon: Settings }] : []),
                        ].map(({ id, label, icon: Icon }) => (
                            <button
                                key={id}
                                onClick={() => setViewMode(id as ViewMode)}
                                className={`flex items-center gap-2 px-4 py-3 border-b-2 transition-colors ${
                                    viewMode === id
                                        ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                                        : 'border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
                                }`}
                            >
                                <Icon className="w-4 h-4" />
                                {label}
                            </button>
                        ))}
                    </nav>
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 container mx-auto px-4 py-6">
                {renderContent()}
            </div>

            {/* Real-time Notifications */}
            <RealtimeNotificationToast />
        </div>
    );
};

export default CustomerSupportPortal;
