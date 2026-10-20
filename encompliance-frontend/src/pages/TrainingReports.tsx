/*
  Description: Training Reports page for generating compliance reports for regulatory requirements.
  Purpose: Provides report generation capabilities with filters, preview functionality, and export options for staff summary, program compliance, and certification status reports.
*/

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FileText,
  Download,
  Filter,
  Calendar,
  Users,
  BookOpen,
  Award,
  Search,
  RefreshCw,
  Eye,
  AlertTriangle,
  CheckCircle,
  Clock
} from 'lucide-react';
import { trainingReportsService, trainingProgramService, staffMemberService } from '../services/trainingService';
import ErrorMessage from '../components/ErrorMessage';
import { useAuth } from '../contexts/AuthContext';

interface ReportData {
  report_type: string;
  generated_at: string;
  filters: {
    date_from?: string;
    date_to?: string;
    department?: string;
    program_id?: number;
  };
  data: any[];
  summary: {
    total_records: number;
    report_period: string;
  };
}

interface FilterOptions {
  departments: string[];
  programs: Array<{ id: number; title: string }>;
}

const TrainingReportsPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [reportData, setReportData] = useState<ReportData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);
  const [exporting, setExporting] = useState(false);

  // Form state
  const [reportType, setReportType] = useState<'staff_summary' | 'program_compliance' | 'certification_status'>('staff_summary');
  const [dateFrom, setDateFrom] = useState<string>('');
  const [dateTo, setDateTo] = useState<string>('');
  const [selectedDepartment, setSelectedDepartment] = useState<string>('');
  const [selectedProgram, setSelectedProgram] = useState<number | ''>('');
  
  // Filter options
  const [filterOptions, setFilterOptions] = useState<FilterOptions>({
    departments: [],
    programs: []
  });

  useEffect(() => {
    loadFilterOptions();
  }, []);

  const loadFilterOptions = async () => {
    try {
      // Load programs for filtering
      const programsResponse = await trainingProgramService.getAll({ per_page: 100 });
      const programs = programsResponse.programs.map(p => ({ id: p.id, title: p.title }));

      // Load staff to get unique departments
      const staffResponse = await staffMemberService.getAll({ per_page: 100 });
      const departments = [...new Set(staffResponse.staff_members
        .map(s => s.department)
        .filter((d): d is string => d !== undefined && d !== null && d.trim() !== '')
      )].sort();

      setFilterOptions({
        departments,
        programs
      });
    } catch (err) {
      console.error('Failed to load filter options:', err);
    }
  };

  const generateReport = async () => {
    try {
      setGenerating(true);
      setError(null);

      const params: any = {
        report_type: reportType
      };

      if (dateFrom) params.date_from = dateFrom;
      if (dateTo) params.date_to = dateTo;
      if (selectedDepartment) params.department = selectedDepartment;
      if (selectedProgram) params.program_id = selectedProgram;

      const data = await trainingReportsService.generateComplianceReport(params);
      setReportData(data);
    } catch (err) {
      setError('Failed to generate report');
      console.error('Report generation error:', err);
    } finally {
      setGenerating(false);
    }
  };

  const exportReport = async (format: 'csv' | 'pdf' = 'csv') => {
    if (!reportData) return;

    try {
      setExporting(true);
      const blob = await trainingReportsService.exportReport(reportData, format);
      const filename = `${reportData.report_type}_${new Date().toISOString().split('T')[0]}.${format}`;
      trainingReportsService.downloadFile(blob, filename);
    } catch (err) {
      setError(`Failed to export report as ${format.toUpperCase()}`);
      console.error('Export error:', err);
    } finally {
      setExporting(false);
    }
  };

  const clearFilters = () => {
    setDateFrom('');
    setDateTo('');
    setSelectedDepartment('');
    setSelectedProgram('');
    setReportData(null);
  };

  const getReportTypeInfo = (type: string) => {
    switch (type) {
      case 'staff_summary':
        return {
          title: 'Staff Training Summary',
          description: 'Individual staff member training progress and compliance status',
          icon: <Users className="h-5 w-5" />
        };
      case 'program_compliance':
        return {
          title: 'Program Compliance Report',
          description: 'Training program completion rates and compliance metrics',
          icon: <BookOpen className="h-5 w-5" />
        };
      case 'certification_status':
        return {
          title: 'Certification Status Report',
          description: 'Current certification status and expiry tracking',
          icon: <Award className="h-5 w-5" />
        };
      default:
        return {
          title: 'Training Report',
          description: 'Training compliance report',
          icon: <FileText className="h-5 w-5" />
        };
    }
  };

  const getComplianceStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'compliant':
      case 'valid':
        return 'text-green-600 bg-green-100 dark:bg-green-900/30 dark:text-green-300';
      case 'non-compliant':
      case 'expired/invalid':
        return 'text-red-600 bg-red-100 dark:bg-red-900/30 dark:text-red-300';
      case 'needs attention':
        return 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900/30 dark:text-yellow-300';
      default:
        return 'text-gray-600 bg-gray-100 dark:bg-gray-700 dark:text-gray-300';
    }
  };

  const renderReportPreview = () => {
    if (!reportData || reportData.data.length === 0) {
      return (
        <div className="text-center py-8">
          <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500 dark:text-gray-400">No data available for the selected criteria</p>
        </div>
      );
    }

    const reportInfo = getReportTypeInfo(reportData.report_type);

    return (
      <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md">
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              {reportInfo.icon}
              <div className="ml-3">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  {reportInfo.title}
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Generated on {new Date(reportData.generated_at).toLocaleString()}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => exportReport('csv')}
                disabled={exporting}
                className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 flex items-center transition-colors disabled:opacity-50"
              >
                <Download className="h-4 w-4 mr-2" />
                Export CSV
              </button>
            </div>
          </div>
          <div className="mt-4 text-sm text-gray-600 dark:text-gray-400">
            <span className="font-medium">{reportData.summary.total_records}</span> records found
            <span className="mx-2">•</span>
            Period: {reportData.summary.report_period}
          </div>
        </div>

        <div className="p-6">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-800">
                <tr>
                  {reportData.data.length > 0 && Object.keys(reportData.data[0]).map((header) => (
                    <th
                      key={header}
                      className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider"
                    >
                      {header.replace(/_/g, ' ')}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-dark-surface divide-y divide-gray-200 dark:divide-gray-700">
                {reportData.data.slice(0, 50).map((row, index) => (
                  <tr key={index} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                    {Object.entries(row).map(([key, value], cellIndex) => (
                      <td key={cellIndex} className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                        {key === 'compliance_status' ? (
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getComplianceStatusColor(value as string)}`}>
                            {value as string}
                          </span>
                        ) : key === 'completion_rate' ? (
                          <span className="font-medium">{String(value)}%</span>
                        ) : key.includes('date') && value ? (
                          new Date(value as string).toLocaleDateString()
                        ) : (
                          value?.toString() || '-'
                        )}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {reportData.data.length > 50 && (
            <div className="mt-4 text-center text-sm text-gray-600 dark:text-gray-400">
              Showing first 50 of {reportData.data.length} records. Export to view all data.
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="container mx-auto px-4 py-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-800 dark:text-white mb-2">
              Training Reports
            </h1>
            <p className="text-gray-600 dark:text-gray-300">
              Generate compliance reports for regulatory requirements
            </p>
          </div>
          {/* View Analytics button - Only show for facility administrators */}
          {user?.user_role !== 'team_member' && (
          <button
            onClick={() => navigate('/training/analytics')}
            className="bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 px-4 py-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 flex items-center transition-colors"
          >
            <Eye className="h-4 w-4 mr-2" />
            View Analytics
          </button>
          )}
        </div>
      </div>

      {/* Report Configuration */}
      <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6 mb-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
          <Filter className="h-5 w-5 mr-2" />
          Report Configuration
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Report Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Report Type
            </label>
            <select
              value={reportType}
              onChange={(e) => setReportType(e.target.value as any)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
            >
              <option value="staff_summary">Staff Training Summary</option>
              <option value="program_compliance">Program Compliance</option>
              <option value="certification_status">Certification Status</option>
            </select>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              {getReportTypeInfo(reportType).description}
            </p>
          </div>

          {/* Date Range */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Date From
            </label>
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Date To
            </label>
            <input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
            />
          </div>

          {/* Department Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Department
            </label>
            <select
              value={selectedDepartment}
              onChange={(e) => setSelectedDepartment(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
            >
              <option value="">All Departments</option>
              {filterOptions.departments.map((dept) => (
                <option key={dept} value={dept}>{dept}</option>
              ))}
            </select>
          </div>

          {/* Program Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Training Program
            </label>
            <select
              value={selectedProgram}
              onChange={(e) => setSelectedProgram(e.target.value ? parseInt(e.target.value) : '')}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
            >
              <option value="">All Programs</option>
              {filterOptions.programs.map((program) => (
                <option key={program.id} value={program.id}>{program.title}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-3 mt-6">
          <button
            onClick={generateReport}
            disabled={generating}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 flex items-center transition-colors disabled:opacity-50"
          >
            {generating ? (
              <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <Search className="h-4 w-4 mr-2" />
            )}
            {generating ? 'Generating...' : 'Generate Report'}
          </button>
          <button
            onClick={clearFilters}
            className="bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 px-4 py-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
          >
            Clear Filters
          </button>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="mb-6">
          <ErrorMessage message={error} />
        </div>
      )}

      {/* Report Preview */}
      {reportData && renderReportPreview()}
    </div>
  );
};

export default TrainingReportsPage; 