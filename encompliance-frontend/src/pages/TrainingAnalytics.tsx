/*
  Description: Training Analytics page for comprehensive training metrics and compliance status visualization.
  Purpose: Displays training completion rates, overdue alerts, certification expiry forecasts, and departmental performance analytics for facility administrators.
  
  Note: Facility administrators are users with a pro subscription who manage facility operations.
*/

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  TrendingUp,
  Users,
  BookOpen,
  AlertTriangle,
  Award,
  Calendar,
  BarChart3,
  PieChart,
  Clock,
  Target,
  Filter,
  Download,
  RefreshCw
} from 'lucide-react';
import { trainingDashboardService } from '../services/trainingService';
import ErrorMessage from '../components/ErrorMessage';

interface AnalyticsData {
  completion_rates_by_program: Record<string, number>;
  completion_rates_by_department: Record<string, number>;
  average_completion_time: Record<string, number>;
  overdue_trends: Array<{ month: string; overdue_count: number }>;
  certification_expiry_forecast: Array<{ month: string; expiring_count: number }>;
  effectiveness_metrics: {
    average_score: number;
    pass_rate: number;
    retry_rate: number;
  };
  summary_stats: {
    total_programs_analyzed: number;
    total_departments: number;
    analysis_period: {
      from: string;
      to: string;
    };
  };
}

interface MetricCard {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  color: string;
  trend?: string;
  description?: string;
}

const TrainingAnalyticsPage: React.FC = () => {
  const navigate = useNavigate();
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dateFrom, setDateFrom] = useState<string>('');
  const [dateTo, setDateTo] = useState<string>('');
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadAnalytics();
  }, []);

  const loadAnalytics = async (customDateFrom?: string, customDateTo?: string) => {
    try {
      setLoading(true);
      setError(null);
      const params: any = {};
      if (customDateFrom || dateFrom) params.date_from = customDateFrom || dateFrom;
      if (customDateTo || dateTo) params.date_to = customDateTo || dateTo;
      
      const data = await trainingDashboardService.getAnalytics(params);
      setAnalytics(data);
    } catch (err) {
      setError('Failed to load training analytics');
      console.error('Analytics error:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadAnalytics();
  };

  const handleDateFilter = () => {
    loadAnalytics(dateFrom, dateTo);
  };

  const clearDateFilter = () => {
    setDateFrom('');
    setDateTo('');
    loadAnalytics('', '');
  };

  const formatPercentage = (value: number): string => {
    return `${value.toFixed(1)}%`;
  };

  const formatTime = (minutes: number): string => {
    if (minutes < 60) return `${Math.round(minutes)}m`;
    const hours = Math.floor(minutes / 60);
    const mins = Math.round(minutes % 60);
    return `${hours}h ${mins}m`;
  };

  const getCompletionRateColor = (rate: number): string => {
    if (rate >= 95) return 'text-green-600 bg-green-100 dark:bg-green-900/30 dark:text-green-300';
    if (rate >= 80) return 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900/30 dark:text-yellow-300';
    return 'text-red-600 bg-red-100 dark:bg-red-900/30 dark:text-red-300';
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8 flex justify-center items-center h-64">
        <div className="animate-pulse text-navy-blue dark:text-white">Loading training analytics...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <ErrorMessage message={error} />
        <div className="text-center mt-4">
          <button
            onClick={() => loadAnalytics()}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  if (!analytics) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center">
          <AlertTriangle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">No Analytics Data</h2>
          <p className="text-gray-600 dark:text-gray-400 mb-4">Unable to load training analytics</p>
          <button
            onClick={() => loadAnalytics()}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  const effectivenessMetrics: MetricCard[] = [
    {
      title: 'Average Score',
      value: `${analytics.effectiveness_metrics.average_score.toFixed(1)}%`,
      icon: <Target className="h-6 w-6" />,
      color: 'bg-blue-500',
      description: 'Average completion score across all training'
    },
    {
      title: 'Pass Rate',
      value: formatPercentage(analytics.effectiveness_metrics.pass_rate),
      icon: <Award className="h-6 w-6" />,
      color: 'bg-green-500',
      description: 'Percentage of successful completions'
    },
    {
      title: 'Programs Analyzed',
      value: analytics.summary_stats.total_programs_analyzed,
      icon: <BookOpen className="h-6 w-6" />,
      color: 'bg-purple-500',
      description: 'Total training programs in analysis'
    },
    {
      title: 'Departments',
      value: analytics.summary_stats.total_departments,
      icon: <Users className="h-6 w-6" />,
      color: 'bg-orange-500',
      description: 'Departments included in analysis'
    }
  ];

  return (
    <div className="container mx-auto px-4 py-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-800 dark:text-white mb-2">
              Training Analytics
            </h1>
            <p className="text-gray-600 dark:text-gray-300">
              Comprehensive training metrics and compliance status
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={handleRefresh}
              disabled={refreshing}
              className="bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 px-4 py-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 flex items-center transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
              Refresh
            </button>
            <button
              onClick={() => navigate('/training/reports')}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center transition-colors"
            >
              <Download className="h-4 w-4 mr-2" />
              Generate Report
            </button>
          </div>
        </div>

        {/* Date Filter */}
        <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-4 mb-6">
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
                className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded-md text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
              />
              <span className="text-gray-500">to</span>
              <input
                type="date"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
                className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded-md text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
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
          <div className="mt-2 text-xs text-gray-500">
            Analysis Period: {analytics.summary_stats.analysis_period.from} to {analytics.summary_stats.analysis_period.to}
          </div>
        </div>
      </div>

      {/* Effectiveness Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {effectivenessMetrics.map((metric, index) => (
          <div key={index} className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6">
            <div className="flex items-center">
              <div className={`${metric.color} text-white p-3 rounded-lg`}>
                {metric.icon}
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">{metric.title}</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{metric.value}</p>
                {metric.description && (
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{metric.description}</p>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        {/* Completion Rates by Program */}
        <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md">
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
                <BarChart3 className="h-5 w-5 mr-2" />
                Completion Rates by Program
              </h3>
            </div>
          </div>
          <div className="p-6">
            {Object.keys(analytics.completion_rates_by_program).length === 0 ? (
              <p className="text-gray-500 dark:text-gray-400 text-center py-4">No program data available</p>
            ) : (
              <div className="space-y-4">
                {Object.entries(analytics.completion_rates_by_program)
                  .sort(([,a], [,b]) => b - a)
                  .slice(0, 10)
                  .map(([program, rate]) => (
                    <div key={program} className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm font-medium text-gray-900 dark:text-white truncate">
                            {program}
                          </span>
                          <span className={`text-sm font-medium px-2 py-1 rounded-full ${getCompletionRateColor(rate)}`}>
                            {formatPercentage(rate)}
                          </span>
                        </div>
                        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                          <div
                            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                            style={{ width: `${Math.min(rate, 100)}%` }}
                          ></div>
                        </div>
                      </div>
                    </div>
                  ))}
              </div>
            )}
          </div>
        </div>

        {/* Completion Rates by Department */}
        <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md">
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
                <PieChart className="h-5 w-5 mr-2" />
                Completion Rates by Department
              </h3>
            </div>
          </div>
          <div className="p-6">
            {Object.keys(analytics.completion_rates_by_department).length === 0 ? (
              <p className="text-gray-500 dark:text-gray-400 text-center py-4">No department data available</p>
            ) : (
              <div className="space-y-4">
                {Object.entries(analytics.completion_rates_by_department)
                  .sort(([,a], [,b]) => b - a)
                  .map(([department, rate]) => (
                    <div key={department} className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm font-medium text-gray-900 dark:text-white">
                            {department}
                          </span>
                          <span className={`text-sm font-medium px-2 py-1 rounded-full ${getCompletionRateColor(rate)}`}>
                            {formatPercentage(rate)}
                          </span>
                        </div>
                        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                          <div
                            className="bg-green-600 h-2 rounded-full transition-all duration-300"
                            style={{ width: `${Math.min(rate, 100)}%` }}
                          ></div>
                        </div>
                      </div>
                    </div>
                  ))}
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        {/* Average Completion Time */}
        <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md">
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
              <Clock className="h-5 w-5 mr-2" />
              Average Completion Time
            </h3>
          </div>
          <div className="p-6">
            {Object.keys(analytics.average_completion_time).length === 0 ? (
              <p className="text-gray-500 dark:text-gray-400 text-center py-4">No completion time data available</p>
            ) : (
              <div className="space-y-3">
                {Object.entries(analytics.average_completion_time)
                  .sort(([,a], [,b]) => b - a)
                  .slice(0, 8)
                  .map(([program, time]) => (
                    <div key={program} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                      <span className="text-sm font-medium text-gray-900 dark:text-white truncate flex-1">
                        {program}
                      </span>
                      <span className="text-sm text-gray-600 dark:text-gray-400 ml-2">
                        {formatTime(time)}
                      </span>
                    </div>
                  ))}
              </div>
            )}
          </div>
        </div>

        {/* Overdue Trends */}
        <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md">
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
              <AlertTriangle className="h-5 w-5 mr-2" />
              Overdue Trends (Last 12 Months)
            </h3>
          </div>
          <div className="p-6">
            {analytics.overdue_trends.length === 0 ? (
              <p className="text-gray-500 dark:text-gray-400 text-center py-4">No overdue trend data available</p>
            ) : (
              <div className="space-y-3">
                {analytics.overdue_trends
                  .slice(0, 6)
                  .reverse()
                  .map((trend) => (
                    <div key={`overdue-${trend.month}`} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                      <span className="text-sm font-medium text-gray-900 dark:text-white">
                        {new Date(trend.month + '-01').toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
                      </span>
                      <span className={`text-sm font-medium px-2 py-1 rounded-full ${
                        trend.overdue_count === 0 
                          ? 'text-green-600 bg-green-100 dark:bg-green-900/30 dark:text-green-300'
                          : trend.overdue_count < 5
                          ? 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900/30 dark:text-yellow-300'
                          : 'text-red-600 bg-red-100 dark:bg-red-900/30 dark:text-red-300'
                      }`}>
                        {trend.overdue_count} overdue
                      </span>
                    </div>
                  ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Certification Expiry Forecast */}
      <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md">
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
            <Calendar className="h-5 w-5 mr-2" />
            Certification Expiry Forecast (Next 6 Months)
          </h3>
        </div>
        <div className="p-6">
          {analytics.certification_expiry_forecast.length === 0 ? (
            <p className="text-gray-500 dark:text-gray-400 text-center py-4">No certification expiry data available</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {analytics.certification_expiry_forecast.map((forecast) => (
                <div key={`expiry-${forecast.month}`} className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                  <div className="text-sm font-medium text-gray-900 dark:text-white mb-2">
                    {new Date(forecast.month + '-01').toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
                  </div>
                  <div className={`text-lg font-bold ${
                    forecast.expiring_count === 0 
                      ? 'text-green-600 dark:text-green-400'
                      : forecast.expiring_count < 5
                      ? 'text-yellow-600 dark:text-yellow-400'
                      : 'text-red-600 dark:text-red-400'
                  }`}>
                    {forecast.expiring_count}
                  </div>
                  <div className="text-xs text-gray-600 dark:text-gray-400">
                    certifications expiring
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default TrainingAnalyticsPage; 