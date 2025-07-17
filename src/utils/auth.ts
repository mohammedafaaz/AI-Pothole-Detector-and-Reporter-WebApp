interface StoredUser {
  id: string;
  email: string;
  password: string;
  isGov: boolean;
  hasCompletedSetup: boolean;
  profile?: {
    name: string;
    age?: number;
    phone?: string;
    location?: { lat: number; lng: number; };
  };
}

const USERS_KEY = 'pothole_reporter_users';

export const getStoredUsers = (): StoredUser[] => {
  const users = localStorage.getItem(USERS_KEY);
  return users ? JSON.parse(users) : [];
};

export const saveUser = (user: StoredUser) => {
  const users = getStoredUsers();
  users.push(user);
  localStorage.setItem(USERS_KEY, JSON.stringify(users));
};

export const findUser = (email: string): StoredUser | undefined => {
  const users = getStoredUsers();
  return users.find(u => u.email === email);
};

export const updateUserProfile = (email: string, profile: StoredUser['profile']) => {
  const users = getStoredUsers();
  const userIndex = users.findIndex(u => u.email === email);
  if (userIndex >= 0) {
    users[userIndex].profile = profile;
    users[userIndex].hasCompletedSetup = true;
    localStorage.setItem(USERS_KEY, JSON.stringify(users));
  }
};
