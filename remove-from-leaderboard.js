// remove-from-leaderboard.js
// Run this in the browser console on the running app (after loading the app)
// It will remove users whose `userData.name` matches any name in the list
// from the persisted `pothole-reporter-storage` localStorage entry.

(function() {
  const NAMES_TO_REMOVE = [
    'John Citizen',
    'shoaib',
    'TEAM AURACODE',
    'AURACODE'
  ];

  const key = 'pothole-reporter-storage';
  const raw = localStorage.getItem(key);
  if (!raw) {
    console.warn('No persisted storage found under', key);
    return;
  }

  let data;
  try {
    data = JSON.parse(raw);
  } catch (err) {
    console.error('Failed to parse persisted storage:', err);
    return;
  }

  const state = data.state || data;
  if (!state || !state.authenticatedUsers) {
    console.error('Unexpected storage format — could not find state.authenticatedUsers');
    return;
  }

  const namesLower = NAMES_TO_REMOVE.map(n => n.toLowerCase());

  // Collect emails/ids to remove
  const emailsToRemove = [];
  const idsToRemove = [];

  Object.entries(state.authenticatedUsers).forEach(([email, entry]) => {
    try {
      const name = entry.userData && entry.userData.name ? String(entry.userData.name).toLowerCase() : '';
      if (namesLower.includes(name)) {
        emailsToRemove.push(email);
        if (entry.userData && entry.userData.id) {
          idsToRemove.push(entry.userData.id);
        }
      }
    } catch (e) { /* ignore malformed entries */ }
  });

  if (emailsToRemove.length === 0) {
    console.log('No matching users found in persisted storage for removal.');
    return;
  }

  console.log('Removing users (emails):', emailsToRemove);

  // Remove users from authenticatedUsers
  emailsToRemove.forEach(email => delete state.authenticatedUsers[email]);

  // Remove matching reports
  if (Array.isArray(state.reports)) {
    const before = state.reports.length;
    state.reports = state.reports.filter(r => {
      const userId = r.userId || r.userID || null;
      const userName = (r.userName || r.user || '').toString().toLowerCase();
      const emailMatches = emailsToRemove.includes((r.userEmail || '').toString());
      return !(idsToRemove.includes(userId) || emailMatches || namesLower.includes(userName));
    });
    console.log('Removed reports:', before - state.reports.length);
  }

  // Remove matching notifications
  if (Array.isArray(state.notifications)) {
    const before = state.notifications.length;
    state.notifications = state.notifications.filter(n => {
      const uid = n.userId || n.userID || null;
      const govId = n.govUserId || null;
      return !(idsToRemove.includes(uid) || idsToRemove.includes(govId));
    });
    console.log('Removed notifications:', before - state.notifications.length);
  }

  // Save back
  try {
    // Keep top-level structure consistent with how the app persists
    if (data.state) {
      data.state = state;
      localStorage.setItem(key, JSON.stringify(data));
    } else {
      localStorage.setItem(key, JSON.stringify(state));
    }
    console.log('Successfully updated persisted storage. Please refresh the page.');
  } catch (err) {
    console.error('Failed to write updated storage:', err);
  }
})();
