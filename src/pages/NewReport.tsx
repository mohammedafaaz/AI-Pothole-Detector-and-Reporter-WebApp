import React from 'react';
import ReportForm from '../components/ReportForm';
import LanguageToggle from '../components/LanguageToggle';
import MobileNavigation from '../components/MobileNavigation';

const NewReport: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      <MobileNavigation />

      {/* Desktop sidebar spacing */}
      <div className="md:pl-64">
        <div className="p-4 mb-4 flex justify-end">
          <LanguageToggle />
        </div>
        <div className="p-4">
          <ReportForm />
        </div>
      </div>
    </div>
  );
};

export default NewReport;