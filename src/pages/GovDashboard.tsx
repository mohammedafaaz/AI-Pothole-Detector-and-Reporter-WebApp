import React, { useState } from 'react';
import { Filter, Map as MapIcon, List } from 'lucide-react';
import MapComponent from '../components/MapComponent';
import ReportCard from '../components/ReportCard';
import { useAppStore } from '../store';
import NotificationBell from '../components/NotificationBell';

const GovDashboard: React.FC = () => {
  const { reports, govUser } = useAppStore();
  
  const [activeTab, setActiveTab] = useState<'map' | 'feed'>('map');
  const [sortBy, setSortBy] = useState<'newest' | 'oldest' | 'severity'>('newest');
  const [filterStatus, setFilterStatus] = useState<'all' | 'pending' | 'in_progress'>('all');
  
  const filterRadius = 5; // 5km radius
  
  const filteredReports = reports
    .filter(report => {
      if (filterStatus === 'all') return true;
      if (filterStatus === 'pending') return report.verified === 'pending';
      if (filterStatus === 'in_progress') return report.fixingStatus === 'in_progress';
      return true;
    })
    .sort((a, b) => {
      if (sortBy === 'newest') {
        return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime();
      }
      if (sortBy === 'oldest') {
        return new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime();
      }
      if (sortBy === 'severity') {
        const severityOrder = { high: 0, medium: 1, low: 2 };
        return severityOrder[a.severity] - severityOrder[b.severity];
      }
      return 0;
    });
  
  return (
    <div className="h-screen flex flex-col gov-gradient">
      <div className="glass p-4">
        <div className="flex justify-between items-center mb-4">
          <h1 className="text-xl font-bold text-white">Government Dashboard</h1>
          <div className="flex items-center gap-4">
            <NotificationBell />
            <div className="text-sm bg-red-900/50 text-red-200 px-3 py-1 rounded-full">
              5km Radius Assignment
            </div>
          </div>
        </div>
        
        <div className="flex border-b border-red-500/30">
          <button
            className={`py-2 px-4 flex items-center ${
              activeTab === 'map'
                ? 'border-b-2 border-white-500 text-red-400'
                : 'text-red-200 hover:text-red-300'
            }`}
            onClick={() => setActiveTab('map')}
          >
            <MapIcon size={18} className="mr-2" />
            Map View
          </button>
          <button
            className={`py-2 px-4 flex items-center ${
              activeTab === 'feed'
                ? 'border-b-2 border-white-500 text-red-400'
                : 'text-red-200 hover:text-red-300'
            }`}
            onClick={() => setActiveTab('feed')}
          >
            <List size={18} className="mr-2" />
            Reports
          </button>
        </div>
      </div>
      
      <div className="flex-1 overflow-hidden animate-fade-in">
        {activeTab === 'map' ? (
          <div className="h-full">
            {govUser && (
              <MapComponent
                centerLat={govUser.location.lat}
                centerLng={govUser.location.lng}
                zoom={14}
                filterRadius={filterRadius}
              />
            )}
          </div>
        ) : (
          <div className="h-full overflow-y-auto p-4">
            <div className="glass rounded-lg p-3 mb-4 flex items-center justify-between animate-pop-in">
              <div className="flex items-center">
                <Filter size={18} className="text-red-400 mr-2" />
                <span className="text-sm font-medium text-red-200">Filters:</span>
              </div>
              
              <div className="flex space-x-2">
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as 'newest' | 'oldest' | 'severity')}
                  className="text-sm bg-black/100 border border-white-500/30 rounded text-red-200 p-1"
                >
                  <option value="newest">Newest</option>
                  <option value="oldest">Oldest</option>
                  <option value="severity">Highest Severity</option>
                </select>
                
                <select
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value as 'all' | 'pending' | 'in_progress')}
                  className="text-sm bg-black/100 border border-white-500/30 rounded text-red-200 p-1"
                >
                  <option value="all">All Reports</option>
                  <option value="pending">Pending Verification</option>
                  <option value="in_progress">In Progress</option>
                </select>
              </div>
            </div>
            
            {filteredReports.length > 0 ? (
              <div className="grid grid-cols-2 gap-4 animate-fade-in">
                {filteredReports.map(report => (
                  <ReportCard key={report.id} report={report} isGovView={true} />
                ))}
              </div>
            ) : (
              <div className="text-center py-10 text-red-200 animate-fade-in">
                <p>No reports match your filters</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default GovDashboard;