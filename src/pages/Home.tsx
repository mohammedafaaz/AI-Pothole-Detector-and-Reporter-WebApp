import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Camera, Filter, TestTube } from 'lucide-react';
import MapComponent from '../components/MapComponent';
import ReportCard from '../components/ReportCard';
import { useAppStore } from '../store';
import NotificationBell from '../components/NotificationBell';
import { runAPITests } from '../utils/apiTest';

const Home: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { reports } = useAppStore();
  
  const [activeTab, setActiveTab] = useState<'map' | 'feed'>('map');
  const [sortBy, setSortBy] = useState<'newest' | 'oldest' | 'upvotes'>('newest');
  const [filterVerified, setFilterVerified] = useState<'all' | 'verified' | 'pending'>('all');
  
  const handleNewReport = () => {
    navigate('/new-report');
  };

  const handleTestAPI = () => {
    runAPITests();
  };
  
  // Parse lat/lng from query params for map centering
  const params = new URLSearchParams(location.search);
  const lat = params.get('lat');
  const lng = params.get('lng');
  const mapCenter = lat && lng ? { lat: parseFloat(lat), lng: parseFloat(lng) } : undefined;

  const filteredReports = reports
    .filter(report => {
      if (filterVerified === 'all') return true;
      if (filterVerified === 'verified') return report.verified === 'verified';
      if (filterVerified === 'pending') return report.verified === 'pending';
      return true;
    })
    .sort((a, b) => {
      if (sortBy === 'newest') {
        return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime();
      }
      if (sortBy === 'oldest') {
        return new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime();
      }
      if (sortBy === 'upvotes') {
        return b.upvotes - a.upvotes;
      }
      return 0;
    });
  
  return (
    <div className="h-screen flex flex-col dark-gradient">
      <div className="glass p-4">
        <div className="flex justify-between items-center mb-4">
          <h1 className="text-xl font-bold text-white">Pothole Reporter</h1>
          <div className="flex items-center gap-4">
            <NotificationBell />
            <button
              onClick={handleTestAPI}
              className="bg-green-500 hover:bg-green-600 text-white py-2 px-3 rounded-full flex items-center transition-colors"
              title="Test Flask API Connection"
            >
              <TestTube size={16} />
            </button>
            <button
              onClick={handleNewReport}
              className="bg-blue-500 hover:bg-blue-600 text-white py-2 px-4 rounded-full flex items-center transition-colors"
            >
              <Camera size={18} className="mr-2" />
              Report
            </button>
          </div>
        </div>
        
        <div className="flex border-b border-blue-500/30">
          <button
            className={`py-2 px-4 ${
              activeTab === 'map'
                ? 'border-b-2 border-blue-500 text-blue-400'
                : 'text-blue-200 hover:text-blue-300'
            }`}
            onClick={() => setActiveTab('map')}
          >
            Map View
          </button>
          <button
            className={`py-2 px-4 ${
              activeTab === 'feed'
                ? 'border-b-2 border-blue-500 text-blue-400'
                : 'text-blue-200 hover:text-blue-300'
            }`}
            onClick={() => setActiveTab('feed')}
          >
            Live Feed
          </button>
        </div>
      </div>
      
      <div className="flex-1 overflow-hidden animate-fade-in">
        {activeTab === 'map' ? (
          <div className="h-full">
            <MapComponent
              centerLat={mapCenter?.lat}
              centerLng={mapCenter?.lng}
            />
          </div>
        ) : (
          <div className="h-full overflow-y-auto p-4">
            <div className="glass p-3 mb-4 flex items-center justify-between rounded-lg animate-pop-in">
              <div className="flex items-center">
                <Filter size={18} className="text-blue-400 mr-2" />
                <span className="text-sm font-medium text-blue-200">Filters:</span>
              </div>
              
              <div className="flex space-x-2">
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as 'newest' | 'oldest' | 'upvotes')}
                  className="text-sm bg-black/100 border border-blue-500/30 rounded text-blue-200 p-1"
                >
                  <option value="newest">Newest</option>
                  <option value="oldest">Oldest</option>
                  <option value="upvotes">Most Upvotes</option>
                </select>
                
                <select
                  value={filterVerified}
                  onChange={(e) => setFilterVerified(e.target.value as 'all' | 'verified' | 'pending')}
                  className="text-sm bg-black/100 border border-blue-500/30 rounded text-blue-200 p-1"
                >
                  <option value="all">All Reports</option>
                  <option value="verified">Verified Only</option>
                  <option value="pending">Pending Only</option>
                </select>
              </div>
            </div>
            
            {filteredReports.length > 0 ? (
              <div className="grid grid-cols-2 gap-4 animate-fade-in">
                {filteredReports.map(report => (
                  <ReportCard key={report.id} report={report} />
                ))}
              </div>
            ) : (
              <div className="text-center py-10 text-blue-200 animate-fade-in">
                <p>No reports match your filters</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default Home;