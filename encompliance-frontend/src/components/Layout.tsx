import React, { ReactNode, useEffect } from 'react';
import Header from './Header';
import Footer from './Footer';
import Sidebar from './Sidebar';
import { useAuth } from '../contexts/AuthContext';
import { useLocation } from 'react-router-dom';
import { resetApiCallTracking } from '../services/aiService';
import { realtimeSyncService } from '../services/realtimeSync';

/*
  Description: Layout component that provides a consistent structure for authenticated and unauthenticated pages, including a header, sidebar (for authenticated users), and footer.
  Purpose: Wraps page content to maintain a uniform application layout and manage global UI elements like the header and sidebar.
*/

interface LayoutProps {
  children: ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const { isAuthenticated, user } = useAuth();
  const location = useLocation();
  // Reset API call tracking on every location/route change
  useEffect(() => {
    resetApiCallTracking();
  }, [location.pathname]);

  // Initialize real-time sync for team members
  useEffect(() => {
    if (isAuthenticated && user && user.user_role === 'team_member' && user.id && user.facility_id) {
      console.log('Initializing real-time sync for team member');
      realtimeSyncService.initialize(user.id, user.facility_id, user.user_role);
      
      // Cleanup function to disconnect when component unmounts or user logs out
      return () => {
        realtimeSyncService.disconnect();
      };
    }
  }, [isAuthenticated, user?.id, user?.facility_id, user?.user_role]);

  // Disconnect sync when user logs out
  useEffect(() => {
    if (!isAuthenticated) {
      realtimeSyncService.disconnect();
    }
  }, [isAuthenticated]);

  return (
    <div className="flex flex-col min-h-screen bg-gray-50 dark:bg-dark-bg dark:text-dark-text transition-colors duration-1000">
      <div className="fixed top-0 left-0 right-0 z-50">
        <Header />
      </div>
      <div className="flex flex-1 mt-16">
        {isAuthenticated && (
          <div className="fixed left-0 top-16 z-40 h-[calc(100vh-4rem)] border-r border-gray-700">
            <Sidebar />
          </div>
        )}
        <main className={`flex-1 p-4 ${isAuthenticated ? 'ml-64' : 'ml-0'}`}>{children}</main>
      </div>
      {!isAuthenticated && <Footer />}
    </div>
  );
};

export default Layout; 