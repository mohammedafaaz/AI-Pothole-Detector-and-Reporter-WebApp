import React from 'react';
import MobileNavigation from '../components/MobileNavigation';
import WakeUpTimeSettings from '../components/WakeUpTimeSettings';

const WakeTimeSettings: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      <MobileNavigation />

      {/* Header */}
      <div className="bg-white border-b border-gray-200 md:pl-64 pt-0 md:pt-0 mt-0">
        <div className="flex items-center justify-center py-1 md:py-3">
          <div className="flex items-center">
            <div className="w-10 h-10 md:w-16 md:h-16 flex items-center justify-center">
              <img
                src="/logo2.jpg"
                alt="FixMyPothole.AI Logo"
                className="w-10 h-10 md:w-16 md:h-16 object-contain"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Desktop sidebar spacing */}
      <div className="md:pl-64">
        <div className="p-4 md:p-6">
          <div className="mb-6">
            <h1 className="text-2xl font-bold text-gray-900 mb-2">Wake-up Time Settings</h1>
            <p className="text-gray-600">Configure your preferred wake-up time for optimized garbage collection scheduling</p>
          </div>

          <WakeUpTimeSettings />
        </div>
      </div>
    </div>
  );
};

export default WakeTimeSettings;