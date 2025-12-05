import React, { useState } from 'react';
import { Users, ChevronDown, ChevronUp, Clock, AlertTriangle } from 'lucide-react';
import { GroupedReport } from '../types';
import ModernReportCard from './ModernReportCard';
import Card from './ui/Card';

interface GroupedReportCardProps {
  groupedReport: GroupedReport;
  isGovView?: boolean;
}

const GroupedReportCard: React.FC<GroupedReportCardProps> = ({ 
  groupedReport, 
  isGovView = false 
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const reportCount = groupedReport.reports.length;
  
  const getSeverityStats = () => {
    const severityCounts = groupedReport.reports.reduce((acc, report) => {
      acc[report.severity] = (acc[report.severity] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
    return severityCounts;
  };
  
  const getTimeRange = () => {
    const dates = groupedReport.reports.map(r => new Date(r.createdAt));
    const earliest = new Date(Math.min(...dates.map(d => d.getTime())));
    const latest = new Date(Math.max(...dates.map(d => d.getTime())));
    return { earliest, latest };
  };
  
  const severityStats = getSeverityStats();
  const timeRange = getTimeRange();
  const hasHighSeverity = groupedReport.reports.some(r => r.severity === 'high');

  if (reportCount === 1) {
    return (
      <ModernReportCard
        report={groupedReport.reports[0]}
        isGovView={isGovView}
        showAnnotatedImages={true}
      />
    );
  }

  return (
    <Card variant="default" padding="sm" className={`border-l-4 ${hasHighSeverity ? 'border-l-red-500' : 'border-l-blue-500'}`}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Users className={`w-5 h-5 ${hasHighSeverity ? 'text-red-600' : 'text-blue-600'}`} />
          <span className="font-semibold text-gray-900">
            {reportCount} Reports at Same Location
          </span>
          {hasHighSeverity && (
            <AlertTriangle className="w-4 h-4 text-red-500" />
          )}
        </div>
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className={`flex items-center gap-1 ${hasHighSeverity ? 'text-red-600 hover:text-red-800' : 'text-blue-600 hover:text-blue-800'}`}
        >
          {isExpanded ? (
            <>
              <span className="text-sm">Collapse</span>
              <ChevronUp className="w-4 h-4" />
            </>
          ) : (
            <>
              <span className="text-sm">View All</span>
              <ChevronDown className="w-4 h-4" />
            </>
          )}
        </button>
      </div>
      
      {/* Summary Stats */}
      <div className="flex items-center gap-4 mb-3 text-sm text-gray-600">
        <div className="flex items-center gap-1">
          <Clock className="w-4 h-4" />
          <span>
            {timeRange.earliest.toLocaleDateString()} - {timeRange.latest.toLocaleDateString()}
          </span>
        </div>
        <div className="flex gap-2">
          {Object.entries(severityStats).map(([severity, count]) => (
            <span key={severity} className={`px-2 py-1 rounded text-xs font-medium ${
              severity === 'high' ? 'bg-red-100 text-red-800' :
              severity === 'medium' ? 'bg-yellow-100 text-yellow-800' :
              'bg-green-100 text-green-800'
            }`}>
              {count} {severity}
            </span>
          ))}
        </div>
      </div>

      <div className="mb-3">
        <ModernReportCard
          report={groupedReport.reports[0]}
          isGovView={isGovView}
          showAnnotatedImages={true}
        />
      </div>

      {isExpanded && (
        <div className="space-y-3 border-t pt-3">
          {groupedReport.reports.slice(1).map((report) => (
            <ModernReportCard
              key={report.id}
              report={report}
              isGovView={isGovView}
              showAnnotatedImages={true}
            />
          ))}
        </div>
      )}
    </Card>
  );
};

export default GroupedReportCard;