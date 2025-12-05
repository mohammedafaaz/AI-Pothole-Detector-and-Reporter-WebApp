import React, { useState } from 'react';
import { Clock, Save } from 'lucide-react';
import { useAppStore } from '../store';
import Card from './ui/Card';
import Button from './ui/Button';

const WakeUpTimeSettings: React.FC = () => {
  const { currentUser, updateUserProfile } = useAppStore();
  const [wakeUpTime, setWakeUpTime] = useState(currentUser?.wakeUpTime || '07:00');
  const [isSaving, setIsSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      updateUserProfile({ wakeUpTime });
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (error) {
      console.error('Failed to save wake-up time:', error);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Card className="p-6">
      <div className="flex items-center mb-4">
        <Clock className="w-6 h-6 text-blue-600 mr-2" />
        <h2 className="text-xl font-bold text-gray-900">Wake-up Time Preference</h2>
      </div>
      
      <p className="text-gray-600 mb-6">
        Set your preferred wake-up time to help optimize garbage collection scheduling in your area.
      </p>

      <div className="space-y-4">
        <div>
          <label htmlFor="wakeUpTime" className="block text-sm font-medium text-gray-700 mb-2">
            Preferred Wake-up Time
          </label>
          <input
            type="time"
            id="wakeUpTime"
            value={wakeUpTime}
            onChange={(e) => setWakeUpTime(e.target.value)}
            className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        <Button
          onClick={handleSave}
          disabled={isSaving || wakeUpTime === currentUser?.wakeUpTime}
          className={`${saved ? 'bg-green-600 hover:bg-green-700' : ''}`}
        >
          {isSaving ? (
            'Saving...'
          ) : saved ? (
            <>
              <Save className="w-4 h-4 mr-2" />
              Saved!
            </>
          ) : (
            <>
              <Save className="w-4 h-4 mr-2" />
              Save Preference
            </>
          )}
        </Button>

        {saved && (
          <p className="text-sm text-green-600">
            Your wake-up time preference has been saved successfully!
          </p>
        )}
      </div>
    </Card>
  );
};

export default WakeUpTimeSettings;