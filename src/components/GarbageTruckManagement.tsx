import React from 'react';
import { Clock, Truck, MapPin, ArrowRight } from 'lucide-react';
import Card from './ui/Card';

// Mock data for garbage truck time management
const mockAreaData = [
  { id: '1', name: 'PB ROAD', avgWakeTime: '6:00 AM', timeValue: 6.0 },
  { id: '2', name: 'SRI ANJANEYA SWAMY TEMPLE ROAD', avgWakeTime: '6:45 AM', timeValue: 6.75 },
  { id: '3', name: 'ITI PARK', avgWakeTime: '7:20 AM', timeValue: 7.33 },
  { id: '4', name: 'OLD FORT ROAD', avgWakeTime: '8:00 AM', timeValue: 8.0 }
];

const GarbageTruckManagement: React.FC = () => {
  // Sort areas by earliest waking time
  const sortedAreas = [...mockAreaData].sort((a, b) => a.timeValue - b.timeValue);

  const getTimeColor = (timeValue: number) => {
    if (timeValue < 6.5) return 'text-green-600 bg-green-50';
    if (timeValue < 7.5) return 'text-yellow-600 bg-yellow-50';
    return 'text-red-600 bg-red-50';
  };

  return (
    <Card className="p-6">
      <div className="flex items-center mb-6">
        <Truck className="w-6 h-6 text-blue-600 mr-2" />
        <h2 className="text-xl font-bold text-gray-900">Garbage Truck Time Management</h2>
      </div>

      {/* Area Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {sortedAreas.map((area) => (
          <div key={area.id} className="p-4 border border-gray-200 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-semibold text-gray-900">{area.name}</h3>
              <MapPin className="w-4 h-4 text-gray-500" />
            </div>
            <div className="flex items-center">
              <Clock className="w-4 h-4 text-gray-500 mr-1" />
              <span className={`text-sm font-medium px-2 py-1 rounded ${getTimeColor(area.timeValue)}`}>
                {area.avgWakeTime}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Optimized Route */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
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
                  <p className="text-sm text-gray-600">Average resident garbage dumping time</p>
                </div>
              </div>
              
              {index < sortedAreas.length - 1 && (
                <ArrowRight className="w-5 h-5 text-blue-600 mx-2" />
              )}
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
};

export default GarbageTruckManagement;