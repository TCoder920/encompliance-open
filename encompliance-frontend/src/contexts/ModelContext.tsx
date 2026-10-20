/*
  Description: ModelContext provides AI model selection and configuration state for the application.
  Purpose: Allows users to choose and configure AI models, storing preferences and settings for compliance assistant features.
*/
import React, { createContext, useState, useContext, useEffect } from 'react';
import api from '../services/api';

export interface ModelSettings {
  provider: string; // 'auto', 'openai', 'anthropic', 'google', 'other'
  api_key?: string; // API key stored in localStorage for simplicity
  otherApiUrl: string;
  localModelUrl: string;
}

interface ModelContextType {
  selectedModel: string; // 'basic' or 'pro'
  setSelectedModel: (model: string) => void;
  modelSettings: ModelSettings;
  updateModelSettings: (settings: Partial<ModelSettings>) => void; // Allow partial updates
  saveSettingsToBackend: () => Promise<void>;
  loadUserSettings: () => Promise<void>;
  loadError: string | null;
  deleteStoredApiKey: () => void;
  clearLocalModelUrl: () => void;
  clearOtherApiUrl: () => void;
}

const defaultSettings: ModelSettings = {
  provider: 'auto',
  api_key: '',
  otherApiUrl: '',
  localModelUrl: 'http://127.0.0.1:1234/v1', // Default LM Studio URL with /v1
};

const ModelContext = createContext<ModelContextType | undefined>(undefined);

export const ModelProvider: React.FC<{children: React.ReactNode}> = ({ children }) => {
  const [selectedModel, setSelectedModelInternal] = useState<string>(() => {
    const storedModel = localStorage.getItem('selectedAIModel');
    // Migrate from old values to new values if needed
    if (storedModel === 'local-model' || storedModel === 'cloud-model') {
      return 'basic'; // Default everything to 'basic' mode
    }
    return storedModel || 'basic'; // Default to basic mode
  });
  
  // Initialize with default settings, will be overwritten by loadUserSettings
  const [modelSettings, setModelSettingsInternal] = useState<ModelSettings>(() => {
    // Try to load from localStorage first
    const storedSettings = localStorage.getItem('modelSettings');
    return storedSettings ? JSON.parse(storedSettings) : defaultSettings;
  });
  
  const [settingsLoaded, setSettingsLoaded] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);

  // Function to save settings to localStorage and update state
  const updateModelSettings = (settings: Partial<ModelSettings>) => {
    setModelSettingsInternal(prev => {
      const updated = { ...prev, ...settings };
      // Save to localStorage
      localStorage.setItem('modelSettings', JSON.stringify(updated));
      return updated;
    });
  };

  // Function to update selected model and save to localStorage
  const setSelectedModel = (model: string) => {
    setSelectedModelInternal(model);
    localStorage.setItem('selectedAIModel', model);
  };

  // Function to load settings from the backend (optional, can fall back to localStorage)
  const loadUserSettings = async () => {
    try {
      setLoadError(null);
      
      // Check if user is authenticated before attempting to fetch settings
      const token = localStorage.getItem('token');
      if (!token) {
        // Not authenticated, fall back to localStorage settings
        const storedSettings = localStorage.getItem('modelSettings');
        if (storedSettings) {
          try {
            const parsedSettings = JSON.parse(storedSettings);
            setModelSettingsInternal(parsedSettings);
          } catch (parseError) {
            console.error("Error parsing stored settings:", parseError);
            setModelSettingsInternal(defaultSettings);
          }
        }
        setSettingsLoaded(true);
        return;
      }
      
      // Add timeout to prevent getting stuck
      const timeoutPromise = new Promise<{data: null}>((_, reject) => {
        setTimeout(() => reject(new Error('Timeout: settings request took too long')), 5000);
      });
      
      // Race the API call with a timeout
      const response = await Promise.race([
        api.get('/users/me/settings'),
        timeoutPromise
      ]);
      
      if (response.data) {
        // Get API key from localStorage for security (not from backend)
        const storedApiKey = localStorage.getItem('model_api_key') || '';
        
        // Merge backend settings with localStorage API key
        const loadedSettings = {
          ...response.data,
          api_key: storedApiKey
        };
        
        // Update state
        setModelSettingsInternal(loadedSettings);
        
        // Also save to localStorage
        localStorage.setItem('modelSettings', JSON.stringify(loadedSettings));
        
        setSettingsLoaded(true);
      } else {
        setModelSettingsInternal(prev => {
          // Keep API key from localStorage
          const apiKey = localStorage.getItem('model_api_key') || '';
          const settings = { ...defaultSettings, api_key: apiKey };
          
          // Save to localStorage without logging the full object that contains API key
          localStorage.setItem('modelSettings', JSON.stringify(settings));
          
          return settings;
        });
      }
    } catch (error) {
      console.error("Failed to load user settings from backend:", error);
      setLoadError(error instanceof Error ? error.message : "Failed to load settings");
      
      // Fall back to localStorage
      const storedSettings = localStorage.getItem('modelSettings');
      if (storedSettings) {
        try {
          const parsedSettings = JSON.parse(storedSettings);
          setModelSettingsInternal(parsedSettings);
        } catch (parseError) {
          console.error("Error parsing stored settings:", parseError);
          setModelSettingsInternal(defaultSettings);
        }
      }
    } finally {
      setSettingsLoaded(true);
    }
  };

  // Save settings to backend and localStorage
  const saveSettingsToBackend = async () => {
    try {
      setLoadError(null);
      
      // Store API key separately in localStorage for security
      if (modelSettings.api_key) {
        localStorage.setItem('model_api_key', modelSettings.api_key);
      }
      
      // Prepare data for backend (mask API key)
      const backendData = {
        ...modelSettings,
        api_key: modelSettings.api_key ? "********" : ""
      };
      
      await api.put('/users/me/settings', backendData);
      
      // Create a safe version for logging
      const safeLogSettings = {
        ...backendData,
        api_key: backendData.api_key ? "********" : ""
      };
      
      return;
    } catch (error) {
      console.error("Failed to save user settings to backend:", error);
      setLoadError(error instanceof Error ? error.message : "Failed to save settings");
      throw error;
    }
  };

  // Load settings from backend on mount
  useEffect(() => {
    if (!settingsLoaded) {
      loadUserSettings();
    }
  }, [settingsLoaded]);

  // Make sure selected model is saved to localStorage
  useEffect(() => {
    localStorage.setItem('selectedAIModel', selectedModel);
  }, [selectedModel]);

  // *** Add Implementation for Deletion/Clearing ***
  const deleteStoredApiKey = () => {
    try {
      localStorage.removeItem('model_api_key');
      // Also remove any reference to API key in the model settings
      setModelSettingsInternal(prev => ({ ...prev, api_key: '' }));
    } catch (error) {
      console.error("Failed to delete API key from storage");
      setLoadError("Failed to delete API key from storage."); // Optionally set error
    }
  };

  const clearLocalModelUrl = () => {
    // Reset URL in state and trigger save via updateModelSettings
    // Ensure defaultSettings is accessible here or use the actual default value directly
    const currentDefaultSettings = defaultSettings; // Assuming defaultSettings is defined in scope
    updateModelSettings({ localModelUrl: currentDefaultSettings.localModelUrl });
  };

   const clearOtherApiUrl = () => {
    // Reset URL in state and trigger save via updateModelSettings
    const currentDefaultSettings = defaultSettings; // Assuming defaultSettings is defined in scope
    updateModelSettings({ otherApiUrl: currentDefaultSettings.otherApiUrl });
  };

  return (
    <ModelContext.Provider value={{ 
      selectedModel, 
      setSelectedModel,
      modelSettings,
      updateModelSettings,
      saveSettingsToBackend,
      loadUserSettings,
      loadError,
      deleteStoredApiKey,
      clearLocalModelUrl,
      clearOtherApiUrl
    }}>
      {children}
    </ModelContext.Provider>
  );
};

export const useModel = () => {
  const context = useContext(ModelContext);
  if (context === undefined) {
    throw new Error('useModel must be used within a ModelProvider');
  }
  return context;
}; 