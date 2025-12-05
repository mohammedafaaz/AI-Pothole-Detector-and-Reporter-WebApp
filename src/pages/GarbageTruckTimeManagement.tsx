import React from 'react';
import { Clock, Truck, MapPin, ArrowRight } from 'lucide-react';
import Card from '../components/ui/Card';
import MobileNavigation from '../components/MobileNavigation';
import { useAppStore } from '../store';

const GarbageTruckTimeManagement: React.FC = () => {
  const { reports } = useAppStore();

  // Get actual garbage reports from the system
  const garbageReports = reports.filter(report => report.reportType === 'garbage');

  // Group reports by area (simplified - using lat/lng ranges)
  const getAreaFromLocation = (lat: number, lng: number) => {
    // Simple area grouping based on coordinate ranges
    const latRange = Math.floor(lat * 100) / 100;
    const lngRange = Math.floor(lng * 100) / 100;
    return `Area ${latRange.toFixed(2)}, ${lngRange.toFixed(2)}`;
  };

  // Calculate average wake times based on report timestamps
  const areaData = garbageReports.reduce((acc, report) => {
    const area = getAreaFromLocation(report.location.lat, report.location.lng);
    const reportHour = new Date(report.createdAt).getHours();
    
    if (!acc[area]) {
      acc[area] = { reports: [], totalHours: 0, count: 0 };
    }
    
    acc[area].reports.push(report);
    acc[area].totalHours += reportHour;
    acc[area].count += 1;
    
    return acc;
  }, {} as Record<string, { reports: any[], totalHours: number, count: number }>);

  // Convert to sorted array with calculated average wake times
  const sortedAreas = Object.entries(areaData)
    .map(([name, data]) => {
      const avgHour = data.totalHours / data.count;
      const avgWakeTime = `${Math.floor(avgHour)}:${String(Math.floor((avgHour % 1) * 60)).padStart(2, '0')} ${avgHour >= 12 ? 'PM' : 'AM'}`;
      
      return {
        id: name,
        name,
        avgWakeTime,
        timeValue: avgHour,
        reportCount: data.count
      };
    })
    .sort((a, b) => a.timeValue - b.timeValue);

  const getTimeColor = (timeValue: number) => {
    if (timeValue < 6.5) return 'text-green-600 bg-green-50';
    if (timeValue < 7.5) return 'text-yellow-600 bg-yellow-50';
    return 'text-red-600 bg-red-50';
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <MobileNavigation />

      {/* Centered Logo Header */}
      <div className="bg-white border-b border-gray-200 md:pl-64">
        <div className="flex items-center justify-center py-2 md:py-3">
          <div className="flex items-center">
            <div className="w-12 h-12 md:w-16 md:h-16 flex items-center justify-center">
              <img
                src="/logo2.jpg"
                alt="FixMyPothole.AI Logo"
                className="w-12 h-12 md:w-16 md:h-16 object-contain"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Desktop sidebar spacing */}
      <div className="md:pl-64">
        {/* Header */}
        <div className="bg-blue-900 border-b border-blue-800 px-4 py-4 md:px-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-white">Garbage Truck Time Management</h1>
              <p className="text-blue-200 mt-1">Optimize collection routes based on resident activity patterns</p>
            </div>
            <Truck className="w-8 h-8 text-blue-200" />
          </div>
        </div>

        <div className="px-4 md:px-6 py-6">
          {garbageReports.length === 0 ? (
            <Card className="text-center py-12">
              <Truck className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Garbage Reports Available</h3>
              <p className="text-gray-600">
                Garbage truck time management data will be available once garbage dump reports are submitted.
              </p>
            </Card>
          ) : (
            <>
              {/* Statistics Overview */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <Card className="p-6">
                  <div className="flex items-center">
                    <div className="p-3 bg-blue-100 rounded-lg">
                      <Truck className="w-6 h-6 text-blue-600" />
                    </div>
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-600">Total Areas</p>
                      <p className="text-2xl font-bold text-gray-900">{sortedAreas.length}</p>
                    </div>
                  </div>
                </Card>

                <Card className="p-6">
                  <div className="flex items-center">
                    <div className="p-3 bg-green-100 rounded-lg">
                      <MapPin className="w-6 h-6 text-green-600" />
                    </div>
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-600">Total Reports</p>
                      <p className="text-2xl font-bold text-gray-900">{garbageReports.length}</p>
                    </div>
                  </div>
                </Card>

                <Card className="p-6">
                  <div className="flex items-center">
                    <div className="p-3 bg-yellow-100 rounded-lg">
                      <Clock className="w-6 h-6 text-yellow-600" />
                    </div>
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-600">Avg Collection Time</p>
                      <p className="text-2xl font-bold text-gray-900">
                        {sortedAreas.length > 0 
                          ? `${Math.floor(sortedAreas.reduce((sum, area) => sum + area.timeValue, 0) / sortedAreas.length)}:00 AM`
                          : 'N/A'
                        }
                      </p>
                    </div>
                  </div>
                </Card>
              </div>

              {/* Area Statistics */}
              <Card className="p-6 mb-8">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Area Activity Analysis</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {sortedAreas.map((area) => (
                    <div key={area.id} className="p-4 border border-gray-200 rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-semibold text-gray-900">{area.name}</h4>
                        <MapPin className="w-4 h-4 text-gray-500" />
                      </div>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center">
                          <Clock className="w-4 h-4 text-gray-500 mr-1" />
                          <span className={`text-sm font-medium px-2 py-1 rounded ${getTimeColor(area.timeValue)}`}>
                            {area.avgWakeTime}
                          </span>
                        </div>
                        <span className="text-xs text-gray-500">{area.reportCount} reports</span>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>

              {/* Optimized Route */}
              <Card className="p-6">
                <h3 className="text-lg font-semibold text-blue-900 mb-4">Optimized Garbage Collection Route</h3>
                
                <div className="space-y-3">
                  {sortedAreas.map((area, index) => (
                    <div key={area.id} className="flex items-center">
                      <div className="flex items-center bg-white rounded-lg p-3 shadow-sm border border-blue-200 flex-1">
                        <div className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-bold mr-3">
                          {index + 1}
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center justify-between">
                            <span className="font-medium text-gray-900">{area.name}</span>
                            <div className="flex items-center text-sm text-gray-600">
                              <Clock className="w-4 h-4 mr-1" />
                              <span>{area.avgWakeTime}</span>
                            </div>
                          </div>
                          <p className="text-sm text-gray-600">
                            Based on {area.reportCount} report{area.reportCount !== 1 ? 's' : ''} from residents
                          </p>
                        </div>
                      </div>
                      
                      {index < sortedAreas.length - 1 && (
                        <ArrowRight className="w-5 h-5 text-blue-600 mx-2" />
                      )}
                    </div>
                  ))}
                </div>
              </Card>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default GarbageTruckTimeManagement;