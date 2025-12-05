import React, { useState } from 'react';
import { AlertTriangle, Save } from 'lucide-react';
import { useAppStore } from '../store';
import Button from './ui/Button';

interface SeverityControlProps {
  reportId: string;
  currentSeverity: 'high' | 'medium' | 'low';
  onClose: () => void;
}

const SeverityControl: React.FC<SeverityControlProps> = ({ reportId, currentSeverity, onClose }) => {
  const { updateReport } = useAppStore();
  const [selectedSeverity, setSelectedSeverity] = useState<'high' | 'medium' | 'low'>(currentSeverity);
  const [isSaving, setIsSaving] = useState(false);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      updateReport(reportId, { severity: selectedSeverity });
      onClose();
    } catch (error) {
      console.error('Failed to update severity:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const getSeverityColor = (severity: 'high' | 'medium' | 'low') => {
    switch (severity) {
      case 'high': return 'bg-red-100 border-red-300 text-red-800';
      case 'medium': return 'bg-yellow-100 border-yellow-300 text-yellow-800';
      case 'low': return 'bg-green-100 border-green-300 text-green-800';
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-[10001] flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
        <div className="flex items-center mb-4">
          <AlertTriangle className="w-6 h-6 text-orange-600 mr-2" />
          <h3 className="text-lg font-semibold text-gray-900">Override Severity Level</h3>
        </div>

        <p className="text-gray-600 mb-6">
          Manually adjust the severity level of this civic issue based on your assessment.
        </p>

        <div className="space-y-3 mb-6">
          {(['high', 'medium', 'low'] as const).map((severity) => (
            <label key={severity} className="flex items-center cursor-pointer">
              <input
                type="radio"
                name="severity"
                value={severity}
                checked={selectedSeverity === severity}
                onChange={(e) => setSelectedSeverity(e.target.value as 'high' | 'medium' | 'low')}
                className="sr-only"
              />
              <div className={`
                flex items-center w-full p-3 border-2 rounded-lg transition-all
                ${selectedSeverity === severity 
                  ? `${getSeverityColor(severity)} border-current` 
                  : 'bg-gray-50 border-gray-200 hover:border-gray-300'
                }
              `}>
                <div className={`
                  w-4 h-4 rounded-full border-2 mr-3 flex items-center justify-center
                  ${selectedSeverity === severity ? 'border-current' : 'border-gray-300'}
                `}>
                  {selectedSeverity === severity && (
                    <div className="w-2 h-2 rounded-full bg-current" />
                  )}
                </div>
                <div>
                  <div className="font-medium capitalize">{severity} Priority</div>
                  <div className="text-sm opacity-75">
                    {severity === 'high' && 'Requires immediate attention'}
                    {severity === 'medium' && 'Should be addressed soon'}
                    {severity === 'low' && 'Can be scheduled for later'}
                  </div>
                </div>
              </div>
            </label>
          ))}
        </div>

        <div className="flex gap-3">
          <Button
            variant="secondary"
            onClick={onClose}
            className="flex-1"
          >
            Cancel
          </Button>
          <Button
            onClick={handleSave}
            disabled={isSaving || selectedSeverity === currentSeverity}
            className="flex-1"
          >
            {isSaving ? (
              'Saving...'
            ) : (
              <>
                <Save className="w-4 h-4 mr-2" />
                Update Severity
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
};

export default SeverityControl;