// Script to clear existing data and keep only shoaibshoaib@gmail.com reports
// Run this in browser console on the application

console.log('Clearing existing data and keeping only shoaibshoaib@gmail.com reports...');

// Clear localStorage
localStorage.removeItem('pothole-reporter-storage');

// Set fresh data with only shoaibshoaib@gmail.com
const freshData = {
  state: {
    authenticatedUsers: {
      'shoaibshoaib@gmail.com': {
        password: 'password',
        isGov: false,
        hasCompletedSetup: true,
        userData: {
          id: 'shoaib-user-1',
          name: 'Shoaib',
          age: 25,
          email: 'shoaibshoaib@gmail.com',
          points: 0,
          badge: 'none',
          reports: [],
          createdAt: new Date().toISOString()
        }
      },
      'gov@test.com': {
        password: 'password',
        isGov: true,
        hasCompletedSetup: true,
        userData: {
          id: 'test-gov-1',
          name: 'City Government',
          location: { lat: 40.7128, lng: -74.0060 },
          phone: '+1-555-0123',
          email: 'gov@test.com',
          createdAt: new Date().toISOString()
        }
      }
    },
    userEmail: null,
    reports: [],
    notifications: []
  },
  version: 0
};

localStorage.setItem('pothole-reporter-storage', JSON.stringify(freshData));

console.log('Data cleared successfully! Only shoaibshoaib@gmail.com user remains.');
console.log('Please refresh the page to see changes.');