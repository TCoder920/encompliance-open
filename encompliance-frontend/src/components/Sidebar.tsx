/*
  Description: Sidebar component. Provides navigation links and quick access to main application features.
  Purpose: Offers a persistent navigation menu for authenticated users to access different sections of the app.
  Enhanced with freemium functionality to show tier badges for premium features.
*/
import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { getTierFromSubscriptionStatus } from '../utils/tiers';
import { isPremiumFeature, canUseFeature, canUseFeatureWithRole } from '../utils/accessControl';
import { 
  FileText, 
  Settings, 
  MessageSquare, 
  Download, 
  Calendar, 
  ChevronDown, 
  ChevronRight, 
  StickyNote,
  BarChart3,
  Home,
  Menu,
  LayoutDashboard,
  Search,
  Shield,
  Mail,
  GraduationCap,
  Users,
  BookOpen,
  ClipboardList,
  ClipboardCheck,
  Building,
  CalendarCheck
} from 'lucide-react';

const Sidebar: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated, user } = useAuth();
  const [trainingExpanded, setTrainingExpanded] = useState(location.pathname.startsWith('/training'));

  const userTier = getTierFromSubscriptionStatus(user?.subscription_status);

  return (
    <aside className="w-64 bg-navy-blue dark:bg-dark-surface text-white h-[calc(100vh-4rem)] flex flex-col border-r border-gray-700">
      {/* Main Navigation */}
      <div className="flex-1 overflow-y-auto">
        <nav className="flex flex-col space-y-2 p-4">
          <button 
            onClick={() => navigate('/')}
            className={`flex items-center space-x-2 p-3 rounded-lg transition-colors ${
              location.pathname === '/' 
                ? 'bg-white/10 text-blue-300' 
                : 'hover:bg-white/5 hover:text-blue-300'
            }`}
          >
            <Home className="h-5 w-5" />
            <span>Home</span>
          </button>

          {isAuthenticated && (
            <>
              <button 
                onClick={() => navigate('/dashboard')}
                className={`flex items-center space-x-2 p-3 rounded-lg transition-colors ${
                  location.pathname === '/dashboard' 
                    ? 'bg-white/10 text-blue-300' 
                    : 'hover:bg-white/5 hover:text-blue-300'
                }`}
              >
                <LayoutDashboard className="h-5 w-5" />
                <span>Dashboard</span>
              </button>

              {/* Facility Overview - Only for Pro users */}
              {user?.subscription_status === 'pro' && (
                <button 
                  onClick={() => navigate('/facility')}
                  className={`flex items-center space-x-2 p-3 rounded-lg transition-colors ${
                    location.pathname === '/facility' 
                      ? 'bg-white/10 text-blue-300' 
                      : 'hover:bg-white/5 hover:text-blue-300'
                  }`}
                >
                  <Building className="h-5 w-5" />
                  <span>Facility Overview</span>
                </button>
              )}
              
              <button 
                onClick={() => navigate('/search')}
                className={`flex items-center space-x-2 p-3 rounded-lg transition-colors w-full ${
                  location.pathname === '/search' 
                    ? 'bg-white/10 text-blue-300' 
                    : 'hover:bg-white/5 hover:text-blue-300'
                }`}
              >
                <Search className="h-5 w-5" />
                <span>Compliance Assistant</span>
              </button>

              {/* Training & Certification Section */}
              <div>
                <button 
                  onClick={() => {
                    setTrainingExpanded(!trainingExpanded);
                    if (!trainingExpanded) {
                      navigate('/training');
                    }
                  }}
                  className={`flex items-center justify-between w-full p-3 rounded-lg transition-colors ${
                    location.pathname.startsWith('/training') 
                      ? 'bg-white/10 text-blue-300' 
                      : 'hover:bg-white/5 hover:text-blue-300'
                  }`}
                >
                  <div className="flex items-center space-x-2 min-w-0 flex-1">
                    <GraduationCap className="h-5 w-5 flex-shrink-0" />
                    <span className="truncate">Training & Certification</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    {isPremiumFeature('training_certification') && !canUseFeature(userTier, 'training_certification') && (
                      <span className="text-xs text-yellow-400 whitespace-nowrap">
                        Subscription Required
                      </span>
                    )}
                    {trainingExpanded ? (
                      <ChevronDown className="h-4 w-4" />
                    ) : (
                      <ChevronRight className="h-4 w-4" />
                    )}
                  </div>
                </button>
                
                {trainingExpanded && (
                  <div className="ml-4 mt-2 space-y-1">
                    <button 
                      onClick={() => navigate('/training')}
                      className={`flex items-center space-x-2 p-2 rounded-lg transition-colors w-full text-sm ${
                        location.pathname === '/training' 
                          ? 'bg-white/10 text-blue-300' 
                          : 'hover:bg-white/5 hover:text-blue-300'
                      }`}
                    >
                      <LayoutDashboard className="h-4 w-4" />
                      <span>Overview</span>
                    </button>
                    
                    <button 
                      onClick={() => navigate('/training/programs')}
                      className={`flex items-center space-x-2 p-2 rounded-lg transition-colors w-full text-sm ${
                        location.pathname === '/training/programs' 
                          ? 'bg-white/10 text-blue-300' 
                          : 'hover:bg-white/5 hover:text-blue-300'
                      }`}
                    >
                      <BookOpen className="h-4 w-4" />
                      <span>Training Programs</span>
                    </button>
                    
                    {/* Staff Management - Only show for facility administrators */}
                    {user?.user_role !== 'team_member' && (
                      <button 
                        onClick={() => navigate('/training/staff')}
                        className={`flex items-center space-x-2 p-2 rounded-lg transition-colors w-full text-sm ${
                          location.pathname === '/training/staff' 
                            ? 'bg-white/10 text-blue-300' 
                            : 'hover:bg-white/5 hover:text-blue-300'
                        }`}
                      >
                        <Users className="h-4 w-4" />
                        <span>Staff Management</span>
                      </button>
                    )}
                    
                    <button 
                      onClick={() => navigate('/training/assignments')}
                      className={`flex items-center space-x-2 p-2 rounded-lg transition-colors w-full text-sm ${
                        location.pathname === '/training/assignments' 
                          ? 'bg-white/10 text-blue-300' 
                          : 'hover:bg-white/5 hover:text-blue-300'
                      }`}
                    >
                      <ClipboardList className="h-4 w-4" />
                      <span>Assignments</span>
                    </button>
                  </div>
                )}
              </div>

              {/* Task Management - Only show for facility administrators and free users (who see upgrade prompt) */}
              {user?.user_role !== 'team_member' && (
                <button 
                  onClick={() => navigate('/tasks')}
                  className={`flex items-center justify-between p-3 rounded-lg transition-colors ${
                    location.pathname.startsWith('/tasks') 
                      ? 'bg-white/10 text-blue-300' 
                      : 'hover:bg-white/5 hover:text-blue-300'
                  }`}
                >
                  <div className="flex items-center space-x-2 min-w-0 flex-1">
                    <ClipboardCheck className="h-5 w-5 flex-shrink-0" />
                    <span className="truncate">Task Management</span>
                  </div>
                  {isPremiumFeature('task_management') && !canUseFeature(userTier, 'task_management') && (
                    <span className="text-xs text-yellow-400 whitespace-nowrap ml-2">
                      Subscription Required
                    </span>
                  )}
                </button>
              )}

              <button 
                onClick={() => navigate('/notes')}
                className={`flex items-center justify-between p-3 rounded-lg transition-colors ${
                  location.pathname.startsWith('/notes') 
                    ? 'bg-white/10 text-blue-300' 
                    : 'hover:bg-white/5 hover:text-blue-300'
                }`}
              >
                <div className="flex items-center space-x-2 min-w-0 flex-1">
                  <StickyNote className="h-5 w-5 flex-shrink-0" />
                  <span className="truncate">Notes</span>
                </div>
                {isPremiumFeature('notes') && !canUseFeature(userTier, 'notes') && (
                  <span className="text-xs text-yellow-400 whitespace-nowrap ml-2">
                    Subscription Required
                  </span>
                )}
              </button>

              <button 
                onClick={() => navigate('/calendar')}
                className={`flex items-center justify-between p-3 rounded-lg transition-colors ${
                  location.pathname.startsWith('/calendar') 
                    ? 'bg-white/10 text-blue-300' 
                    : 'hover:bg-white/5 hover:text-blue-300'
                }`}
              >
                <div className="flex items-center space-x-2 min-w-0 flex-1">
                  <Calendar className="h-5 w-5 flex-shrink-0" />
                  <span className="truncate">Calendar</span>
                </div>
                {isPremiumFeature('calendar') && !canUseFeature(userTier, 'calendar') && (
                  <span className="text-xs text-yellow-400 whitespace-nowrap ml-2">
                    Subscription Required
                  </span>
                )}
              </button>

              <button 
                onClick={() => navigate('/activities')}
                className={`flex items-center justify-between p-3 rounded-lg transition-colors ${
                  location.pathname.startsWith('/activities') 
                    ? 'bg-white/10 text-blue-300' 
                    : 'hover:bg-white/5 hover:text-blue-300'
                }`}
              >
                <div className="flex items-center space-x-2 min-w-0 flex-1">
                  <CalendarCheck className="h-5 w-5 flex-shrink-0" />
                  <span className="truncate">Activities</span>
                </div>
                {/* Optional: Add premium feature check if activities are premium */}
              </button>

              {/* Data Export - Only show for facility administrators and free users (who see upgrade prompt) */}
              {user?.user_role !== 'team_member' && (
                <button 
                  onClick={() => navigate('/export')}
                  className={`flex items-center justify-between p-3 rounded-lg transition-colors ${
                    location.pathname.startsWith('/export') 
                      ? 'bg-white/10 text-blue-300' 
                      : canUseFeatureWithRole(userTier, 'data_export', user?.user_role, user?.subscription_status)
                        ? 'hover:bg-white/5 hover:text-blue-300'
                        : 'hover:bg-white/5 hover:text-yellow-300 cursor-pointer'
                  }`}
                  title={!canUseFeatureWithRole(userTier, 'data_export', user?.user_role, user?.subscription_status) ? 'Subscription required for data export' : 'Export your data'}
                >
                  <div className="flex items-center space-x-2 min-w-0 flex-1">
                    <Download className="h-5 w-5 flex-shrink-0" />
                    <span className="truncate">Data Export</span>
                  </div>
                  {!canUseFeatureWithRole(userTier, 'data_export', user?.user_role, user?.subscription_status) && (
                    <span className="text-xs text-yellow-400 whitespace-nowrap ml-2">
                      Subscription Required
                    </span>
                  )}
                </button>
              )}


            </>
          )}
        </nav>
      </div>

      {/* Footer Links for Authenticated Users */}
      {isAuthenticated && (
        <div className="shrink-0 p-4 border-t border-gray-700">
          <nav className="flex flex-col space-y-2">
            <button 
              onClick={() => navigate('/terms')}
              className="flex items-center space-x-2 p-2 text-sm text-gray-300 hover:text-white transition-colors"
            >
              <FileText className="h-4 w-4" />
              <span>Terms of Service</span>
            </button>
            <button 
              onClick={() => navigate('/privacy')}
              className="flex items-center space-x-2 p-2 text-sm text-gray-300 hover:text-white transition-colors"
            >
              <Shield className="h-4 w-4" />
              <span>Privacy Policy</span>
            </button>
            <button 
              onClick={() => navigate('/contact')}
              className="flex items-center space-x-2 p-2 text-sm text-gray-300 hover:text-white transition-colors"
            >
              <Mail className="h-4 w-4" />
              <span>Contact Us</span>
            </button>
          </nav>
          <div className="mt-4 text-xs text-gray-400 text-center">
            <span>&copy; {new Date().getFullYear()} Encompliance.io</span>
          </div>
        </div>
      )}
    </aside>
  );
};

export default Sidebar; 