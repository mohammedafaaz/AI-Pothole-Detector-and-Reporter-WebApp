import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { User, GovUser, Report, Badge, GroupedReport } from '../types';
import { groupReportsByLocation } from '../utils/reportGrouping';
import type { Language } from '../utils/translations';

export interface AppNotification {
  id: string;
  message: string;
  read: boolean;
  createdAt: Date;
  type?: 'resolved' | 'compliment' | 'info' | 'new_report';
  reportId?: string;
  govUserId?: string;
  complimentedBy?: string[];
  location?: { lat: number; lng: number };
  userId?: string;
}

interface AppState {
  isLoggedIn: boolean;
  isGovUser: boolean;
  currentUser: User | null;
  govUser: GovUser | null;
  userEmail: string | null;
  reports: Report[];
  groupedReports: GroupedReport[];
  userLocation: { lat: number; lng: number } | null;
  govLocation: { lat: number; lng: number } | null;
  hasCompletedSetup: boolean;
  language: Language;
  authenticatedUsers: {
    [email: string]: {
      password: string;
      isGov: boolean;
      hasCompletedSetup: boolean;
      userData: User | GovUser | null;
    };
  };
  notifications: AppNotification[];
  addNotification: (notif: Omit<AppNotification, 'id' | 'read' | 'createdAt' | 'complimentedBy'> & Partial<Pick<AppNotification, 'complimentedBy'>>) => void;
  markNotificationRead: (id: string) => void;
  markAllNotificationsRead: () => void;
  deleteNotification: (id: string) => void;
  sendComplimentToGov: (notifId: string, userId: string) => void;
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
  setGovLocation: (location: { lat: number; lng: number } | null) => void;
  getBadge: (points: number) => Badge;
  refreshGroupedReports: () => void;
  setLanguage: (lang: Language) => void;
}

const defaultAuthenticatedUsers = {
  'admin@gov.in': {
    password: 'admin@gov',
    isGov: true,
    hasCompletedSetup: true,
    userData: {
      id: 'gov-admin-1',
      name: 'Government Admin',
      location: { lat: 20.5937, lng: 78.9629 },
      phone: '',
      email: 'admin@gov.in',
      createdAt: new Date()
    } as GovUser
  }
};

export const useAppStore = create(
  persist<AppState>(
    (set, get) => ({
      isLoggedIn: false,
      isGovUser: false,
      currentUser: null,
      govUser: null,
      reports: [],
      groupedReports: [],
      userLocation: null,
      govLocation: null,
      hasCompletedSetup: false,
      userEmail: null,
      language: 'en' as Language,
      authenticatedUsers: defaultAuthenticatedUsers,
      notifications: [] as AppNotification[],
      
      addNotification: (notif: any) =>
        set((state: any) => ({
          notifications: [
            {
              id: `notif-${Date.now()}-${Math.random()}`,
              read: false,
              createdAt: new Date(),
              complimentedBy: notif.complimentedBy || [],
              userId: notif.userId,
              ...notif,
            },
            ...state.notifications,
          ],
        })),
        
      markNotificationRead: (id: string) =>
        set((state: any) => {
          const { currentUser, isGovUser, govUser } = state;
          return {
            notifications: state.notifications.map((n: any) =>
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
        set((state: any) => {
          const { currentUser, isGovUser, govUser } = state;
          return {
            notifications: state.notifications.map((n: any) =>
              (
                (!isGovUser && (!n.userId || n.userId === currentUser?.id)) ||
                (isGovUser && n.govUserId === govUser?.id)
              )
                ? { ...n, read: true }
                : n
            ),
          };
        }),

      deleteNotification: (id: string) =>
        set((state: any) => {
          const { currentUser, isGovUser, govUser } = state;
          return {
            notifications: state.notifications.filter((n: any) => {
              if (n.id !== id) return true;
              if (isGovUser && govUser) {
                return !(n.govUserId === govUser.id || (n.type === 'compliment' && n.govUserId === govUser.id));
              } else if (currentUser) {
                return !((n.userId === currentUser.id || !n.userId) && n.type !== 'compliment');
              }
              return true;
            }),
          };
        }),
        
      sendComplimentToGov: (notifId: string, userId: string) =>
        set((state: any) => ({
          notifications: state.notifications.map((n: any) =>
            n.id === notifId && n.type === 'resolved'
              ? { ...n, complimentedBy: [...(n.complimentedBy || []), userId] }
              : n
          ).concat(
            (() => {
              const notif = state.notifications.find((n: any) => n.id === notifId);
              if (notif && notif.govUserId) {
                return [{
                  id: `notif-${Date.now()}-${Math.random()}`,
                  message: `You received a compliment from a citizen for resolving a pothole.`,
                  read: false,
                  createdAt: new Date(),
                  type: 'compliment' as const,
                  govUserId: notif.govUserId,
                }];
              }
              return [];
            })()
          ),
        })),

      register: (email: string, password: string, isGov: boolean) => {
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

      signIn: (email: string, password: string) => {
        const state = get();
        const user = state.authenticatedUsers[email];

        if (!user || user.password !== password) {
          return false;
        }

        const newState: any = {
          isLoggedIn: true,
          isGovUser: user.isGov,
          hasCompletedSetup: user.hasCompletedSetup,
          userEmail: email,
          currentUser: !user.isGov ? user.userData as User : null,
          govUser: user.isGov ? user.userData as GovUser : null
        };

        if (user.isGov && user.userData) {
          const govData = user.userData as GovUser;
          newState.govLocation = govData.location;
        }

        set(newState);
        return true;
      },

      logout: () => {
        set({
          isLoggedIn: false,
          isGovUser: false,
          currentUser: null,
          govUser: null,
          userLocation: null,
          govLocation: null,
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
            const newState: any = {
              isLoggedIn: true,
              isGovUser: user.isGov,
              hasCompletedSetup: user.hasCompletedSetup,
              currentUser: !user.isGov ? user.userData as User : null,
              govUser: user.isGov ? user.userData as GovUser : null
            };

            if (user.isGov && user.userData) {
              const govData = user.userData as GovUser;
              newState.govLocation = govData.location;
            }

            set(newState);
          }
        }
      },

      createUser: (userData: any) => set((state: any) => {
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

      createGovUser: (userData: any) => set((state: any) => {
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
      
      addReport: (reportData: any) => set((state: any) => {
        console.log('🔄 Adding report:', { reportData, currentUser: state.currentUser?.name });
        console.log('📊 Current reports count before adding:', state.reports.length);

        if (!state.currentUser) {
          console.error('Cannot create report: User not logged in');
          return state;
        }

        const { userId, upvotedBy, downvotedBy, ...restReportData } = reportData;
        const newReport: Report = {
          id: `report-${Date.now()}`,
          userName: state.currentUser.name,
          userId: state.currentUser.id,
          createdAt: new Date(),
          upvotes: 0,
          downvotes: 0,
          upvotedBy: [],
          downvotedBy: [],
          verified: 'pending',
          fixingStatus: 'pending',
          reportType: 'pothole',
          ...restReportData,
        };

        const updatedReports = [newReport, ...state.reports];

        // Sync report id into currentUser.reports and authenticatedUsers
        const email = state.userEmail;
        let updatedCurrentUser = state.currentUser;
        let updatedAuthenticatedUsers = { ...state.authenticatedUsers };

        if (email && updatedCurrentUser) {
          const userReports = Array.isArray(updatedCurrentUser.reports) ? [...updatedCurrentUser.reports] : [];
          userReports.unshift(newReport.id);
          updatedCurrentUser = { ...updatedCurrentUser, reports: userReports };

          if (updatedAuthenticatedUsers[email]) {
            const userData = updatedAuthenticatedUsers[email].userData || {};
            const authUserReports = Array.isArray((userData as any).reports) ? [...(userData as any).reports] : [];
            authUserReports.unshift(newReport.id);
            updatedAuthenticatedUsers[email] = {
              ...updatedAuthenticatedUsers[email],
              userData: { ...(userData as any), reports: authUserReports },
            };
          }
        }

        // Helper: distance in km between two coords
        const distanceKm = (lat1: number, lon1: number, lat2: number, lon2: number) => {
          const toRad = (v: number) => (v * Math.PI) / 180;
          const R = 6371; // km
          const dLat = toRad(lat2 - lat1);
          const dLon = toRad(lon2 - lon1);
          const a =
            Math.sin(dLat / 2) * Math.sin(dLat / 2) +
            Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) *
            Math.sin(dLon / 2) * Math.sin(dLon / 2);
          const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
          return R * c;
        };

        // Create reporter notification
        const reporterNotif = {
          id: `notif-${Date.now()}-${Math.random()}`,
          message: `Report submitted successfully.`,
          read: false,
          createdAt: new Date(),
          type: 'new_report' as const,
          reportId: newReport.id,
          userId: state.currentUser.id,
          location: newReport.location,
        };

        // Gov notifications for nearby gov users (within 5km)
        const govNotifs: any[] = [];
        Object.keys(state.authenticatedUsers || {}).forEach((key: string) => {
          const auth = state.authenticatedUsers[key];
          if (auth && auth.isGov && auth.userData && (auth.userData as any).location) {
            const govLoc = (auth.userData as any).location;
            const reportLoc = newReport.location;
            try {
              const d = distanceKm(govLoc.lat, govLoc.lng, reportLoc.lat, reportLoc.lng);
              if (d <= 5) {
                govNotifs.push({
                  id: `notif-${Date.now()}-${Math.random()}`,
                  message: `New report near your jurisdiction: ${reportLoc.address || ''}`,
                  read: false,
                  createdAt: new Date(),
                  type: 'new_report' as const,
                  reportId: newReport.id,
                  govUserId: (auth.userData as any).id,
                  location: reportLoc,
                });
              }
            } catch (e) {
              // ignore malformed locations
            }
          }
        });

        const newNotifications = [reporterNotif, ...govNotifs, ...state.notifications];

        console.log('✅ Report added successfully:', {
          reportId: newReport.id,
          totalReports: updatedReports.length,
          reportType: newReport.reportType,
          addedNotifications: newNotifications.length - state.notifications.length,
        });

        return {
          reports: updatedReports,
          groupedReports: groupReportsByLocation(updatedReports),
          currentUser: updatedCurrentUser,
          authenticatedUsers: updatedAuthenticatedUsers,
          notifications: newNotifications,
        };
      }),
      
      deleteReport: (reportId: string) => set((state: any) => {
        const updatedReports = state.reports.filter((report: any) => report.id !== reportId);
        return {
          reports: updatedReports,
          groupedReports: groupReportsByLocation(updatedReports)
        };
      }),
      
      updateReport: (reportId: string, updates: any) => set((state: any) => {
        const updatedReports = state.reports.map((report: any) =>
          report.id === reportId ? { ...report, ...updates } : report
        );
        return { 
          reports: updatedReports, 
          groupedReports: groupReportsByLocation(updatedReports)
        };
      }),
      
      voteReport: (reportId: string, vote: 'up' | 'down') => {
        const currentUser = get().currentUser;
        if (!currentUser) return;

        set((state: any) => ({
          reports: state.reports.map((report: any) => {
            if (report.id !== reportId) return report;

            const hasUpvoted = report.upvotedBy?.includes(currentUser.id) || false;
            const hasDownvoted = report.downvotedBy?.includes(currentUser.id) || false;

            if (vote === 'up') {
              if (hasUpvoted) {
                return {
                  ...report,
                  upvotes: Math.max(0, report.upvotes - 1),
                  upvotedBy: report.upvotedBy?.filter((id: any) => id !== currentUser.id) || []
                };
              } else {
                return {
                  ...report,
                  upvotes: report.upvotes + 1,
                  downvotes: hasDownvoted ? Math.max(0, report.downvotes - 1) : report.downvotes,
                  upvotedBy: [...(report.upvotedBy || []), currentUser.id],
                  downvotedBy: hasDownvoted
                    ? report.downvotedBy?.filter((id: any) => id !== currentUser.id) || []
                    : report.downvotedBy || []
                };
              }
            } else {
              if (hasDownvoted) {
                return {
                  ...report,
                  downvotes: Math.max(0, report.downvotes - 1),
                  downvotedBy: report.downvotedBy?.filter((id: any) => id !== currentUser.id) || []
                };
              } else {
                return {
                  ...report,
                  downvotes: report.downvotes + 1,
                  upvotes: hasUpvoted ? Math.max(0, report.upvotes - 1) : report.upvotes,
                  downvotedBy: [...(report.downvotedBy || []), currentUser.id],
                  upvotedBy: hasUpvoted
                    ? report.upvotedBy?.filter((id: any) => id !== currentUser.id) || []
                    : report.upvotedBy || []
                };
              }
            }
          })
        }));
      },
      
      updateUserProfile: (updates: any) => set((state: any) => {
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
      
      updateGovProfile: (updates: any) => set((state: any) => {
        const email = state.userEmail;
        if (!email || !state.govUser) return {};

        const updatedGovUser = { ...state.govUser, ...updates };

        const newState: any = {
          govUser: updatedGovUser,
          authenticatedUsers: {
            ...state.authenticatedUsers,
            [email]: {
              ...state.authenticatedUsers[email]!,
              userData: updatedGovUser,
            },
          },
        };

        if (updates.location) {
          newState.govLocation = updates.location;
        }

        return newState;
      }),
      
      setUserLocation: (location: { lat: number; lng: number } | null) => set({ userLocation: location }),
      setGovLocation: (location: { lat: number; lng: number } | null) => set({ govLocation: location }),
      
      getBadge: (points: number) => {
        if (points >= 100) return 'gold';
        if (points >= 50) return 'silver';
        if (points >= 25) return 'bronze';
        return 'none';
      },

      refreshGroupedReports: () => set((state: any) => ({
        groupedReports: groupReportsByLocation(state.reports)
      })),

      setLanguage: (lang: Language) => set({ language: lang }),
    }),
    {
      name: 'pothole-reporter-storage',
      partialize: (state) => ({
        authenticatedUsers: state.authenticatedUsers,
        userEmail: state.userEmail,
        reports: state.reports,
        notifications: state.notifications,
        language: state.language,
      }) as unknown as AppState,
      merge: (persistedState: any, currentState: any): AppState => {
        const merged = {
          ...currentState,
          ...persistedState,
          authenticatedUsers: {
            ...defaultAuthenticatedUsers,
            ...persistedState?.authenticatedUsers,
          },
          reports: [],
          notifications: [],
          groupedReports: [],
        } as AppState;

        return merged;
      },
    }
  )
);