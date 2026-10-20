/*
  Description: Entry point for the Customer Support Portal. Enforces dark mode, handles authentication, and renders the portal shell.
*/
import React, { useEffect } from 'react';
import { createRoot } from 'react-dom/client';
import './index.css';
import { ThemeProvider } from './contexts/ThemeContext';
import CustomerSupportLoginPage from './pages/CustomerSupportLoginPage';
import CustomerSupportPortal from './pages/CustomerSupportPortal';
import { CustomerSupportAuthProvider, useCustomerSupportAuth } from './contexts/CustomerSupportAuthContext';

const DarkModeWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  useEffect(() => {
    document.documentElement.classList.add('dark');
    localStorage.setItem('theme', 'dark');
  }, []);
  
  return <>{children}</>;
};

const CustomerSupportApp: React.FC = () => {
  const { supportToken, setSupportToken, logout } = useCustomerSupportAuth();
  if (!supportToken) {
    return <CustomerSupportLoginPage onLoginSuccess={setSupportToken} />;
    }
  return <CustomerSupportPortal onLogout={logout} />;
};

const container = document.getElementById('root');
if (container) {
    const root = createRoot(container);
    root.render(
        <React.StrictMode>
            <ThemeProvider>
                <DarkModeWrapper>
          <CustomerSupportAuthProvider>
            <CustomerSupportApp />
          </CustomerSupportAuthProvider>
                </DarkModeWrapper>
            </ThemeProvider>
        </React.StrictMode>
    );
} else {
  console.error('Failed to find the root element for the customer support portal.');
} 