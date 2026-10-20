/*
  Description: Home page component. Serves as the landing page for the application, introducing features and guiding users to key actions.
  Purpose: Welcomes users and provides navigation to signup, login, and main features.
*/
import React, { useState, useEffect, useRef } from 'react';
import { Shield, CheckCircle, AlertTriangle, Users, FileCheck, Clock, CheckSquare, AlertCircle, ExternalLink, FileText, Search, User } from 'lucide-react';
import ErrorMessage from '../components/ErrorMessage';
import { useAuth } from '../contexts/AuthContext';
import documentService from '../services/documentService';
import { useNavigate } from 'react-router-dom';

const HomePage: React.FC = () => {
  const { isAuthenticated, user } = useAuth();
  const navigate = useNavigate();
  const [metrics, setMetrics] = useState({
    activeUsers: 2142,
    documentsAnalyzed: 8212,
    complianceQueries: 75565,
    enforcementActions: 56,
    inspectionsPassed: 656
  });

  const [showTicker, setShowTicker] = useState(true);
  const [startAnimation, setStartAnimation] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Initial pause before animation starts
  useEffect(() => {
    const animationTimer = setTimeout(() => {
      setStartAnimation(true);
      setIsLoading(false);
    }, 5000); // 5 second pause

    return () => clearTimeout(animationTimer);
  }, []);

  // Continuous metrics update
  useEffect(() => {
    if (!startAnimation) return;

    try {
      const updateInterval = setInterval(() => {
        setMetrics(prev => ({
          activeUsers: prev.activeUsers + Math.floor(Math.random() * 3), // 0-2 new users
          documentsAnalyzed: prev.documentsAnalyzed + Math.floor(Math.random() * 2), // 0-1 new documents
          complianceQueries: prev.complianceQueries + Math.floor(Math.random() * 5), // 0-4 new queries
          enforcementActions: prev.enforcementActions, // Keep static as it's from official data
          inspectionsPassed: prev.inspectionsPassed // Keep static as it's less frequent
        }));
      }, 3000); // Update every 3 seconds

      return () => clearInterval(updateInterval);
    } catch (err) {
      console.error('Error updating metrics:', err);
      setError('Unable to update metrics data. Please refresh the page.');
    }
  }, [startAnimation]);

  return (
    <div className="min-h-screen transition-colors duration-1000">
      {/* Hero Section */}
      <section className="bg-gradient-to-r from-navy-blue to-blue-700 dark:from-dark-surface dark:to-gray-800 text-white py-16 transition-colors duration-1000">
        <div className="container mx-auto px-4">
          <div className="flex flex-col md:flex-row items-center">
            <div className="md:w-1/2 mb-8 md:mb-0">
              <h1 className="text-4xl md:text-5xl font-bold mb-4">
                Simplify Childcare Compliance
              </h1>
              <p className="text-xl mb-6">
                AI-powered tools to help childcare providers understand and meet regulatory requirements.
              </p>
              <div className="flex flex-col sm:flex-row space-y-4 sm:space-y-0 sm:space-x-4">
                {isAuthenticated ? (
                  <button
                    onClick={() => navigate('/dashboard')}
                    className="bg-white text-navy-blue dark:bg-gray-700 dark:text-white px-6 py-3 rounded-lg font-bold text-lg hover:bg-blue-100 dark:hover:bg-gray-600 transition duration-300"
                  >
                    Go to Dashboard
                  </button>
                ) : (
                  <>
                    <button
                      onClick={() => navigate('/signup')}
                      className="bg-white text-navy-blue dark:bg-gray-700 dark:text-white px-6 py-3 rounded-lg font-bold text-lg hover:bg-blue-100 dark:hover:bg-gray-600 transition duration-300"
                    >
                      Get Started
                    </button>
                    <button
                      onClick={() => navigate('/login')}
                      className="border-2 border-white text-white px-6 py-3 rounded-lg font-bold text-lg hover:bg-white hover:bg-opacity-10 transition duration-300"
                    >
                      Log In
                    </button>
                  </>
                )}
              </div>
            </div>
            <div className="md:w-1/2 flex justify-center">
              <Shield className="w-48 h-48 text-white opacity-90" />
            </div>
          </div>
        </div>
      </section>

      {/* Metrics Ticker */}
      <div className="bg-blue-100 dark:bg-gray-800 py-4 overflow-hidden relative transition-colors duration-1000">
        {error && <ErrorMessage message={error} />}
        {isLoading ? (
          <div className="container mx-auto px-4 flex justify-center">
            <p className="text-navy-blue dark:text-white">Loading metrics...</p>
          </div>
        ) : (
          <div className="relative overflow-hidden w-full">
            <div className="animate-marquee inline-flex whitespace-nowrap absolute">
              <div className="flex items-center space-x-2 text-navy-blue dark:text-white mx-8">
                <Users className="h-5 w-5" />
                <span className="font-semibold">{metrics.activeUsers.toLocaleString()}</span>
                <span>Active Users</span>
              </div>
              <div className="flex items-center space-x-2 text-navy-blue dark:text-white mx-8">
                <FileText className="h-5 w-5" />
                <span className="font-semibold">{metrics.documentsAnalyzed.toLocaleString()}</span>
                <span>Documents Analyzed</span>
              </div>
              <div className="flex items-center space-x-2 text-navy-blue dark:text-white mx-8">
                <Search className="h-5 w-5" />
                <span className="font-semibold">{metrics.complianceQueries.toLocaleString()}</span>
                <span>Compliance Queries</span>
              </div>
              <div className="flex items-center space-x-2 text-navy-blue dark:text-white mx-8">
                <AlertCircle className="h-5 w-5" />
                <span className="font-semibold">{metrics.enforcementActions.toLocaleString()}</span>
                <span>Enforcement Actions Avoided</span>
              </div>
              <div className="flex items-center space-x-2 text-navy-blue dark:text-white mx-8">
                <CheckSquare className="h-5 w-5" />
                <span className="font-semibold">{metrics.inspectionsPassed.toLocaleString()}</span>
                <span>Inspections Passed</span>
              </div>
            </div>
            <div className="animate-marquee2 inline-flex whitespace-nowrap absolute">
              <div className="flex items-center space-x-2 text-navy-blue dark:text-white mx-8">
                <Users className="h-5 w-5" />
                <span className="font-semibold">{metrics.activeUsers.toLocaleString()}</span>
                <span>Active Users</span>
              </div>
              <div className="flex items-center space-x-2 text-navy-blue dark:text-white mx-8">
                <FileText className="h-5 w-5" />
                <span className="font-semibold">{metrics.documentsAnalyzed.toLocaleString()}</span>
                <span>Documents Analyzed</span>
              </div>
              <div className="flex items-center space-x-2 text-navy-blue dark:text-white mx-8">
                <Search className="h-5 w-5" />
                <span className="font-semibold">{metrics.complianceQueries.toLocaleString()}</span>
                <span>Compliance Queries</span>
              </div>
              <div className="flex items-center space-x-2 text-navy-blue dark:text-white mx-8">
                <AlertCircle className="h-5 w-5" />
                <span className="font-semibold">{metrics.enforcementActions.toLocaleString()}</span>
                <span>Enforcement Actions Avoided</span>
              </div>
              <div className="flex items-center space-x-2 text-navy-blue dark:text-white mx-8">
                <CheckSquare className="h-5 w-5" />
                <span className="font-semibold">{metrics.inspectionsPassed.toLocaleString()}</span>
                <span>Inspections Passed</span>
              </div>
            </div>
            {/* Add an invisible spacer to ensure proper height */}
            <div className="invisible inline-flex whitespace-nowrap">
              <div className="flex items-center space-x-2 mx-8">
                <span className="h-5 w-5" />
                <span className="font-semibold">Spacer</span>
                <span>Spacer</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Features Section */}
      <section className="py-16 bg-white dark:bg-dark-bg transition-colors duration-1000">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-center mb-12 text-navy-blue dark:text-white">How You Benefit From Using Encompliance</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="bg-gray-50 dark:bg-dark-surface rounded-lg p-6 shadow-md transition-all duration-300 hover:shadow-lg transform hover:-translate-y-1 transition-colors duration-1000">
              <div className="text-blue-600 dark:text-blue-400 mb-4">
                <FileCheck className="h-12 w-12" />
              </div>
              <h3 className="text-xl font-bold mb-2 text-navy-blue dark:text-white">Document Analysis</h3>
              <p className="text-gray-600 dark:text-gray-300">
                Upload your documents and get AI-powered analysis to identify compliance issues and areas for improvement.
              </p>
            </div>
            
            <div className="bg-gray-50 dark:bg-dark-surface rounded-lg p-6 shadow-md transition-all duration-300 hover:shadow-lg transform hover:-translate-y-1 transition-colors duration-1000">
              <div className="text-green-600 dark:text-green-400 mb-4">
                <CheckCircle className="h-12 w-12" />
              </div>
              <h3 className="text-xl font-bold mb-2 text-navy-blue dark:text-white">Compliance Assistance</h3>
              <p className="text-gray-600 dark:text-gray-300">
                Get real-time guidance on regulatory requirements and best practices for your childcare operation.
              </p>
            </div>
            
            <div className="bg-gray-50 dark:bg-dark-surface rounded-lg p-6 shadow-md transition-all duration-300 hover:shadow-lg transform hover:-translate-y-1 transition-colors duration-1000">
              <div className="text-yellow-600 dark:text-yellow-400 mb-4">
                <AlertTriangle className="h-12 w-12" />
              </div>
              <h3 className="text-xl font-bold mb-2 text-navy-blue dark:text-white">Risk Mitigation</h3>
              <p className="text-gray-600 dark:text-gray-300">
                Identify potential compliance risks before they become issues, helping you avoid penalties and enforcement actions.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 bg-gray-100 dark:bg-gray-800 transition-colors duration-1000">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold mb-6 text-navy-blue dark:text-white">Ready to Simplify Your Compliance Process?</h2>
          <p className="text-xl mb-8 text-gray-600 dark:text-gray-300 max-w-3xl mx-auto">
            Join thousands of childcare providers who are using Encompliance.io to streamline their regulatory compliance.
          </p>
          
          {isAuthenticated ? (
            <button
              onClick={() => navigate('/dashboard')}
              className="bg-navy-blue text-white dark:bg-blue-600 px-8 py-4 rounded-lg font-bold text-lg hover:bg-blue-800 dark:hover:bg-blue-700 transition duration-300"
            >
              Go to Dashboard
            </button>
          ) : (
            <button
              onClick={() => navigate('/signup')}
              className="bg-navy-blue text-white dark:bg-blue-600 px-8 py-4 rounded-lg font-bold text-lg hover:bg-blue-800 dark:hover:bg-blue-700 transition duration-300"
            >
              Get Started Today
            </button>
          )}
        </div>
      </section>

      {/* Testimonials Section */}
      <section className="py-16 bg-white dark:bg-dark-bg transition-colors duration-1000">
        {/* ... existing testimonials code ... */}
      </section>
    </div>
  );
};

export default HomePage;