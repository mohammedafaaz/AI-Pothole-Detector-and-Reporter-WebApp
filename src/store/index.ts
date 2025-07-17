import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { User, GovUser, Report, Badge } from '../types';

interface Notification {
  id: string;
  message: string;
  read: boolean;
  createdAt: Date;
  type?: 'resolved' | 'compliment' | 'info' | 'new_report';
  reportId?: string;
  govUserId?: string;
  complimentedBy?: string[];
  location?: { lat: number; lng: number }; // Add location for map redirection
  userId?: string; // Owner of the notification
}

interface AppState {
  isLoggedIn: boolean;
  isGovUser: boolean;
  currentUser: User | null;
  govUser: GovUser | null;
  userEmail: string | null;
  reports: Report[];
  userLocation: { lat: number; lng: number } | null;
  hasCompletedSetup: boolean;
  authenticatedUsers: {
    [email: string]: {
      password: string;
      isGov: boolean;
      hasCompletedSetup: boolean;
      userData: User | GovUser | null;
    };
  };
  notifications: Notification[];
  addNotification: (notif: Omit<Notification, 'id' | 'read' | 'createdAt' | 'complimentedBy'> & Partial<Pick<Notification, 'complimentedBy'>>) => void;
  markNotificationRead: (id: string) => void;
  markAllNotificationsRead: () => void;
  sendComplimentToGov: (notifId: string, userId: string) => void;

  // Actions
  register: (email: string, password: string, isGov: boolean) => boolean;
  signIn: (email: string, password: string) => boolean;
  logout: () => void;
  initAuth: () => void;
  createUser: (userData: Omit<User, 'id' | 'reports' | 'points' | 'createdAt'>) => void;
  createGovUser: (userData: Omit<GovUser, 'id' | 'createdAt'>) => void;
  addReport: (report: Omit<Report, 'id' | 'userName' | 'createdAt' | 'upvotes' | 'downvotes' | 'verified' | 'fixingStatus'>) => void;
  deleteReport: (reportId: string) => void;
  updateReport: (reportId: string, updates: Partial<Report>) => void;
  voteReport: (reportId: string, vote: 'up' | 'down') => void;
  updateUserProfile: (updates: Partial<Omit<User, 'id' | 'reports' | 'points' | 'createdAt'>>) => void;
  updateGovProfile: (updates: Partial<Omit<GovUser, 'id' | 'createdAt'>>) => void;
  setUserLocation: (location: { lat: number; lng: number } | null) => void;
  getBadge: (points: number) => Badge;
}

export const useAppStore = create<AppState>()(
  persist(
    (set, get) => ({
      // Initial state
      isLoggedIn: false,
      isGovUser: false,
      currentUser: null,
      govUser: null,
      reports: [],
      userLocation: null,
      hasCompletedSetup: false,
      userEmail: null,
      authenticatedUsers: {},
      notifications: [],
      addNotification: (notif) =>
        set((state) => ({
          notifications: [
            {
              id: `notif-${Date.now()}-${Math.random()}`,
              read: false,
              createdAt: new Date(),
              complimentedBy: notif.complimentedBy || [],
              userId: notif.userId, // assign userId if provided
              ...notif,
            },
            ...state.notifications,
          ],
        })),
      markNotificationRead: (id) =>
        set((state) => {
          const { currentUser, isGovUser, govUser } = state;
          return {
            notifications: state.notifications.map((n) =>
              n.id === id &&
              (
                (!isGovUser && (!n.userId || n.userId === currentUser?.id)) ||
                (isGovUser && n.govUserId === govUser?.id)
              )
                ? { ...n, read: true }
                : n
            ),
          };
        }),
      markAllNotificationsRead: () =>
        set((state) => {
          const { currentUser, isGovUser, govUser } = state;
          return {
            notifications: state.notifications.map((n) =>
              (
                (!isGovUser && (!n.userId || n.userId === currentUser?.id)) ||
                (isGovUser && n.govUserId === govUser?.id)
              )
                ? { ...n, read: true }
                : n
            ),
          };
        }),
      sendComplimentToGov: (notifId, userId) =>
        set((state) => ({
          notifications: state.notifications.map((n) =>
            n.id === notifId && n.type === 'resolved'
              ? { ...n, complimentedBy: [...(n.complimentedBy || []), userId] }
              : n
          ).concat(
            // Send compliment notification to government user
            (() => {
              const notif = state.notifications.find(n => n.id === notifId);
              if (notif && notif.govUserId) {
                return [{
                  id: `notif-${Date.now()}-${Math.random()}`,
                  message: `You received a compliment from a citizen for resolving a pothole at ${notif.message.replace(/^Pothole at /, '').replace(' has been resolved!', '')}.`,
                  read: false,
                  createdAt: new Date(),
                  type: 'compliment',
                  govUserId: notif.govUserId,
                }];
              }
              return [];
            })()
          ),
        })),

      // Actions
      register: (email, password, isGov) => {
        const state = get();
        if (state.authenticatedUsers[email]) return false;

        set({
          authenticatedUsers: {
            ...state.authenticatedUsers,
            [email]: {
              password,
              isGov,
              hasCompletedSetup: false,
              userData: null
            }
          },
          isLoggedIn: true,
          isGovUser: isGov,
          userEmail: email
        });
        return true;
      },

      signIn: (email, password) => {
        const state = get();
        const user = state.authenticatedUsers[email];
        
        if (!user || user.password !== password) return false;
        
        set({
          isLoggedIn: true,
          isGovUser: user.isGov,
          hasCompletedSetup: user.hasCompletedSetup,
          userEmail: email,
          currentUser: !user.isGov ? user.userData as User : null,
          govUser: user.isGov ? user.userData as GovUser : null
        });

        return true;
      },

      logout: () => {
        set({
          isLoggedIn: false,
          isGovUser: false,
          currentUser: null,
          govUser: null,
          userLocation: null,
          hasCompletedSetup: false,
          userEmail: null
        });
      },

      initAuth: () => {
        const state = get();
        const email = state.userEmail;
        if (email) {
          const user = state.authenticatedUsers[email];
          if (user) {
            set({
              isLoggedIn: true,
              isGovUser: user.isGov,
              hasCompletedSetup: user.hasCompletedSetup,
              currentUser: !user.isGov ? user.userData as User : null,
              govUser: user.isGov ? user.userData as GovUser : null
            });
          }
        }
      },

      createUser: (userData) => set(state => {
        const email = state.userEmail;
        if (!email) return {};

        const updatedUser = {
          id: `user-${Date.now()}`,
          ...userData,
          points: 0,
          reports: [],
          badge: 'none' as Badge,
          createdAt: new Date()
        };

        return {
          currentUser: updatedUser,
          hasCompletedSetup: true,
          authenticatedUsers: {
            ...state.authenticatedUsers,
            [email]: {
              ...state.authenticatedUsers[email]!,
              hasCompletedSetup: true,
              userData: updatedUser
            }
          }
        };
      }),

      createGovUser: (userData) => set(state => {
        const email = state.userEmail;
        if (!email) return {};

        const updatedUser = {
          id: `gov-${Date.now()}`,
          ...userData,
          createdAt: new Date()
        };

        return {
          govUser: updatedUser,
          hasCompletedSetup: true,
          authenticatedUsers: {
            ...state.authenticatedUsers,
            [email]: {
              ...state.authenticatedUsers[email]!,
              hasCompletedSetup: true,
              userData: updatedUser
            }
          }
        };
      }),
      
      addReport: (reportData) => set((state) => {
        // Exclude userId and voting arrays from reportData to avoid duplicate keys
        // eslint-disable-next-line @typescript-eslint/no-unused-vars
        const { userId, upvotedBy, downvotedBy, ...restReportData } = reportData;
        const newReport: Report = {
          id: `report-${Date.now()}`,
          userName: state.currentUser?.name || 'Anonymous',
          userId: state.currentUser?.id || 'anonymous',
          createdAt: new Date(),
          upvotes: 0,
          downvotes: 0,
          upvotedBy: [],
          downvotedBy: [],
          verified: 'pending',
          fixingStatus: 'pending',
          ...restReportData,
        };
        const locationText = newReport.location.address
          ? newReport.location.address
          : `${newReport.location.lat.toFixed(4)}, ${newReport.location.lng.toFixed(4)}`;
        // Add a notification for all users except the reporter
        const allUserNotifications: Notification[] = Object.values(state.authenticatedUsers)
          .filter(u => u.userData && (u.userData as User).id !== newReport.userId && !u.isGov)
          .map(u => ({
            id: `notif-${Date.now()}-${Math.random()}`,
            message: `New pothole reported at ${locationText}.`,
            read: false,
            createdAt: new Date(),
            type: 'new_report',
            reportId: newReport.id,
            location: { lat: newReport.location.lat, lng: newReport.location.lng },
            userId: (u.userData as User).id,
          } as Notification));
        // No points awarded for just submitting - only when verified

        return {
          reports: [newReport, ...state.reports],
          notifications: [
            ...allUserNotifications,
            ...state.notifications,
          ],
        };
      }),
      
      deleteReport: (reportId) => set((state) => {
        const reportToDelete = state.reports.find(report => report.id === reportId);

        // If report was verified, deduct 1 point from the user
        if (reportToDelete && reportToDelete.verified === 'verified') {
          const reportOwnerEmail = Object.keys(state.authenticatedUsers).find(email => {
            const userData = state.authenticatedUsers[email]?.userData as User;
            return userData && userData.id === reportToDelete.userId;
          });

          if (reportOwnerEmail) {
            const reportOwner = state.authenticatedUsers[reportOwnerEmail]?.userData as User;
            if (reportOwner) {
              const newPoints = Math.max(0, (reportOwner.points || 0) - 1);
              let newBadge = reportOwner.badge;

              // Update badge based on points
              if (newPoints >= 100) {
                newBadge = 'gold';
              } else if (newPoints >= 50) {
                newBadge = 'silver';
              } else if (newPoints >= 25) {
                newBadge = 'bronze';
              } else {
                newBadge = 'none';
              }

              const updatedUser = {
                ...reportOwner,
                points: newPoints,
                badge: newBadge
              };

              return {
                reports: state.reports.filter(report => report.id !== reportId),
                currentUser: state.currentUser?.id === updatedUser.id ? updatedUser : state.currentUser,
                authenticatedUsers: {
                  ...state.authenticatedUsers,
                  [reportOwnerEmail]: {
                    ...state.authenticatedUsers[reportOwnerEmail]!,
                    userData: updatedUser,
                  },
                },
              };
            }
          }
        }

        return {
          reports: state.reports.filter(report => report.id !== reportId)
        };
      }),
      
      updateReport: (reportId, updates) => set((state) => {
        const updatedReports = state.reports.map(report => 
          report.id === reportId ? { ...report, ...updates } : report
        );
        let notifications = state.notifications;
        const updatedReport = updatedReports.find((r) => r.id === reportId);
        if (updatedReport) {
          const locationText = updatedReport.location.address
            ? updatedReport.location.address
            : `${updatedReport.location.lat.toFixed(4)}, ${updatedReport.location.lng.toFixed(4)}`;
          if (updates.verified === 'verified') {
            notifications = [
              {
                id: `notif-${Date.now()}-${Math.random()}`,
                message: `Report at ${locationText} has been verified by government.`,
                read: false,
                createdAt: new Date(),
                type: 'info',
                reportId,
                userId: updatedReport.userId,
              },
              ...notifications,
            ];
          }
          if (updates.verified === 'rejected') {
            notifications = [
              {
                id: `notif-${Date.now()}-${Math.random()}`,
                message: `Report at ${locationText} was rejected by government.`,
                read: false,
                createdAt: new Date(),
                type: 'info',
                reportId,
                userId: updatedReport.userId,
              },
              ...notifications,
            ];
          }
          if (updates.fixingStatus === 'in_progress') {
            notifications = [
              {
                id: `notif-${Date.now()}-${Math.random()}`,
                message: `Fixing started for pothole at ${locationText}.`,
                read: false,
                createdAt: new Date(),
                type: 'info',
                reportId,
                userId: updatedReport.userId,
              },
              ...notifications,
            ];
          }
          if (updates.fixingStatus === 'resolved') {
            notifications = [
              {
                id: `notif-${Date.now()}-${Math.random()}`,
                message: `Pothole at ${locationText} has been resolved!`,
                read: false,
                createdAt: new Date(),
                type: 'resolved',
                reportId,
                govUserId: state.govUser?.id,
                complimentedBy: [],
                userId: updatedReport.userId,
              },
              ...notifications,
            ];
          }
        }

        if (updates.verified === 'verified' && updatedReport) {
          // Find the user who submitted this report and award 1 point
          const reportOwnerEmail = Object.keys(state.authenticatedUsers).find(email => {
            const userData = state.authenticatedUsers[email]?.userData as User;
            return userData && userData.id === updatedReport.userId;
          });

          if (reportOwnerEmail) {
            const reportOwner = state.authenticatedUsers[reportOwnerEmail]?.userData as User;
            if (reportOwner) {
              const newPoints = (reportOwner.points || 0) + 1;
              let newBadge = reportOwner.badge;

              // Update badge based on points
              if (newPoints >= 100) {
                newBadge = 'gold';
              } else if (newPoints >= 50) {
                newBadge = 'silver';
              } else if (newPoints >= 25) {
                newBadge = 'bronze';
              }

              const updatedUser = {
                ...reportOwner,
                points: newPoints,
                badge: newBadge
              };

              return {
                reports: updatedReports,
                currentUser: state.currentUser?.id === updatedUser.id ? updatedUser : state.currentUser,
                authenticatedUsers: {
                  ...state.authenticatedUsers,
                  [reportOwnerEmail]: {
                    ...state.authenticatedUsers[reportOwnerEmail]!,
                    userData: updatedUser,
                  },
                },
                notifications,
              };
            }
          }
        }

        return { reports: updatedReports, notifications };
      }),
      
      voteReport: (reportId, vote) => {
        const currentUser = get().currentUser;
        if (!currentUser) return;

        set((state) => ({
          reports: state.reports.map(report => {
            if (report.id !== reportId) return report;

            const hasUpvoted = report.upvotedBy?.includes(currentUser.id) || false;
            const hasDownvoted = report.downvotedBy?.includes(currentUser.id) || false;

            if (vote === 'up') {
              if (hasUpvoted) {
                // Remove upvote
                return {
                  ...report,
                  upvotes: Math.max(0, report.upvotes - 1),
                  upvotedBy: report.upvotedBy?.filter(id => id !== currentUser.id) || []
                };
              } else {
                // Add upvote and remove downvote if exists
                return {
                  ...report,
                  upvotes: report.upvotes + 1,
                  downvotes: hasDownvoted ? Math.max(0, report.downvotes - 1) : report.downvotes,
                  upvotedBy: [...(report.upvotedBy || []), currentUser.id],
                  downvotedBy: hasDownvoted
                    ? report.downvotedBy?.filter(id => id !== currentUser.id) || []
                    : report.downvotedBy || []
                };
              }
            } else {
              if (hasDownvoted) {
                // Remove downvote
                return {
                  ...report,
                  downvotes: Math.max(0, report.downvotes - 1),
                  downvotedBy: report.downvotedBy?.filter(id => id !== currentUser.id) || []
                };
              } else {
                // Add downvote and remove upvote if exists
                return {
                  ...report,
                  downvotes: report.downvotes + 1,
                  upvotes: hasUpvoted ? Math.max(0, report.upvotes - 1) : report.upvotes,
                  downvotedBy: [...(report.downvotedBy || []), currentUser.id],
                  upvotedBy: hasUpvoted
                    ? report.upvotedBy?.filter(id => id !== currentUser.id) || []
                    : report.upvotedBy || []
                };
              }
            }
          })
        }));
      },
      
      updateUserProfile: (updates) => set((state) => {
        const email = state.userEmail;
        if (!email || !state.currentUser) return {};

        const updatedUser = { ...state.currentUser, ...updates };

        return {
          currentUser: updatedUser,
          authenticatedUsers: {
            ...state.authenticatedUsers,
            [email]: {
              ...state.authenticatedUsers[email]!,
              userData: updatedUser,
            },
          },
        };
      }),
      
      updateGovProfile: (updates) => set((state) => {
        const email = state.userEmail;
        if (!email || !state.govUser) return {};

        const updatedGovUser = { ...state.govUser, ...updates };

        return {
          govUser: updatedGovUser,
          authenticatedUsers: {
            ...state.authenticatedUsers,
            [email]: {
              ...state.authenticatedUsers[email]!,
              userData: updatedGovUser,
            },
          },
        };
      }),
      
      setUserLocation: (location) => set({ userLocation: location }),
      
      getBadge: (points) => {
        if (points >= 100) return 'gold';
        if (points >= 50) return 'silver';
        if (points >= 25) return 'bronze';
        return 'none';
      },
    }),
    {
      name: 'pothole-reporter-storage',
      partialize: (state) => ({
        authenticatedUsers: state.authenticatedUsers,
        userEmail: state.userEmail,
        reports: state.reports,
        notifications: state.notifications,
      }),
    }
  )
);