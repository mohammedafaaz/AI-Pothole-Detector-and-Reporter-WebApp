import { Report } from '../types';

// Generate random coordinates around a center point
export const getRandomLocation = (centerLat: number, centerLng: number, radiusKm: number) => {
  // Earth's radius in kilometers
  const earthRadius = 6371;
  
  // Convert radius from kilometers to radians
  const radiusInRadian = radiusKm / earthRadius;
  
  // Random angle
  const randomAngle = Math.random() * Math.PI * 2;
  
  // Random radius (using square root to ensure uniform distribution)
  const randomRadius = Math.sqrt(Math.random()) * radiusInRadian;
  
  // Convert center point to radians
  const centerLatRad = (centerLat * Math.PI) / 180;
  const centerLngRad = (centerLng * Math.PI) / 180;
  
  // Calculate new position
  const newLatRad = Math.asin(
    Math.sin(centerLatRad) * Math.cos(randomRadius) +
    Math.cos(centerLatRad) * Math.sin(randomRadius) * Math.cos(randomAngle)
  );
  
  const newLngRad = centerLngRad +
    Math.atan2(
      Math.sin(randomAngle) * Math.sin(randomRadius) * Math.cos(centerLatRad),
      Math.cos(randomRadius) - Math.sin(centerLatRad) * Math.sin(newLatRad)
    );
  
  // Convert back to degrees
  const newLat = (newLatRad * 180) / Math.PI;
  const newLng = (newLngRad * 180) / Math.PI;
  
  return { lat: newLat, lng: newLng };
};

// Calculate distance between two coordinates in kilometers
export const getDistanceFromLatLngInKm = (
  lat1: number, 
  lng1: number, 
  lat2: number, 
  lng2: number
) => {
  const earthRadius = 6371; // Radius of the earth in km
  const dLat = deg2rad(lat2 - lat1);
  const dLng = deg2rad(lng2 - lng1);
  const a = 
    Math.sin(dLat/2) * Math.sin(dLat/2) +
    Math.cos(deg2rad(lat1)) * Math.cos(deg2rad(lat2)) * 
    Math.sin(dLng/2) * Math.sin(dLng/2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a)); 
  const distance = earthRadius * c; // Distance in km
  return distance;
};

const deg2rad = (deg: number) => {
  return deg * (Math.PI/180);
};

// Generate mock reports
export const generateMockReports = (): Report[] => {
  const centerLat = 40.7128; // NYC latitude
  const centerLng = -74.0060; // NYC longitude
  
  const severityOptions = ['high', 'medium', 'low'] as const;
  const verificationOptions = ['pending', 'verified', 'rejected'] as const;
  const fixingOptions = ['pending', 'in_progress', 'resolved'] as const;
  
  const mockReports: Report[] = [];
  
  for (let i = 0; i < 20; i++) {
    const location = getRandomLocation(centerLat, centerLng, 10);
    const severity = severityOptions[Math.floor(Math.random() * severityOptions.length)];
    const verified = verificationOptions[Math.floor(Math.random() * verificationOptions.length)];
    const fixingStatus = fixingOptions[Math.floor(Math.random() * fixingOptions.length)];
    
    // Generate a past date within the last 30 days
    const createdAt = new Date();
    createdAt.setDate(createdAt.getDate() - Math.floor(Math.random() * 30));
    
    mockReports.push({
      id: `report-${i}`,
      userId: `user-${Math.floor(Math.random() * 10)}`,
      userName: `User ${Math.floor(Math.random() * 10)}`,
      createdAt,
      location: {
        lat: location.lat,
        lng: location.lng,
        address: `${Math.floor(Math.random() * 1000)} Main St, City`
      },
      photo: `https://picsum.photos/seed/${i}/500/300`,
      description: Math.random() > 0.3 ? `Pothole report #${i}` : undefined,
      severity,
      confidence: Math.random() * 0.5 + 0.5, // 0.5 to 1.0
      upvotes: Math.floor(Math.random() * 50),
      downvotes: Math.floor(Math.random() * 10),
      upvotedBy: [],
      downvotedBy: [],
      verified,
      fixingStatus
    });
  }
  
  return mockReports;
};