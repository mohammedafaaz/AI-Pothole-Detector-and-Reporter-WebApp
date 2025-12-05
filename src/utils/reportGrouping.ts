import { Report, GroupedReport } from '../types';

// Function to calculate distance between two coordinates in meters
function calculateDistance(lat1: number, lng1: number, lat2: number, lng2: number): number {
  const R = 6371e3; // Earth's radius in meters
  const φ1 = lat1 * Math.PI / 180;
  const φ2 = lat2 * Math.PI / 180;
  const Δφ = (lat2 - lat1) * Math.PI / 180;
  const Δλ = (lng2 - lng1) * Math.PI / 180;

  const a = Math.sin(Δφ / 2) * Math.sin(Δφ / 2) +
    Math.cos(φ1) * Math.cos(φ2) *
    Math.sin(Δλ / 2) * Math.sin(Δλ / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

  return R * c;
}

// Group reports by proximity (within 50 meters)
export function groupReportsByLocation(reports: Report[], proximityThreshold = 50): GroupedReport[] {
  const grouped: GroupedReport[] = [];
  const processed = new Set<string>();

  reports.forEach(report => {
    if (processed.has(report.id)) return;

    const nearbyReports = reports.filter(otherReport => {
      if (processed.has(otherReport.id) || report.id === otherReport.id) return false;
      
      const distance = calculateDistance(
        report.location.lat,
        report.location.lng,
        otherReport.location.lat,
        otherReport.location.lng
      );
      
      return distance <= proximityThreshold && report.reportType === otherReport.reportType;
    });

    const allReports = [report, ...nearbyReports];
    allReports.forEach(r => processed.add(r.id));

    // Determine group severity (highest severity wins)
    const severityOrder = { high: 3, medium: 2, low: 1 };
    const groupSeverity = allReports.reduce<'high' | 'medium' | 'low'>((highest, r) => 
      severityOrder[r.severity] > severityOrder[highest] ? r.severity : highest, 
      'low'
    );

    // Determine group status (most critical status wins)
    const statusOrder = { rejected: 0, resolved: 1, in_progress: 2, pending: 3 };
    const groupStatus = allReports.reduce<'pending' | 'in_progress' | 'resolved' | 'rejected'>((mostCritical, r) => 
      statusOrder[r.fixingStatus] > statusOrder[mostCritical] ? r.fixingStatus : mostCritical,
      'resolved'
    );

    // Determine group verification (most critical verification wins)
    const verificationOrder = { rejected: 0, verified: 1, pending: 2 };
    const groupVerification = allReports.reduce<'pending' | 'verified' | 'rejected'>((mostCritical, r) => 
      verificationOrder[r.verified] > verificationOrder[mostCritical] ? r.verified : mostCritical,
      'verified'
    );

    grouped.push({
      id: `group-${report.id}`,
      location: report.location,
      reports: allReports.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()),
      severity: groupSeverity,
      verified: groupVerification,
      fixingStatus: groupStatus,
      reportType: report.reportType,
      createdAt: new Date(Math.min(...allReports.map(r => new Date(r.createdAt).getTime()))),
      updatedAt: new Date(Math.max(...allReports.map(r => new Date(r.createdAt).getTime())))
    });
  });

  return grouped.sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime());
}