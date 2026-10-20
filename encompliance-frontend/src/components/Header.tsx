/*
  Description: Header component. Displays the main navigation bar and branding for the application.
  Purpose: Provides consistent navigation and access to key sections across the frontend.
*/
import React, { useState, useEffect, useRef } from 'react';
import { Shield, Home, LogIn, User, Settings, LayoutDashboard, Search, FileText, Bell, Building, CalendarCheck } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useLocale } from '../contexts/LocaleContext';
import ThemeToggle from './ThemeToggle';
import SurveyPromptIcon from './SurveyPromptIcon';
import ComplianceSurveyModal from './ComplianceSurveyModal';
import axios from 'axios';
import { useNavigate, useLocation } from 'react-router-dom';
import { notificationService } from '../services/notificationService';

const Header: React.FC = () => {
  const { isAuthenticated, logout, user } = useAuth();
  const { locale, translations, toggleLocale } = useLocale();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isSurveyModalOpen, setIsSurveyModalOpen] = useState(false);
  const [surveyStatus, setSurveyStatus] = useState<'idle' | 'submitting' | 'success' | 'error'>('idle');
  const [surveyError, setSurveyError] = useState<string | null>(null);
  const [showSurveyIcon, setShowSurveyIcon] = useState(true);
  const [isFadingOut, setIsFadingOut] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isNotificationsOpen, setIsNotificationsOpen] = useState(false);
  const mobileMenuRef = useRef<HTMLDivElement>(null);
  const mobileButtonRef = useRef<HTMLButtonElement>(null);
  const notificationsRef = useRef<HTMLDivElement>(null);
  const notificationsButtonRef = useRef<HTMLButtonElement>(null);
  const navigate = useNavigate();
  const location = useLocation();

  // Fetch unread notifications count
  useEffect(() => {
    if (isAuthenticated) {
      const fetchUnreadCount = async () => {
        try {
          const count = await notificationService.getUnreadCount();
          setUnreadCount(count);
        } catch (error) {
          console.error('Failed to fetch unread notifications count:', error);
        }
      };
      
      fetchUnreadCount();
      
      // Set up polling for notifications (every 30 seconds)
      const intervalId = setInterval(fetchUnreadCount, 30000);
      
      return () => clearInterval(intervalId);
    }
  }, [isAuthenticated]);

  // Handle clicks outside the mobile menu to close it
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (isMobileMenuOpen && 
          mobileMenuRef.current && 
          !mobileMenuRef.current.contains(event.target as Node) &&
          mobileButtonRef.current && 
          !mobileButtonRef.current.contains(event.target as Node)) {
        setIsMobileMenuOpen(false);
      }
      
      if (isNotificationsOpen && 
          notificationsRef.current && 
          !notificationsRef.current.contains(event.target as Node) &&
          notificationsButtonRef.current && 
          !notificationsButtonRef.current.contains(event.target as Node)) {
        setIsNotificationsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isMobileMenuOpen, isNotificationsOpen]);

  // Handle auto-dismiss of success/error notifications
  useEffect(() => {
    let fadeTimer: NodeJS.Timeout;
    let dismissTimer: NodeJS.Timeout;
    
    if (surveyStatus === 'success' || surveyStatus === 'error') {
      fadeTimer = setTimeout(() => {
        setIsFadingOut(true);
      }, surveyStatus === 'success' ? 2500 : 4500);
      
      dismissTimer = setTimeout(() => {
        setSurveyStatus('idle');
        setIsFadingOut(false);
        if (surveyStatus === 'error') {
          setSurveyError(null);
        }
      }, surveyStatus === 'success' ? 3000 : 5000);
    }
    
    return () => {
      if (fadeTimer) clearTimeout(fadeTimer);
      if (dismissTimer) clearTimeout(dismissTimer);
      setIsFadingOut(false);
    };
  }, [surveyStatus]);

  const handleSurveySubmit = async (response: string, otherText?: string) => {
    if (!user || !user.id) {
      console.error('User ID not found, cannot submit survey.');
      setSurveyError('Could not identify user. Please log in again.');
      setSurveyStatus('error');
      return;
    }

    setSurveyStatus('submitting');
    setSurveyError(null);

    try {
      const payload = { response, otherText };
      const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
      const token = localStorage.getItem('token');

      await axios.post(`${apiBaseUrl}/api/v1/submit-survey`, payload, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      setSurveyStatus('success');
      setIsSurveyModalOpen(false);
      setShowSurveyIcon(false);
    } catch (error) {
      console.error('Error submitting survey:', error);
      let errorMessage = 'Failed to submit survey. Please try again.';
      if (axios.isAxiosError(error) && error.response) {
        errorMessage = error.response.data.detail || errorMessage;
      }
      setSurveyError(errorMessage);
      setSurveyStatus('error');
      throw error;
    }
  };

  const handleNotificationsClick = () => {
    if (isNotificationsOpen) {
      setIsNotificationsOpen(false);
    } else {
      setIsNotificationsOpen(true);
      // Navigate to notifications page instead of showing dropdown
      navigate('/notifications');
    }
  };

  return (
    <header className="bg-navy-blue dark:bg-dark-surface text-white shadow-md transition-colors duration-1000 border-b border-gray-700 h-16">
      <div className="h-full">
        <div className="flex justify-between items-center h-full px-4">
          <div className="flex items-center space-x-2 cursor-pointer" onClick={() => navigate('/')}>
            <Shield className="h-8 w-8" />
            <div className="flex flex-col leading-tight">
              <span className="text-xl font-bold font-times">Encompliance.io</span>
              <span className="text-[10px] uppercase tracking-wide">{translations.headerWelcome}</span>
            </div>
          </div>
          
          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center space-x-4">
            {isAuthenticated ? (
              <>
                <div className="flex items-center space-x-4">
                  <ThemeToggle />
                  <button
                    onClick={toggleLocale}
                    className="px-3 py-1 rounded-lg border border-gray-500 text-xs hover:bg-gray-700 transition-colors"
                  >
                    {locale === 'en' ? 'ES' : 'EN'}
                  </button>
                  <button 
                    onClick={() => navigate('/userSettings')}
                    className={`flex items-center space-x-1 ${location.pathname === '/userSettings' ? 'text-blue-300' : 'hover:text-blue-300'}`}
                  >
                    <User className="h-5 w-5" />
                    <span>User Settings</span>
                  </button>
                  <button
                    ref={notificationsButtonRef}
                    onClick={handleNotificationsClick}
                    className="relative p-1 rounded-full hover:bg-gray-700 transition-colors"
                    aria-label="Notifications"
                  >
                    <Bell className="h-5 w-5" />
                    {unreadCount > 0 && (
                      <span className="absolute top-0 right-0 transform translate-x-1/2 -translate-y-1/2 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
                        {unreadCount > 99 ? '99+' : unreadCount}
                      </span>
                    )}
                  </button>
                  {showSurveyIcon && (
                    <SurveyPromptIcon onClick={() => setIsSurveyModalOpen(true)} />
                  )}
                  <button 
                    onClick={async () => {
                      await logout();
                      navigate('/');
                    }}
                    className="bg-white text-navy-blue dark:bg-gray-700 dark:text-white px-4 py-2 rounded font-bold hover:bg-blue-100 dark:hover:bg-gray-600 transition duration-200"
                  >
                    Logout
                  </button>
                </div>
              </>
            ) : (
              <>
                <div className="flex items-center space-x-4">
                  <ThemeToggle />
                  <button
                    onClick={() => navigate('/login')}
                    className="flex items-center space-x-1 text-white hover:text-blue-300"
                  >
                    <LogIn className="h-5 w-5" />
                    <span>Login</span>
                  </button>
                  <button
                    onClick={() => navigate('/signup')}
                    className="bg-white text-navy-blue dark:bg-gray-700 dark:text-white px-4 py-2 rounded font-bold hover:bg-blue-100 dark:hover:bg-gray-600 transition duration-200"
                  >
                    Sign Up
                  </button>
                </div>
              </>
            )}
          </nav>
          
          {/* Mobile Menu Button */}
          <div className="md:hidden">
            <button 
              ref={mobileButtonRef}
              className="text-white p-2 rounded hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-white"
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              aria-label="Toggle menu"
              aria-expanded={isMobileMenuOpen}
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
          </div>
        </div>

        {/* Mobile Menu */}
        {isMobileMenuOpen && (
          <div ref={mobileMenuRef} className="md:hidden">
            <nav className="absolute right-0 mt-2 mr-4 bg-navy-blue dark:bg-dark-surface rounded-lg shadow-lg py-2 z-50 w-64">
              <div className="flex flex-col space-y-2 px-4">
                {isAuthenticated ? (
                  <>
                    <div className="flex justify-between items-center mb-2">
                      <ThemeToggle />
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={handleNotificationsClick}
                          className="relative p-1 rounded-full hover:bg-gray-700 transition-colors"
                          aria-label="Notifications"
                        >
                          <Bell className="h-5 w-5" />
                          {unreadCount > 0 && (
                            <span className="absolute top-0 right-0 transform translate-x-1/2 -translate-y-1/2 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
                              {unreadCount > 99 ? '99+' : unreadCount}
                            </span>
                          )}
                        </button>
                        {showSurveyIcon && (
                          <SurveyPromptIcon onClick={() => {setIsSurveyModalOpen(true); setIsMobileMenuOpen(false);}} />
                        )}
                      </div>
                    </div>
                    <button
                      onClick={() => { navigate('/userSettings'); setIsMobileMenuOpen(false); }}
                      className="flex items-center space-x-2 text-white hover:bg-gray-700 p-2 rounded w-full text-left"
                    >
                      <User className="h-5 w-5" />
                      <span>User Settings</span>
                    </button>
                    <button 
                      onClick={async () => {
                        await logout();
                        navigate('/');
                        setIsMobileMenuOpen(false);
                      }}
                      className="w-full text-center bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded font-bold transition duration-200"
                    >
                      Logout
                    </button>
                  </>
                ) : (
                  <>
                    <div className="flex justify-between items-center mb-2">
                      <ThemeToggle />
                    </div>
                    <button
                      onClick={() => { navigate('/login'); setIsMobileMenuOpen(false); }}
                      className="flex items-center justify-between p-2 rounded hover:bg-gray-700 w-full"
                    >
                      <span>Login</span>
                      <LogIn className="h-5 w-5" />
                    </button>
                    <button
                      onClick={() => { navigate('/signup'); setIsMobileMenuOpen(false); }}
                      className="w-full text-center bg-white text-navy-blue dark:bg-gray-700 dark:text-white px-4 py-2 rounded font-bold hover:bg-blue-100 dark:hover:bg-gray-600 transition duration-200"
                    >
                      Sign Up
                    </button>
                  </>
                )}
              </div>
            </nav>
          </div>
        )}
      </div>

      <ComplianceSurveyModal
        isOpen={isSurveyModalOpen}
        onClose={() => {
          setIsSurveyModalOpen(false);
          setSurveyStatus('idle');
          setSurveyError(null);
        }}
        onSubmit={handleSurveySubmit}
        userId={user?.id ? String(user.id) : null}
      />
    </header>
  );
};

export default Header;