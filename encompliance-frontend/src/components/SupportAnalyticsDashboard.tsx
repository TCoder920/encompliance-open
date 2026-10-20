/*
  Description: Support Analytics Dashboard component with visual charts for SLA metrics and ticket analytics.
  Purpose: Provides comprehensive visualization of support ticket metrics, SLA compliance, and performance analytics.
*/
import React, { useState, useEffect } from 'react';
import customerSupportApi from '../services/customerSupportApi';
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  LineChart,
  Line,
} from 'recharts';
import {
  BarChart3,
  TrendingUp,
  AlertCircle,
  Clock,
  CheckCircle,
  Users,
  Ticket,
  Download,
  RefreshCw,
  Filter,
} from 'lucide-react';
import { useCustomerSupportAuth } from '../contexts/CustomerSupportAuthContext';

interface SupportAnalytics {
  total_tickets: number;
  open_tickets: number;
  in_progress_tickets: number;
  resolved_tickets: number;
  closed_tickets: number;
  escalated_tickets: number;
  tickets_by_priority: Record<string, number>;
  tickets_by_category: Record<string, number>;
  tickets_by_tier: Record<string, number>;
  average_resolution_time_hours: number | null;
  average_response_time_hours: number | null;
  tickets_by_agent: Record<string, number>;
  recent_tickets: any[];
  sla_breached_tickets: number;
  sla_compliance_rate: number | null;
  tickets_requiring_attention: number;
}

const SupportAnalyticsDashboard: React.FC = () => {
  const { supportToken } = useCustomerSupportAuth();
  const [analytics, setAnalytics] = useState<SupportAnalytics | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [dateFrom, setDateFrom] = useState<string>('');
  const [dateTo, setDateTo] = useState<string>('');



  const fetchAnalytics = async (customDateFrom?: string, customDateTo?: string) => {
    if (!supportToken) return;

    setLoading(true);
    setError(null);
    try {
      const params: any = {};
      if (customDateFrom || dateFrom) params.date_from = customDateFrom || dateFrom;
      if (customDateTo || dateTo) params.date_to = customDateTo || dateTo;
      
      const response = await customerSupportApi.get<SupportAnalytics>(
        '/api/v1/support/analytics',
        { 
          params
        }
      );
      setAnalytics(response.data);
    } catch (err) {
      console.error('Error fetching analytics:', err);
      setError('Failed to load analytics data');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, [supportToken]);

  const handleDateFilter = () => {
    fetchAnalytics(dateFrom, dateTo);
  };

  const clearDateFilter = () => {
    setDateFrom('');
    setDateTo('');
    fetchAnalytics('', '');
  };

  const handleRefresh = () => {
    setRefreshing(true);
    fetchAnalytics();
  };

  const handleExport = () => {
    if (!analytics) return;
    const dataStr = JSON.stringify(analytics, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `support-analytics-${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-pulse text-gray-600 dark:text-gray-400">Loading analytics...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center p-8">
        <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
        <p className="text-red-600 dark:text-red-400 mb-4">{error}</p>
        <button
          onClick={handleRefresh}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!analytics) {
    return <div className="text-center p-8 text-gray-500">No analytics data available</div>;
  }

  const statusSummary = [
    { name: 'Open', value: analytics.open_tickets, color: '#3b82f6' },
    { name: 'In Progress', value: analytics.in_progress_tickets, color: '#f59e0b' },
    { name: 'Resolved', value: analytics.resolved_tickets, color: '#10b981' },
    { name: 'Closed', value: analytics.closed_tickets, color: '#6b7280' },
    { name: 'Escalated', value: analytics.escalated_tickets, color: '#ef4444' },
  ];
  const totalStatusTickets = statusSummary.reduce((sum, entry) => sum + entry.value, 0);
  const hasStatusTickets = statusSummary.some(entry => entry.value > 0);
  const statusChartData = hasStatusTickets
    ? statusSummary.map(entry => ({
        ...entry,
        chartValue: entry.value > 0 ? entry.value : 0.0001,
      }))
    : [];

  const priorityData = Object.entries(analytics.tickets_by_priority).map(([name, value]) => ({
    name: name.charAt(0).toUpperCase() + name.slice(1),
    value,
  }));

  const categoryData = Object.entries(analytics.tickets_by_category).map(([name, value]) => ({
    name: name.charAt(0).toUpperCase() + name.slice(1),
    value,
  }));

  const tierData = Object.entries(analytics.tickets_by_tier).map(([name, value]) => ({
    name: name.charAt(0).toUpperCase() + name.slice(1),
    value,
  }));

  const agentData = Object.entries(analytics.tickets_by_agent)
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 10); // Top 10 agents

  const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <BarChart3 className="w-6 h-6" />
          Support Analytics Dashboard
        </h2>
        <div className="flex gap-2">
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="flex items-center gap-2 px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-300 dark:hover:bg-gray-600 disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <button
            onClick={handleExport}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            <Download className="w-4 h-4" />
            Export
          </button>
        </div>
      </div>

      {/* Date Range Filter */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 mb-6">
        <div className="flex items-center gap-4 flex-wrap">
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-gray-500" />
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Filter by Date:</span>
          </div>
          <div className="flex items-center gap-2">
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded-md text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            />
            <span className="text-gray-500">to</span>
            <input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded-md text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            />
          </div>
          <button
            onClick={handleDateFilter}
            className="bg-blue-600 text-white px-3 py-1 rounded-md text-sm hover:bg-blue-700"
          >
            Apply
          </button>
          <button
            onClick={clearDateFilter}
            className="bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 px-3 py-1 rounded-md text-sm hover:bg-gray-200 dark:hover:bg-gray-600"
          >
            Clear
          </button>
        </div>
      </div>

      {/* Key Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Total Tickets</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">{analytics.total_tickets}</p>
            </div>
            <Ticket className="w-8 h-8 text-blue-500" />
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">SLA Compliance</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {analytics.sla_compliance_rate !== null ? `${analytics.sla_compliance_rate.toFixed(1)}%` : 'N/A'}
              </p>
            </div>
            <TrendingUp className="w-8 h-8 text-green-500" />
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">SLA Breached</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">{analytics.sla_breached_tickets}</p>
            </div>
            <AlertCircle className="w-8 h-8 text-red-500" />
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Requires Attention</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">{analytics.tickets_requiring_attention}</p>
            </div>
            <Clock className="w-8 h-8 text-orange-500" />
          </div>
        </div>
      </div>

      {/* Performance Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Average Response Time</h3>
          <div className="text-3xl font-bold text-blue-600 dark:text-blue-400">
            {analytics.average_response_time_hours !== null
              ? `${analytics.average_response_time_hours.toFixed(1)}h`
              : 'N/A'}
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Average Resolution Time</h3>
          <div className="text-3xl font-bold text-green-600 dark:text-green-400">
            {analytics.average_resolution_time_hours !== null
              ? `${analytics.average_resolution_time_hours.toFixed(1)}h`
              : 'N/A'}
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Tickets by Status */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Tickets by Status</h3>
          {hasStatusTickets ? (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={statusChartData}
                  cx="50%"
                  cy="45%"
                  labelLine={false}
                  label={false}
                  outerRadius={70}
                  fill="#8884d8"
                  dataKey="chartValue"
                  paddingAngle={statusChartData.length > 1 ? 2 : 0}
                >
                  {statusChartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip 
                  formatter={(_, __, payload) => [`${payload?.payload?.value ?? 0} tickets`, payload?.name || '']}
                  labelFormatter={(name: string) => name}
                  contentStyle={{ 
                    backgroundColor: 'rgba(255, 255, 255, 0.95)',
                    border: '1px solid #ccc',
                    borderRadius: '4px',
                    padding: '8px'
                  }}
                />
                <Legend 
                  verticalAlign="bottom" 
                  height={80}
                  iconType="circle"
                  wrapperStyle={{ paddingTop: '20px' }}
                  formatter={(value: string) => {
                    const entry = statusSummary.find(d => d.name === value);
                    const percentage = entry && totalStatusTickets > 0 ? ((entry.value / totalStatusTickets) * 100).toFixed(0) : '0';
                    return `${value} (${entry?.value || 0} - ${percentage}%)`;
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="text-center text-gray-500 dark:text-gray-400 py-12">
              No tickets have been created yet.
            </div>
          )}
        </div>

        {/* Tickets by Priority */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Tickets by Priority</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={priorityData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" fill="#3b82f6" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Tickets by Category */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Tickets by Category</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={categoryData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" fill="#10b981" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Tickets by Tier */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Tickets by Support Tier</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={tierData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" fill="#8b5cf6" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Top Agents */}
      {agentData.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white flex items-center gap-2">
            <Users className="w-5 h-5" />
            Top Agents by Ticket Count
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={agentData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis dataKey="name" type="category" width={100} />
              <Tooltip />
              <Bar dataKey="value" fill="#f59e0b" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
};

export default SupportAnalyticsDashboard;

