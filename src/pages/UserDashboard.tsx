import React from 'react';
import { Trophy, Star, Medal, Users, TrendingUp } from 'lucide-react';
import { useAppStore } from '../store';
import MobileNavigation from '../components/MobileNavigation';
import Card from '../components/ui/Card';

const UserDashboard: React.FC = () => {
  const { currentUser } = useAppStore();

  if (!currentUser) {
    return <div>Loading...</div>;
  }

  // Only show the current logged-in user in the leaderboard
  const allUsers = currentUser ? [currentUser] : [];

  const getBadgeIcon = (badge: string) => {
    switch (badge) {
      case 'gold': return <Trophy className="w-5 h-5 text-yellow-500" />;
      case 'silver': return <Medal className="w-5 h-5 text-gray-400" />;
      case 'bronze': return <Star className="w-5 h-5 text-orange-500" />;
      default: return <Users className="w-5 h-5 text-gray-400" />;
    }
  };

  const getBadgeColor = (badge: string) => {
    switch (badge) {
      case 'gold': return 'bg-yellow-50 text-yellow-700 border-yellow-200';
      case 'silver': return 'bg-gray-50 text-gray-700 border-gray-200';
      case 'bronze': return 'bg-orange-50 text-orange-700 border-orange-200';
      default: return 'bg-gray-50 text-gray-600 border-gray-200';
    }
  };

  // Find current user's rank
  const currentUserRank = allUsers.findIndex(user => user.id === currentUser.id) + 1;

  return (
    <div className="min-h-screen bg-gray-50">
      <MobileNavigation />

      {/* Header */}
      <div className="bg-white border-b border-gray-200 md:pl-64 pt-0 md:pt-0 mt-0">
        <div className="flex items-center justify-center py-1 md:py-3">
          <div className="flex items-center">
            <div className="w-10 h-10 md:w-16 md:h-16 flex items-center justify-center">
              <img
                src="/logo2.jpg"
                alt="FixMyPothole.AI Logo"
                className="w-10 h-10 md:w-16 md:h-16 object-contain"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Desktop sidebar spacing */}
      <div className="md:pl-64">
        <div className="p-4 md:p-6">
          <div className="mb-6">
            <h1 className="text-2xl font-bold text-gray-900 mb-2">Dashboard</h1>
            <p className="text-gray-600">Track your progress and see how you rank among other citizens</p>
          </div>

          {/* User Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <Card className="p-6">
              <div className="flex items-center">
                <div className="p-3 bg-blue-100 rounded-lg">
                  <TrendingUp className="w-6 h-6 text-blue-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Total Points</p>
                  <p className="text-2xl font-bold text-gray-900">{currentUser.points}</p>
                </div>
              </div>
            </Card>

            <Card className="p-6">
              <div className="flex items-center">
                <div className="p-3 bg-green-100 rounded-lg">
                  <Trophy className="w-6 h-6 text-green-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Current Rank</p>
                  <p className="text-2xl font-bold text-gray-900">#{currentUserRank}</p>
                </div>
              </div>
            </Card>

            <Card className="p-6">
              <div className="flex items-center">
                <div className={`p-3 rounded-lg ${getBadgeColor(currentUser.badge)}`}>
                  {getBadgeIcon(currentUser.badge)}
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Badge Level</p>
                  <p className="text-2xl font-bold text-gray-900 capitalize">{currentUser.badge || 'None'}</p>
                </div>
              </div>
            </Card>
          </div>

          {/* Leaderboard */}
          <Card className="p-6">
            <div className="flex items-center mb-6">
              <Trophy className="w-6 h-6 text-yellow-500 mr-2" />
              <h2 className="text-xl font-bold text-gray-900">Leaderboard</h2>
            </div>

            {allUsers.length === 0 ? (
              <div className="text-center py-8">
                <Users className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Other Users Yet</h3>
                <p className="text-gray-600">
                  You're the first user! Invite others to join and compete on the leaderboard.
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {allUsers.slice(0, 10).map((user, index) => (
                  <div
                    key={user.id}
                    className={`flex items-center justify-between p-4 rounded-lg border ${
                      user.id === currentUser.id 
                        ? 'bg-blue-50 border-blue-200' 
                        : 'bg-gray-50 border-gray-200'
                    }`}
                  >
                    <div className="flex items-center">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                        index === 0 ? 'bg-yellow-100 text-yellow-800' :
                        index === 1 ? 'bg-gray-100 text-gray-800' :
                        index === 2 ? 'bg-orange-100 text-orange-800' :
                        'bg-gray-100 text-gray-600'
                      }`}>
                        {index + 1}
                      </div>
                      <div className="ml-3">
                        <p className={`font-medium ${
                          user.id === currentUser.id ? 'text-blue-900' : 'text-gray-900'
                        }`}>
                          {user.name} {user.id === currentUser.id && '(You)'}
                        </p>
                      </div>
                    </div>
                    
                    <div className="flex items-center">
                      <span className={`font-bold mr-2 ${
                        user.id === currentUser.id ? 'text-blue-900' : 'text-gray-900'
                      }`}>
                        {user.points} pts
                      </span>
                      {getBadgeIcon(user.badge)}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
};

export default UserDashboard;