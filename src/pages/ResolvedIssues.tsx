import React from 'react';
import { CheckCircle, Calendar, MapPin, User } from 'lucide-react';
import Card from '../components/ui/Card';
import MobileNavigation from '../components/MobileNavigation';
import { useAppStore } from '../store';

const ResolvedIssues: React.FC = () => {
  const { reports } = useAppStore();

  const resolvedReports = reports.filter(report => report.fixingStatus === 'resolved');

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
        <div className="bg-green-900 border-b border-green-800 px-4 py-4 md:px-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-white">Resolved Issues</h1>
              <p className="text-green-200 mt-1">Successfully fixed problems in your jurisdiction</p>
            </div>
            <CheckCircle className="w-8 h-8 text-green-200" />
          </div>
        </div>

        <div className="px-4 md:px-6 py-6">
          {resolvedReports.length === 0 ? (
            <Card className="text-center py-12">
              <CheckCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Resolved Issues Yet</h3>
              <p className="text-gray-600">
                Resolved issues will appear here once reports are marked as fixed.
              </p>
            </Card>
          ) : (
            <>
              {/* Statistics */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <Card className="p-6">
                  <div className="flex items-center">
                    <div className="p-3 bg-green-100 rounded-lg">
                      <CheckCircle className="w-6 h-6 text-green-600" />
                    </div>
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-600">Total Resolved</p>
                      <p className="text-2xl font-bold text-gray-900">{resolvedReports.length}</p>
                    </div>
                  </div>
                </Card>

                <Card className="p-6">
                  <div className="flex items-center">
                    <div className="p-3 bg-blue-100 rounded-lg">
                      <Calendar className="w-6 h-6 text-blue-600" />
                    </div>
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-600">This Month</p>
                      <p className="text-2xl font-bold text-gray-900">
                        {resolvedReports.filter(r => {
                          const reportDate = new Date(r.createdAt);
                          const now = new Date();
                          return reportDate.getMonth() === now.getMonth() && 
                                 reportDate.getFullYear() === now.getFullYear();
                        }).length}
                      </p>
                    </div>
                  </div>
                </Card>

                <Card className="p-6">
                  <div className="flex items-center">
                    <div className="p-3 bg-purple-100 rounded-lg">
                      <MapPin className="w-6 h-6 text-purple-600" />
                    </div>
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-600">Avg Resolution Time</p>
                      <p className="text-2xl font-bold text-gray-900">3 days</p>
                    </div>
                  </div>
                </Card>
              </div>

              {/* Resolved Reports List */}
              <div className="space-y-4">
                {resolvedReports.map((report) => (
                  <Card key={report.id} className="p-6">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <CheckCircle className="w-5 h-5 text-green-600" />
                          <span className="font-semibold text-gray-900">
                            {report.reportType === 'pothole' ? 'Pothole' : 'Garbage Dump'} Fixed
                          </span>
                          <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                            Resolved
                          </span>
                        </div>
                        
                        <div className="flex items-center gap-4 text-sm text-gray-600 mb-3">
                          <div className="flex items-center gap-1">
                            <MapPin className="w-4 h-4" />
                            <span>{report.location.address}</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <User className="w-4 h-4" />
                            <span>Reported by {report.userName}</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <Calendar className="w-4 h-4" />
                            <span>{new Date(report.createdAt).toLocaleDateString()}</span>
                          </div>
                        </div>

                        {report.description && (
                          <p className="text-gray-700 mb-3">{report.description}</p>
                        )}

                        <div className="flex items-center gap-2">
                          <span className={`px-2 py-1 rounded text-xs font-medium ${
                            report.severity === 'high' ? 'bg-red-100 text-red-800' :
                            report.severity === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-green-100 text-green-800'
                          }`}>
                            {report.severity} priority
                          </span>
                        </div>
                      </div>

                      {(report.photos || []).length > 0 && (
                        <div className="ml-4">
                          <img
                            src={report.photos?.[0]?.image || report.photo}
                            alt="Resolved issue"
                            className="w-20 h-20 object-cover rounded-lg"
                          />
                        </div>
                      )}
                    </div>
                  </Card>
                ))}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default ResolvedIssues;