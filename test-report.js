// Simple test to check if reports are being added
console.log('Testing report submission...');

// This would be run in browser console to test
const testReport = {
  userId: 'test-user',
  photos: [{
    image: 'data:image/jpeg;base64,test',
    detections: []
  }],
  photo: 'data:image/jpeg;base64,test',
  description: 'Test pothole report',
  severity: 'medium',
  confidence: 0.8,
  location: {
    lat: 40.7128,
    lng: -74.0060,
    address: 'Test Location'
  },
  reportType: 'pothole'
};

// To test in browser console:
// 1. Open browser dev tools
// 2. Go to Console tab
// 3. Type: window.testAddReport = testReport; 
// 4. Then: useAppStore.getState().addReport(window.testAddReport);
// 5. Check: useAppStore.getState().reports.length