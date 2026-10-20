/*
  Description: Test suite for the main App component. Mocks dependencies and verifies the App renders without crashing.
  Purpose: Ensures the core application component loads successfully and integrates with mocked providers and routes.
*/
import React from 'react';
import { render } from '@testing-library/react';

// Mock necessary dependencies before importing App
jest.mock('./services/api', () => ({
  __esModule: true,
  default: {
    baseURL: 'http://localhost:8000',
  }
}));

// Mock all components
jest.mock('./components/AIChat', () => ({
  __esModule: true,
  default: () => (
    <div data-testid="ai-chat">AI Chat Component</div>
  ),
}));

jest.mock('./components/Header', () => ({
  __esModule: true,
  default: () => <div data-testid="header">Header</div>,
}));

jest.mock('./components/Footer', () => ({
  __esModule: true,
  default: () => <div data-testid="footer">Footer</div>,
}));

jest.mock('./components/Layout', () => ({
  __esModule: true,
  default: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="layout">{children}</div>
  ),
}));

// Mock all pages
jest.mock('./pages/HomePage', () => () => <div>Home Page</div>);
jest.mock('./pages/LoginPage', () => () => <div>Login Page</div>);
jest.mock('./pages/SignupPage', () => () => <div>Signup Page</div>);
jest.mock('./pages/Dashboard', () => () => <div>Dashboard</div>);
jest.mock('./pages/DocumentViewerPage', () => () => <div>Document Viewer Page</div>);
jest.mock('./pages/ManualUploadPage', () => () => <div>Manual Upload Page</div>);
jest.mock('./pages/ComplianceChatPage', () => () => <div>Compliance Chat Page</div>);
jest.mock('./pages/UserSettingsPage', () => () => <div>User Settings Page</div>);
jest.mock('./pages/AllQueriesPage', () => () => <div>All Queries Page</div>);
jest.mock('./pages/TermsPage', () => () => <div>Terms Page</div>);
jest.mock('./pages/PrivacyPage', () => () => <div>Privacy Page</div>);
jest.mock('./pages/ContactPage', () => () => <div>Contact Page</div>);
jest.mock('./pages/CustomerSupportPortal', () => () => <div>Customer Support Portal</div>);

// Mock all required context providers
jest.mock('./contexts/AuthContext', () => ({
  AuthProvider: ({ children }: { children: React.ReactNode }) => <div data-testid="auth-provider">{children}</div>,
  useAuth: () => ({ isAuthenticated: true, loading: false }),
}));

jest.mock('./contexts/ModelContext', () => ({
  ModelProvider: ({ children }: { children: React.ReactNode }) => <div data-testid="model-provider">{children}</div>,
}));

jest.mock('./contexts/ThemeContext', () => ({
  ThemeProvider: ({ children }: { children: React.ReactNode }) => <div data-testid="theme-provider">{children}</div>,
}));

// Mock react-router-dom
jest.mock('react-router-dom', () => ({
  BrowserRouter: ({ children }: { children: React.ReactNode }) => <div data-testid="browser-router">{children}</div>,
  Routes: ({ children }: { children: React.ReactNode }) => <div data-testid="routes">{children}</div>,
  Route: () => <div data-testid="route">Route</div>,
  Navigate: () => <div>Navigate</div>,
  useLocation: () => ({ pathname: '/' }),
}));

// Import App after all mocks are set up
const App = require('./App').default;

describe('App Component', () => {
  it('renders without crashing', () => {
    const { container } = render(<App />);
    expect(container).toBeTruthy();
  });
}); 