import React, { useState } from 'react';
import { Filter, Calendar, AlertTriangle } from 'lucide-react';
import Button from './ui/Button';
import Card from './ui/Card';

interface FilterOptions {
  severity: string[];
  dateRange: 'all' | 'today' | 'week' | 'month' | 'custom';
  customStartDate?: string;
  customEndDate?: string;
  sortBy: 'date' | 'severity' | 'status';
  sortOrder: 'asc' | 'desc';
}

interface ReportFiltersProps {
  filters: FilterOptions;
  onFiltersChange: (filters: FilterOptions) => void;
  className?: string;
}

const ReportFilters: React.FC<ReportFiltersProps> = ({ filters, onFiltersChange, className = '' }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const handleSeverityChange = (severity: string) => {
    const newSeverities = filters.severity.includes(severity)
      ? filters.severity.filter(s => s !== severity)
      : [...filters.severity, severity];
    
    onFiltersChange({ ...filters, severity: newSeverities });
  };

  const handleDateRangeChange = (dateRange: FilterOptions['dateRange']) => {
    onFiltersChange({ 
      ...filters, 
      dateRange,
      customStartDate: undefined,
      customEndDate: undefined
    });
  };

  const handleCustomDateChange = (field: 'customStartDate' | 'customEndDate', value: string) => {
    onFiltersChange({ 
      ...filters, 
      dateRange: 'custom',
      [field]: value 
    });
  };

  const handleSortChange = (sortBy: FilterOptions['sortBy'], sortOrder: FilterOptions['sortOrder']) => {
    onFiltersChange({ ...filters, sortBy, sortOrder });
  };

  const clearFilters = () => {
    onFiltersChange({
      severity: [],
      dateRange: 'all',
      sortBy: 'date',
      sortOrder: 'desc'
    });
  };

  const hasActiveFilters = filters.severity.length > 0 || filters.dateRange !== 'all';

  return (
    <Card className={`${className}`}>
      <div className="p-4">
        {/* Filter Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-gray-600" />
            <h3 className="font-medium text-gray-900">Filters</h3>
            {hasActiveFilters && (
              <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full">
                Active
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            {hasActiveFilters && (
              <Button
                variant="ghost"
                onClick={clearFilters}
                className="text-gray-500 hover:text-gray-700 text-sm"
              >
                Clear
              </Button>
            )}
            <Button
              variant="ghost"
              onClick={() => setIsExpanded(!isExpanded)}
              className="text-gray-500 hover:text-gray-700"
            >
              {isExpanded ? 'Less' : 'More'}
            </Button>
          </div>
        </div>

        {/* Quick Filters - Always Visible */}
        <div className="space-y-4">
          {/* Severity Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Severity
            </label>
            <div className="flex flex-wrap gap-2">
              {['high', 'medium', 'low'].map(severity => (
                <button
                  key={severity}
                  onClick={() => handleSeverityChange(severity)}
                  className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                    filters.severity.includes(severity)
                      ? severity === 'high' 
                        ? 'bg-red-100 text-red-800 border border-red-200'
                        : severity === 'medium'
                        ? 'bg-yellow-100 text-yellow-800 border border-yellow-200'
                        : 'bg-green-100 text-green-800 border border-green-200'
                      : 'bg-gray-100 text-gray-600 border border-gray-200 hover:bg-gray-200'
                  }`}
                >
                  <div className="flex items-center gap-1">
                    <AlertTriangle className="w-3 h-3" />
                    {severity.charAt(0).toUpperCase() + severity.slice(1)}
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Date Range Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Date Range
            </label>
            <div className="flex flex-wrap gap-2">
              {[
                { value: 'all', label: 'All Time' },
                { value: 'today', label: 'Today' },
                { value: 'week', label: 'This Week' },
                { value: 'month', label: 'This Month' },
                { value: 'custom', label: 'Custom' }
              ].map(option => (
                <button
                  key={option.value}
                  onClick={() => handleDateRangeChange(option.value as FilterOptions['dateRange'])}
                  className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                    filters.dateRange === option.value
                      ? 'bg-blue-100 text-blue-800 border border-blue-200'
                      : 'bg-gray-100 text-gray-600 border border-gray-200 hover:bg-gray-200'
                  }`}
                >
                  <div className="flex items-center gap-1">
                    <Calendar className="w-3 h-3" />
                    {option.label}
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Expanded Filters */}
        {isExpanded && (
          <div className="mt-4 pt-4 border-t border-gray-200 space-y-4">
            {/* Custom Date Range */}
            {filters.dateRange === 'custom' && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Start Date
                  </label>
                  <input
                    type="date"
                    value={filters.customStartDate || ''}
                    onChange={(e) => handleCustomDateChange('customStartDate', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    End Date
                  </label>
                  <input
                    type="date"
                    value={filters.customEndDate || ''}
                    onChange={(e) => handleCustomDateChange('customEndDate', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>
            )}

            {/* Sort Options */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Sort By
              </label>
              <div className="grid grid-cols-2 gap-4">
                <select
                  value={filters.sortBy}
                  onChange={(e) => handleSortChange(e.target.value as FilterOptions['sortBy'], filters.sortOrder)}
                  className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="date">Date Created</option>
                  <option value="severity">Severity</option>
                  <option value="status">Status</option>
                </select>
                <select
                  value={filters.sortOrder}
                  onChange={(e) => handleSortChange(filters.sortBy, e.target.value as FilterOptions['sortOrder'])}
                  className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="desc">Newest First</option>
                  <option value="asc">Oldest First</option>
                </select>
              </div>
            </div>
          </div>
        )}
      </div>
    </Card>
  );
};

export default ReportFilters;
export type { FilterOptions };
