/*
  Description: QuickAccessLinks component. Displays customizable quick access links for easy navigation.
  Purpose: Provides users with shortcuts to frequently used features and pages.
  Enhanced with freemium preview functionality.
*/
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Edit2, Plus, X, Save, Calendar, FileText, Settings, Home, Search, Download, GraduationCap, BarChart3, MessageSquare, Bell, Building } from 'lucide-react';
import { userService, QuickAccessLink as ServiceQuickAccessLink } from '../services/userService';
import { useAuth } from '../contexts/AuthContext';
import { Tier, getTierFromSubscriptionStatus } from '../utils/tiers';
import { canUseFeature, canUseFeatureWithRole, isPremiumFeature } from '../utils/accessControl';

interface QuickAccessLink {
  id: string;
  title: string;
  path: string;
  icon: string;
  order: number;
}

interface QuickAccessLinksProps {
  canAccessCalendar?: boolean; // Legacy prop, now handled internally
}

// Available pages for quick access
const AVAILABLE_PAGES = [
  { title: 'Dashboard', path: '/', icon: 'Home', requiresPro: false, adminOnly: false },
  { title: 'Facility Overview', path: '/facility', icon: 'Building', requiresPro: true, adminOnly: true },
  { title: 'Compliance Assistant', path: '/search', icon: 'Search', requiresPro: false, adminOnly: false },
  { title: 'Training & Certification', path: '/training', icon: 'GraduationCap', requiresPro: true, adminOnly: false },
  { title: 'Calendar', path: '/calendar', icon: 'Calendar', requiresPro: true, adminOnly: false },
  { title: 'Notes', path: '/notes', icon: 'FileText', requiresPro: true, adminOnly: false },
  { title: 'Data Export', path: '/export', icon: 'Download', requiresPro: true, adminOnly: true },
  { title: 'Analytics', path: '/training/analytics', icon: 'BarChart3', requiresPro: true, adminOnly: true },
  { title: 'All Queries', path: '/allQueriesPage', icon: 'MessageSquare', requiresPro: false, adminOnly: false },
  { title: 'Notifications', path: '/notifications', icon: 'Bell', requiresPro: false, adminOnly: false },
  { title: 'Settings', path: '/userSettings', icon: 'Settings', requiresPro: false, adminOnly: false },
];

// Default quick access links for facility admins
const DEFAULT_ADMIN_LINKS: QuickAccessLink[] = [
  { id: '1', title: 'Dashboard', path: '/', icon: 'Home', order: 1 },
  { id: '2', title: 'Compliance Assistant', path: '/search', icon: 'Search', order: 2 },
  { id: '3', title: 'Training & Certification', path: '/training', icon: 'GraduationCap', order: 3 },
  { id: '4', title: 'Calendar', path: '/calendar', icon: 'Calendar', order: 4 },
  { id: '5', title: 'Notes', path: '/notes', icon: 'FileText', order: 5 },
  { id: '6', title: 'Settings', path: '/userSettings', icon: 'Settings', order: 6 },
];

// Default quick access links for team members (no admin-only features)
const DEFAULT_TEAM_MEMBER_LINKS: QuickAccessLink[] = [
  { id: '1', title: 'Dashboard', path: '/', icon: 'Home', order: 1 },
  { id: '2', title: 'Compliance Assistant', path: '/search', icon: 'Search', order: 2 },
  { id: '3', title: 'Training & Certification', path: '/training', icon: 'GraduationCap', order: 3 },
  { id: '4', title: 'Calendar', path: '/calendar', icon: 'Calendar', order: 4 },
  { id: '5', title: 'Notes', path: '/notes', icon: 'FileText', order: 5 },
  { id: '6', title: 'Settings', path: '/userSettings', icon: 'Settings', order: 6 },
];

// Convert service link to component link
const convertServiceToComponentLink = (serviceLink: ServiceQuickAccessLink, index: number): QuickAccessLink => ({
  id: `${index}`,
  title: serviceLink.label,
  path: serviceLink.path,
  icon: serviceLink.icon || 'Home',
  order: index + 1,
});

// Convert component link to service link
const convertComponentToServiceLink = (componentLink: QuickAccessLink): ServiceQuickAccessLink => ({
  label: componentLink.title,
  path: componentLink.path,
  icon: componentLink.icon,
});

const QuickAccessLinks: React.FC<QuickAccessLinksProps> = () => {
  const { user } = useAuth();
  const [links, setLinks] = useState<QuickAccessLink[]>([]);
  const [isEditing, setIsEditing] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const userTier = getTierFromSubscriptionStatus(user?.subscription_status);

  // Fetch user's quick access links
  useEffect(() => {
    const fetchLinks = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        const userLinks = await userService.getQuickAccessLinks();
        
        // If user has no links, use role-appropriate defaults
        if (!userLinks || userLinks.length === 0) {
          const defaultLinks = user?.user_role === 'team_member' ? DEFAULT_TEAM_MEMBER_LINKS : DEFAULT_ADMIN_LINKS;
          setLinks(defaultLinks);
        } else {
          // Convert service links to component links and filter for team members
          let convertedLinks = userLinks.map(convertServiceToComponentLink);
          
          // Filter out admin-only links for team members
          if (user?.user_role === 'team_member') {
            convertedLinks = convertedLinks.filter(link => {
              const availablePage = AVAILABLE_PAGES.find(page => page.path === link.path);
              return !availablePage?.adminOnly;
            });
          }
          
          setLinks(convertedLinks);
        }
      } catch (err) {
        console.error('Failed to load quick access links:', err);
        setError('Failed to load quick access links. Using defaults.');
        const defaultLinks = user?.user_role === 'team_member' ? DEFAULT_TEAM_MEMBER_LINKS : DEFAULT_ADMIN_LINKS;
        setLinks(defaultLinks);
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchLinks();
  }, []);
  
  // Handle link navigation
  const handleNavigation = (path: string) => {
    navigate(path);
  };

  // Get icon component by name
  const getIconComponent = (iconName: string) => {
    const icons: { [key: string]: React.ComponentType<any> } = {
      Home,
      Building,
      Calendar,
      FileText,
      Settings,
      Search,
      Download,
      GraduationCap,
      BarChart3,
      MessageSquare,
      Bell
    };
    return icons[iconName] || Home;
  };

  // Save links to backend
  const saveLinks = async (newLinks: QuickAccessLink[]) => {
    try {
      // Convert component links to service links
      const serviceLinks = newLinks.map(convertComponentToServiceLink);
      await userService.updateQuickAccessLinks(serviceLinks);
      setLinks(newLinks);
      setError(null);
    } catch (err) {
      console.error('Failed to save quick access links:', err);
      setError('Failed to save changes. Please try again.');
    }
  };

  // Add a new link
  const addLink = (page: typeof AVAILABLE_PAGES[0]) => {
    const newLink: QuickAccessLink = {
      id: Date.now().toString(),
      title: page.title,
      path: page.path,
      icon: page.icon,
      order: links.length + 1,
    };
    const newLinks = [...links, newLink];
    saveLinks(newLinks);
  };

  // Remove a link
  const removeLink = (linkId: string) => {
    const newLinks = links.filter(link => link.id !== linkId);
    saveLinks(newLinks);
  };

  // Move link up
  const moveLinkUp = (index: number) => {
    if (index === 0) return;
    const newLinks = [...links];
    [newLinks[index], newLinks[index - 1]] = [newLinks[index - 1], newLinks[index]];
    newLinks.forEach((link, i) => link.order = i + 1);
    saveLinks(newLinks);
  };

  // Move link down
  const moveLinkDown = (index: number) => {
    if (index === links.length - 1) return;
    const newLinks = [...links];
    [newLinks[index], newLinks[index + 1]] = [newLinks[index + 1], newLinks[index]];
    newLinks.forEach((link, i) => link.order = i + 1);
    saveLinks(newLinks);
  };

  if (isLoading) {
    return (
      <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded mb-4"></div>
          <div className="space-y-2">
            {[1, 2, 3, 4, 5, 6].map(i => (
              <div key={i} className="h-10 bg-gray-200 dark:bg-gray-700 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // Render edit mode
  if (isEditing) {
    const availablePages = AVAILABLE_PAGES.filter(
      page => !links.some(link => link.path === page.path) && 
      (user?.user_role !== 'team_member' || !page.adminOnly)
    );

    return (
      <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold text-navy-blue dark:text-white">Edit Quick Access</h2>
          <button
            onClick={() => setIsEditing(false)}
            className="p-1 text-gray-600 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-200"
            aria-label="Cancel editing"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {error && (
          <div className="text-red-600 dark:text-red-400 text-sm mb-3">
            {error}
          </div>
        )}

        {/* Current Links */}
        <div className="mb-6">
          <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Current Links</h3>
          <div className="space-y-2">
            {links.map((link, index) => {
              const IconComponent = getIconComponent(link.icon);
              const isProFeature = isPremiumFeature(link.path.replace('/', ''));
              
              return (
                <div key={link.id} className="flex items-center justify-between p-2 border border-gray-200 dark:border-gray-700 rounded">
                  <div className="flex items-center">
                    <IconComponent className="h-4 w-4 mr-2 text-gray-600 dark:text-gray-400" />
                    <span className="text-sm text-gray-700 dark:text-gray-300">{link.title}</span>
                    {isProFeature && (
                      <span className="ml-2 text-xs bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200 px-2 py-1 rounded-full">
                        PRO
                      </span>
                    )}
                  </div>
                  <div className="flex items-center space-x-1">
                    <button
                      onClick={() => moveLinkUp(index)}
                      disabled={index === 0}
                      className="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
                      aria-label="Move up"
                    >
                      ↑
                    </button>
                    <button
                      onClick={() => moveLinkDown(index)}
                      disabled={index === links.length - 1}
                      className="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
                      aria-label="Move down"
                    >
                      ↓
                    </button>
                    <button
                      onClick={() => removeLink(link.id)}
                      className="p-1 text-red-400 hover:text-red-600"
                      aria-label="Remove link"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Available Pages */}
        {availablePages.length > 0 && (
          <div>
            <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Add Links</h3>
            <div className="space-y-2">
              {availablePages.map(page => {
                const IconComponent = getIconComponent(page.icon);
                return (
                  <button
                    key={page.path}
                    onClick={() => addLink(page)}
                    className="w-full flex items-center justify-between p-2 border border-gray-200 dark:border-gray-700 rounded hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                  >
                    <div className="flex items-center">
                      <IconComponent className="h-4 w-4 mr-2 text-gray-600 dark:text-gray-400" />
                      <span className="text-sm text-gray-700 dark:text-gray-300">{page.title}</span>
                      {page.requiresPro && (
                        <span className="ml-2 text-xs bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200 px-2 py-1 rounded-full">
                          PRO
                        </span>
                      )}
                    </div>
                    <Plus className="h-4 w-4 text-gray-400" />
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </div>
    );
  }
  
  // Render view mode
  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold text-navy-blue dark:text-white">Quick Access</h2>
        <button
          onClick={() => setIsEditing(true)}
          className="p-1 text-gray-600 hover:text-blue-600 dark:text-gray-400 dark:hover:text-blue-400"
          aria-label="Edit quick access links"
        >
          <Edit2 className="h-5 w-5" />
        </button>
      </div>
      
      {error && (
        <div className="text-red-600 dark:text-red-400 text-sm mb-3">
          {error}
        </div>
      )}
      
      {links.map((link, index) => {
        const IconComponent = getIconComponent(link.icon);
        // Map paths to feature keys
        let featureKey = link.path.replace('/', '') || 'dashboard';
        if (link.path === '/training/analytics') {
          featureKey = 'analytics';
        } else if (link.path === '/search') {
          featureKey = 'search'; // Free feature
        } else if (link.path === '/allQueriesPage') {
          featureKey = 'queries'; // Free feature
        } else if (link.path === '/notifications') {
          featureKey = 'notifications'; // Free feature
        } else if (link.path === '/export') {
          featureKey = 'data_export';
        } else if (link.path === '/training') {
          featureKey = 'training_certification';
        } else if (link.path === '/facility') {
          featureKey = 'facility_management';
        }
        
        // Hide administrative features completely for team members
        if (user?.user_role === 'team_member' && (featureKey === 'data_export' || featureKey === 'facility_management' || featureKey === 'analytics')) {
          return null;
        }
        
        const isProFeature = isPremiumFeature(featureKey);
        const canUse = featureKey === 'data_export' 
          ? canUseFeatureWithRole(userTier, featureKey, user?.user_role, user?.subscription_status)
          : canUseFeature(userTier, featureKey);
        
        return (
          <div key={index} className="mt-2">
            <button
              onClick={() => handleNavigation(link.path)}
              className={`w-full border text-gray-700 dark:text-gray-300 py-2 px-4 rounded mb-2 flex items-center justify-between hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors ${
                isProFeature && !canUse 
                  ? 'border-yellow-300 dark:border-yellow-600 bg-yellow-50 dark:bg-yellow-900/20' 
                  : 'border-gray-300 dark:border-gray-600'
              }`}
            >
              <div className="flex items-center min-w-0 flex-1">
                <IconComponent className={`mr-2 h-5 w-5 flex-shrink-0 ${
                  link.icon === 'Home' ? 'text-blue-500' :
                  link.icon === 'Building' ? 'text-amber-500' :
                  link.icon === 'Search' ? 'text-indigo-500' :
                  link.icon === 'GraduationCap' ? 'text-emerald-500' :
                  link.icon === 'Calendar' ? 'text-purple-500' : 
                  link.icon === 'FileText' ? 'text-green-500' :
                  link.icon === 'Download' ? 'text-orange-500' :
                  link.icon === 'BarChart3' ? 'text-cyan-500' :
                  link.icon === 'MessageSquare' ? 'text-pink-500' :
                  link.icon === 'Bell' ? 'text-yellow-500' :
                  link.icon === 'Settings' ? 'text-gray-500' :
                  'text-blue-500'
                }`} />
                <span className="truncate text-sm">{link.title}</span>
                {isProFeature && !canUse && (
                  <span className="ml-2 text-xs bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200 px-2 py-1 rounded-full flex-shrink-0">
                    PRO
                  </span>
                )}
              </div>
              {isProFeature && !canUse && (
                <span className="text-xs text-yellow-600 dark:text-yellow-400 flex-shrink-0 ml-2">
                  Preview
                </span>
              )}
            </button>
            {isProFeature && !canUse && (
              <p className="text-xs text-gray-500 dark:text-gray-400 mb-2 px-2 break-words">
                {link.title === 'Calendar' && 'Manage compliance deadlines and events.'}
                {link.title === 'Notes' && 'Organize compliance documentation and checklists.'}
                {link.title === 'Training & Certification' && 'Manage staff training programs and certifications.'}
                {link.title === 'Data Export' && 'Export compliance data and reports.'}
                {link.title === 'Analytics' && 'View detailed training and compliance analytics.'}
                {link.title === 'Facility Overview' && 'Manage facility details, staff, and subscriptions.'}
              </p>
            )}
          </div>
        );
      })}
    </div>
  );
};

export default QuickAccessLinks; 