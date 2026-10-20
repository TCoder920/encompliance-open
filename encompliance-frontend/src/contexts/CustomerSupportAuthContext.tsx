/*
  Description: CustomerSupportAuthContext provides authentication state for support agents.
  Purpose: Manages portal login sessions and token storage for secure access to support tools.
*/
import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { isJwtExpired } from '../utils/jwt';

interface CustomerSupportAuthContextType {
  supportToken: string | null;
  setSupportToken: (token: string | null) => void;
  logout: () => void;
}

const STORAGE_KEY = 'customerSupportToken';

const TOKEN_CHECK_INTERVAL_MS = 30_000;

const CustomerSupportAuthContext = createContext<CustomerSupportAuthContextType | undefined>(undefined);

const getInitialToken = (): string | null => {
  if (typeof window === 'undefined') {
    return null;
  }
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored && isJwtExpired(stored)) {
    localStorage.removeItem(STORAGE_KEY);
    return null;
  }
  return stored;
};

export const CustomerSupportAuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [supportToken, setSupportTokenState] = useState<string | null>(getInitialToken);

  useEffect(() => {
    if (supportToken) {
      localStorage.setItem(STORAGE_KEY, supportToken);
    } else {
      localStorage.removeItem(STORAGE_KEY);
    }
  }, [supportToken]);

  useEffect(() => {
    if (!supportToken) {
      return;
    }

    const intervalId = window.setInterval(() => {
      if (supportToken && isJwtExpired(supportToken, 15_000)) {
        setSupportTokenState(null);
        localStorage.removeItem(STORAGE_KEY);
      }
    }, TOKEN_CHECK_INTERVAL_MS);

    return () => {
      clearInterval(intervalId);
    };
  }, [supportToken]);

  const setSupportToken = (token: string | null) => {
    setSupportTokenState(token);
  };

  const logout = () => {
    setSupportTokenState(null);
    localStorage.removeItem(STORAGE_KEY);
  };

  return (
    <CustomerSupportAuthContext.Provider value={{ supportToken, setSupportToken, logout }}>
      {children}
    </CustomerSupportAuthContext.Provider>
  );
};

export const useCustomerSupportAuth = () => {
  const context = useContext(CustomerSupportAuthContext);
  if (!context) {
    throw new Error('useCustomerSupportAuth must be used within a CustomerSupportAuthProvider');
  }
  return context;
}; 