/*
  Description: Footer component. Displays application copyright, links, and legal information.
  Purpose: Provides consistent footer content and navigation across all pages.
*/
import React from 'react';
import { Shield } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useLocale } from '../contexts/LocaleContext';

const Footer: React.FC = () => {
  const { translations } = useLocale();
  return (
    // Remove relative positioning if no other absolute elements need it
    <footer className="bg-navy-blue dark:bg-dark-surface text-white py-6 transition-colors duration-1000">
      {/* Removed hidden admin link */}
      
      <div className="container mx-auto px-4">
        <div className="flex flex-col md:flex-row justify-between items-center">
          <div className="flex items-center mb-4 md:mb-0">
            <Shield className="h-6 w-6 mr-2" />
            <span className="text-lg font-bold font-times">Encompliance.io</span>
          </div>
          
          <div className="text-sm text-gray-300 text-center md:text-left">
            <p>&copy; {new Date().getFullYear()} Encompliance.io.</p>
            <p>{translations.footerTagline}</p>
          </div>
          
          <div className="mt-4 md:mt-0">
            <ul className="flex space-x-4">
              <li>
                <Link to="/terms" className="hover:text-blue-300">Terms</Link>
              </li>
              <li>
                <Link to="/privacy" className="hover:text-blue-300">Privacy</Link>
              </li>
              <li>
                <Link to="/contact" className="hover:text-blue-300">Contact</Link>
              </li>
              <li>
                <Link to="/instructions" className="hover:text-blue-300">Instructions</Link>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;