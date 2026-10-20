/*
  Description: Locale context to toggle between English and Spanish.
*/

import React, { createContext, useContext, useState, useCallback } from 'react';
import translationService from '../services/translationService';

interface LocaleState {
  locale: 'en' | 'es';
  translations: Record<string, string>;
  toggleLocale: () => Promise<void>;
}

const LocaleContext = createContext<LocaleState | undefined>(undefined);

const DEFAULT_PHRASES = {
  headerWelcome: 'Welcome',
  footerTagline: 'Compliance made simple.',
};

export const LocaleProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [locale, setLocale] = useState<'en' | 'es'>('en');
  const [translations, setTranslations] = useState<Record<string, string>>(DEFAULT_PHRASES);

  const toggleLocale = useCallback(async () => {
    if (locale === 'en') {
      try {
        const response = await translationService.translateBulk(Object.values(DEFAULT_PHRASES));
        const mapped: Record<string, string> = {};
        Object.keys(DEFAULT_PHRASES).forEach((key, idx) => {
          mapped[key] = response[idx] || DEFAULT_PHRASES[key as keyof typeof DEFAULT_PHRASES];
        });
        setTranslations(mapped);
        setLocale('es');
      } catch {
        setLocale('es');
      }
    } else {
      setLocale('en');
      setTranslations(DEFAULT_PHRASES);
    }
  }, [locale]);

  return (
    <LocaleContext.Provider value={{ locale, translations, toggleLocale }}>
      {children}
    </LocaleContext.Provider>
  );
};

export const useLocale = (): LocaleState => {
  const context = useContext(LocaleContext);
  if (!context) {
    throw new Error('useLocale must be used within a LocaleProvider');
  }
  return context;
};

