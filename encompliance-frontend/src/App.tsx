/*
  Description: Main application component for the frontend. Sets up routing, authentication, theming, and layout for all user-facing pages.
  Purpose: Provides the core structure and navigation for the React app, ensuring protected routes and context providers are properly configured.
*/
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import Header from './components/Header';
import Footer from './components/Footer';
import HomePage from './pages/HomePage';
import SignupPage from './pages/SignupPage';
import LoginPage from './pages/LoginPage';
import OTPLoginPage from './pages/OTPLoginPage';
import EmailVerificationPage from './pages/EmailVerificationPage';
import DocumentViewerPage from './pages/DocumentViewerPage';
import ManualUploadPage from './pages/ManualUploadPage';
import Dashboard from './pages/Dashboard';
import ComplianceChatPage from './pages/ComplianceChatPage';
import UserSettingsPage from './pages/UserSettingsPage';
import ChangePasswordPage from './pages/ChangePasswordPage';
import AllQueriesPage from './pages/AllQueriesPage';
import TermsPage from './pages/TermsPage';
import PrivacyPage from './pages/PrivacyPage';
import ContactPage from './pages/ContactPage';
import InstructionsPage from './pages/InstructionsPage';
import CalendarPage from './pages/CalendarPage';
import CalendarSettings from './pages/CalendarSettings';
import NotesPage from './pages/NotesPage';
import NotificationsPage from './pages/NotificationsPage';
import ExportDashboard from './pages/ExportDashboard';

// Training Pages
import TrainingPrograms from './pages/TrainingPrograms';
import StaffManagement from './pages/StaffManagement';
import TrainingAssignments from './pages/TrainingAssignments';
import CreateTrainingProgram from './pages/CreateTrainingProgram';
import ProgramDetails from './pages/ProgramDetails';
import EditTrainingProgram from './pages/EditTrainingProgram';
import TrainingOverview from './pages/TrainingOverview';
import TrainingAnalytics from './pages/TrainingAnalytics';
import TrainingReports from './pages/TrainingReports';
import TrainingCompletions from './pages/TrainingCompletions';
import CreateStaff from './pages/CreateStaff';
import CreateAssignment from './pages/CreateAssignment';
import AssignmentDetails from './pages/AssignmentDetails';
import EditAssignment from './pages/EditAssignment';
import StaffDetails from './pages/StaffDetails';
import EditStaff from './pages/EditStaff';
import StaffProgress from './pages/StaffProgress';
import StaffDirectoryPage from './pages/StaffDirectoryPage';
import AuditLogPage from './pages/AuditLogPage';
import TrainingContent from './pages/TrainingContent';

// Facility Management Pages
import FacilityDashboard from './pages/FacilityDashboard';
import JoinFacilityPage from './pages/JoinFacilityPage';
import SubscriptionPage from './pages/SubscriptionPage';

// Task Management Pages
import TaskManagement from './pages/TaskManagement';
import CreateTask from './pages/CreateTask';
import TaskDetails from './pages/TaskDetails';
import EditTask from './pages/EditTask';
import AssignTask from './pages/AssignTask';
import ActivityCalendar from './pages/Activities/ActivityCalendar';
import SuggestActivityPage from './pages/Activities/SuggestActivityPage';

// Policy Management Pages
import PolicyManagementPage from './pages/PolicyManagementPage';
import PolicyAcknowledgmentPage from './pages/PolicyAcknowledgmentPage';
import SchedulingPage from './pages/SchedulingPage';
import AIAssistantHub from './pages/AIAssistantHub';
import TeamCommunicationPage from './pages/TeamCommunicationPage';
import DataImportPage from './pages/DataImportPage';
import GoogleOAuthSetupPage from './pages/GoogleOAuthSetupPage';
import EnterpriseConsolePage from './pages/EnterpriseConsolePage';
import UsageBillingPage from './pages/UsageBillingPage';
import BillingPage from './pages/BillingPage';
import SupportPage from './pages/SupportPage';


import { AuthProvider, useAuth } from './contexts/AuthContext';
import { ModelProvider } from './contexts/ModelContext';
import { ThemeProvider } from './contexts/ThemeContext';
import { LocaleProvider } from './contexts/LocaleContext';
import './App.css';
import AIChat from './components/AIChat';
import Layout from './components/Layout';
import UpdateNotifier from './components/ui/UpdateNotifier';

// PrivateRoute wrapper for authenticated routes
function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, loading } = useAuth();
  const location = useLocation();
  if (loading) return <div>Loading...</div>;
  if (!isAuthenticated) return <Navigate to="/login" state={{ from: location }} replace />;
  return <>{children}</>;
}

function App() {
  return (
    <AuthProvider>
      <ModelProvider>
        <ThemeProvider>
          <LocaleProvider>
            <Router
              future={{
                v7_startTransition: true,
                v7_relativeSplatPath: true,
              }}
            >
              <Layout>
              <Routes>
                <Route path="/" element={<HomePage />} />
                <Route path="/signup" element={<SignupPage />} />
                <Route path="/login" element={<LoginPage />} />
                <Route path="/login/otp" element={<OTPLoginPage />} />
                <Route path="/verify-email" element={<EmailVerificationPage />} />
                <Route path="/terms" element={<TermsPage />} />
                <Route path="/privacy" element={<PrivacyPage />} />
                <Route path="/contact" element={<ContactPage />} />
                <Route path="/instructions" element={<InstructionsPage />} />
                {/* Authenticated routes */}
                <Route
                  path="/dashboard"
                  element={
                    <PrivateRoute>
                      <Dashboard />
                    </PrivateRoute>
                  }
                />
                <Route
                  path="/calendar"
                  element={
                    <PrivateRoute>
                      <CalendarPage />
                    </PrivateRoute>
                  }
                />
                <Route
                  path="/calendar-settings"
                  element={
                    <PrivateRoute>
                      <CalendarSettings />
                    </PrivateRoute>
                  }
                />
                <Route
                  path="/notes"
                  element={
                    <PrivateRoute>
                      <NotesPage />
                    </PrivateRoute>
                  }
                />
                <Route
                  path="/notifications"
                  element={
                    <PrivateRoute>
                      <NotificationsPage />
                    </PrivateRoute>
                  }
                />
                <Route
                  path="/support"
                  element={
                    <PrivateRoute>
                      <SupportPage />
                    </PrivateRoute>
                  }
                />
                <Route
                  path="/userSettings"
                  element={
                    <PrivateRoute>
                      <UserSettingsPage />
                    </PrivateRoute>
                  }
                />
                <Route
                  path="/changePassword"
                  element={
                    <PrivateRoute>
                      <ChangePasswordPage />
                    </PrivateRoute>
                  }
                />
                <Route
                  path="/allQueriesPage"
                  element={
                    <PrivateRoute>
                      <AllQueriesPage />
                    </PrivateRoute>
                  }
                />
                <Route
                  path="/search"
                  element={
                    <PrivateRoute>
                      <ComplianceChatPage />
                    </PrivateRoute>
                  }
                />
                <Route
                  path="/documentUpload"
                  element={
                    <PrivateRoute>
                      <ManualUploadPage 
                        operationType="default"
                        onUploadComplete={() => {}}
                        onBack={() => {}}
                        onSkip={() => {}}
                        navigateTo={() => {}}
                      />
                    </PrivateRoute>
                  }
                />
                <Route
                  path="/document/:documentId"
                  element={
                    <PrivateRoute>
                      <DocumentViewerPage 
                        navigateTo={() => {}} 
                      />
                    </PrivateRoute>
                  }
                />
                <Route
                  path="/chat/:conversationId"
                  element={
                    <PrivateRoute>
                      <ComplianceChatPage />
                    </PrivateRoute>
                  }
                />
                <Route
                  path="/export"
                  element={
                    <PrivateRoute>
                      <ExportDashboard />
                    </PrivateRoute>
                  }
                />
                
                {/* Training Routes */}
                <Route
                  path="/training"
                  element={
                    <PrivateRoute>
                      <TrainingOverview />
                    </PrivateRoute>
                  }
                />
                <Route
                  path="/training/programs"
                  element={
                    <PrivateRoute>
                      <TrainingPrograms />
                    </PrivateRoute>
                  }
                />
                <Route
                  path="/training/staff"
                  element={
                    <PrivateRoute>
                      <StaffManagement />
                    </PrivateRoute>
                  }
                />
                <Route
                  path="/training/staff/new"
                  element={
                    <PrivateRoute>
                      <CreateStaff />
                    </PrivateRoute>
                  }
                />
                <Route
                  path="/training/staff/:id"
                  element={
                    <PrivateRoute>
                      <StaffDetails />
                    </PrivateRoute>
                  }
                />
                <Route
                  path="/training/staff/:id/edit"
                  element={
                    <PrivateRoute>
                      <EditStaff />
                    </PrivateRoute>
                  }
                />
                <Route
                  path="/training/staff/:id/progress"
                  element={
                    <PrivateRoute>
                      <StaffProgress />
                    </PrivateRoute>
                  }
                />
                <Route
                  path="/training/assignments"
                  element={
                    <PrivateRoute>
                      <TrainingAssignments />
                    </PrivateRoute>
                  }
                />
                <Route
                  path="/training/assignments/new"
                  element={
                    <PrivateRoute>
                      <CreateAssignment />
                    </PrivateRoute>
                  }
                />
                <Route
                  path="/training/assignments/:id"
                  element={
                    <PrivateRoute>
                      <AssignmentDetails />
                    </PrivateRoute>
                  }
                />
                <Route
                  path="/training/assignments/:id/edit"
                  element={
                    <PrivateRoute>
                      <EditAssignment />
                    </PrivateRoute>
                  }
                />
                <Route
                  path="/training/completions"
                  element={
                    <PrivateRoute>
                      <TrainingCompletions />
                    </PrivateRoute>
                  }
                />
                <Route
                  path="/training/programs/new"
                  element={
                    <PrivateRoute>
                      <CreateTrainingProgram />
                    </PrivateRoute>
                  }
                />
                <Route
                  path="/training/programs/:id"
                  element={
                    <PrivateRoute>
                      <ProgramDetails />
                    </PrivateRoute>
                  }
                />
                <Route
                  path="/training/programs/:id/edit"
                  element={
                    <PrivateRoute>
                      <EditTrainingProgram />
                    </PrivateRoute>
                  }
                />
                <Route
                  path="/training/programs/:id/content"
                  element={
                    <PrivateRoute>
                      <TrainingContent />
                    </PrivateRoute>
                  }
                />
                <Route
                  path="/training/analytics"
                  element={
                    <PrivateRoute>
                      <TrainingAnalytics />
                    </PrivateRoute>
                  }
                />
                <Route
                  path="/training/reports"
                  element={
                    <PrivateRoute>
                      <TrainingReports />
                    </PrivateRoute>
                  }
                />
                
                {/* Policy Management Routes */}
                <Route
                  path="/policies"
                  element={
                    <PrivateRoute>
                      <PolicyManagementPage />
                    </PrivateRoute>
                  }
                />
                <Route
                  path="/policies/acknowledge"
                  element={
                    <PrivateRoute>
                      <PolicyAcknowledgmentPage />
                    </PrivateRoute>
                  }
                />
                <Route
                  path="/ai-assistant"
                  element={
                    <PrivateRoute>
                      <AIAssistantHub />
                    </PrivateRoute>
                  }
                />
                <Route
                  path="/team-communication"
                  element={
                    <PrivateRoute>
                      <TeamCommunicationPage />
                    </PrivateRoute>
                  }
                />
                <Route
                  path="/data-import"
                  element={
                    <PrivateRoute>
                      <DataImportPage />
                    </PrivateRoute>
                  }
                />
                <Route
                  path="/google-setup"
                  element={
                    <PrivateRoute>
                      <GoogleOAuthSetupPage />
                    </PrivateRoute>
                  }
                />
                <Route
                  path="/enterprise-console"
                  element={
                    <PrivateRoute>
                      <EnterpriseConsolePage />
                    </PrivateRoute>
                  }
                />
                <Route
                  path="/usage-billing"
                  element={
                    <PrivateRoute>
                      <UsageBillingPage />
                    </PrivateRoute>
                  }
                />
                <Route
                  path="/billing"
                  element={
                    <PrivateRoute>
                      <BillingPage />
                    </PrivateRoute>
                  }
                />
                <Route
                  path="/scheduling"
                  element={
                    <PrivateRoute>
                      <SchedulingPage />
                    </PrivateRoute>
                  }
                />
                
                {/* Facility Management Routes */}
                <Route
                  path="/facility"
                  element={
                    <PrivateRoute>
                      <FacilityDashboard />
                    </PrivateRoute>
                  }
                />
                <Route
                  path="/staff-directory"
                  element={
                    <PrivateRoute>
                      <StaffDirectoryPage />
                    </PrivateRoute>
                  }
                />
                <Route
                  path="/subscription"
                  element={
                    <PrivateRoute>
                      <SubscriptionPage />
                    </PrivateRoute>
                  }
                />
                <Route
                  path="/audit-log"
                  element={
                    <PrivateRoute>
                      <AuditLogPage />
                    </PrivateRoute>
                  }
                />
                <Route
                  path="/join-facility/:invitationCode"
                  element={<JoinFacilityPage />}
                />
                
                {/* Task Management Routes */}
                <Route
                  path="/tasks"
                  element={
                    <PrivateRoute>
                      <TaskManagement />
                    </PrivateRoute>
                  }
                />
                <Route
                  path="/tasks/new"
                  element={
                    <PrivateRoute>
                      <CreateTask />
                    </PrivateRoute>
                  }
                />
                <Route
                  path="/tasks/:id"
                  element={
                    <PrivateRoute>
                      <TaskDetails />
                    </PrivateRoute>
                  }
                />
                <Route
                  path="/tasks/:id/edit"
                  element={
                    <PrivateRoute>
                      <EditTask />
                    </PrivateRoute>
                  }
                />
                <Route
                  path="/tasks/:id/assign"
                  element={
                    <PrivateRoute>
                      <AssignTask />
                    </PrivateRoute>
                  }
                />
                
                {/* Training Routes */}
                <Route
                  path="/training"
                  element={
                    <PrivateRoute>
                      <TrainingOverview />
                    </PrivateRoute>
                  }
                />
                <Route
                  path="/training/programs"
                  element={
                    <PrivateRoute>
                      <TrainingPrograms />
                    </PrivateRoute>
                  }
                />
                <Route
                  path="/training/staff"
                  element={
                    <PrivateRoute>
                      <StaffManagement />
                    </PrivateRoute>
                  }
                />
                <Route
                  path="/training/staff/new"
                  element={
                    <PrivateRoute>
                      <CreateStaff />
                    </PrivateRoute>
                  }
                />
                <Route
                  path="/activities"
                  element={
                    <PrivateRoute>
                      <ActivityCalendar />
                    </PrivateRoute>
                  }
                />
                <Route
                  path="/activities/suggest"
                  element={
                    <PrivateRoute>
                      <SuggestActivityPage />
                    </PrivateRoute>
                  }
                />
                <Route
                  path="/training/staff/:staffId"
                  element={
                    <PrivateRoute>
                      <StaffDetails />
                    </PrivateRoute>
                  }
                />
                
                {/* 404 Catch-all */}
                <Route path="*" element={<div style={{textAlign:'center',marginTop:'10vh'}}><h1>404 - Page Not Found</h1></div>} />
              </Routes>
              </Layout>
            </Router>
          </LocaleProvider>
        </ThemeProvider>
      </ModelProvider>
      {process.env.NODE_ENV === 'production' && <UpdateNotifier />}
    </AuthProvider>
  );
}

export default App; 