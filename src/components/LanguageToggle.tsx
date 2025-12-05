import React from 'react';
import { useAppStore } from '../store';
import type { Language } from '../utils/translations';

const LanguageToggle: React.FC = () => {
  const { language, setLanguage, isGovUser } = useAppStore();

  // Only show language toggle in user portal (not in government portal)
  if (isGovUser) {
    return null;
  }

  const toggleLanguage = () => {
    const newLanguage: Language = language === 'en' ? 'kn' : 'en';
    setLanguage(newLanguage);
  };

  return (
    <button
      onClick={toggleLanguage}
      className="inline-flex items-center px-3 py-2 rounded-lg bg-gradient-to-r from-blue-50 to-indigo-50 hover:from-blue-100 hover:to-indigo-100 text-sm font-medium text-blue-700 border border-blue-200 transition-all duration-200"
      title={language === 'en' ? 'Switch to Kannada' : 'Switch to English'}
    >
      {language === 'en' ? 'ಕನ್ನಡ' : 'English'}
    </button>
  );
};

export default LanguageToggle;
