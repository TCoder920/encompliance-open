import React from 'react';
import { X, ExternalLink, Info, Shield, HelpCircle } from 'lucide-react';

interface AppleCalendarGuideProps {
  isOpen: boolean;
  onClose: () => void;
}

const AppleCalendarGuide: React.FC<AppleCalendarGuideProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center">
            <Info className="w-6 h-6 mr-2 text-blue-500" />
            How to Connect Your Apple Calendar
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Step 1 */}
          <div className="space-y-3">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
              <span className="bg-blue-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm mr-3">1</span>
              Generate an App-Specific Password
            </h3>
            <div className="ml-9 space-y-2">
              <div className="flex items-center space-x-2">
                <span className="text-gray-700 dark:text-gray-300">Go to</span>
                <a 
                  href="https://appleid.apple.com" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 flex items-center"
                >
                  appleid.apple.com
                  <ExternalLink className="w-4 h-4 ml-1" />
                </a>
                <span className="text-gray-700 dark:text-gray-300">and sign in</span>
              </div>
              <ul className="list-disc list-inside text-gray-700 dark:text-gray-300 space-y-1 ml-4">
                <li>Click on "Sign-In and Security"</li>
                <li>Find the "App-Specific Passwords" section</li>
                <li>Click "Generate Password" or the "+" button</li>
                <li>Enter a label like "EnCompliance Calendar"</li>
                <li>Click "Create"</li>
              </ul>
              <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-3">
                <div className="flex items-start">
                  <Shield className="w-5 h-5 text-yellow-600 dark:text-yellow-400 mr-2 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-yellow-800 dark:text-yellow-200">Important!</p>
                    <p className="text-sm text-yellow-700 dark:text-yellow-300">
                      Copy and save the generated password (looks like: abcd-efgh-ijkl-mnop). 
                      You won't be able to see it again!
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Step 2 */}
          <div className="space-y-3">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
              <span className="bg-blue-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm mr-3">2</span>
              Connect in EnCompliance
            </h3>
            <div className="ml-9 space-y-2">
              <ul className="list-disc list-inside text-gray-700 dark:text-gray-300 space-y-1">
                <li>Click "Connect Apple Calendar" button</li>
                <li>Enter your Apple ID email address</li>
                <li>Paste the app-specific password from Step 1</li>
                <li>Click "Connect"</li>
              </ul>
            </div>
          </div>

          {/* Step 3 */}
          <div className="space-y-3">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
              <span className="bg-blue-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm mr-3">3</span>
              Choose What to Sync
            </h3>
            <div className="ml-9 space-y-2">
              <ul className="list-disc list-inside text-gray-700 dark:text-gray-300 space-y-1">
                <li><strong>Import Only:</strong> Bring your Apple Calendar events into EnCompliance</li>
                <li><strong>Two-Way Sync:</strong> Keep both calendars in sync (recommended)</li>
              </ul>
            </div>
          </div>

          {/* Troubleshooting */}
          <div className="space-y-3">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
              <HelpCircle className="w-5 h-5 mr-2 text-orange-500" />
              Troubleshooting
            </h3>
            <div className="space-y-3">
              <div>
                <h4 className="font-medium text-gray-900 dark:text-white">"Invalid Credentials" Error</h4>
                <ul className="list-disc list-inside text-sm text-gray-600 dark:text-gray-400 ml-4">
                  <li>Double-check your Apple ID email address</li>
                  <li>Make sure you're using the app-specific password, not your regular Apple ID password</li>
                  <li>Try generating a new app-specific password</li>
                </ul>
              </div>
              <div>
                <h4 className="font-medium text-gray-900 dark:text-white">"Connection Failed" Error</h4>
                <ul className="list-disc list-inside text-sm text-gray-600 dark:text-gray-400 ml-4">
                  <li>Check your internet connection</li>
                  <li>Ensure you have iCloud Calendar enabled on your Apple device</li>
                  <li>Try again in a few minutes</li>
                </ul>
              </div>
              <div>
                <h4 className="font-medium text-gray-900 dark:text-white">Events Not Syncing</h4>
                <ul className="list-disc list-inside text-sm text-gray-600 dark:text-gray-400 ml-4">
                  <li>Make sure you selected the correct calendar to sync</li>
                  <li>Check that events aren't set to "Private" in your Apple Calendar</li>
                  <li>Try disconnecting and reconnecting your calendar</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Security Notes */}
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
            <h4 className="font-medium text-blue-900 dark:text-blue-200 flex items-center mb-2">
              <Shield className="w-4 h-4 mr-2" />
              Security Notes
            </h4>
            <ul className="list-disc list-inside text-sm text-blue-800 dark:text-blue-300 space-y-1">
              <li>Your app-specific password is stored securely and encrypted</li>
              <li>You can revoke the app-specific password anytime from your Apple ID settings</li>
              <li>EnCompliance only accesses calendar data, not other iCloud information</li>
            </ul>
          </div>
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-gray-200 dark:border-gray-700">
          <div className="flex justify-between items-center">
            <p className="text-sm text-gray-500 dark:text-gray-400">
              For business calendars, contact your IT administrator.
            </p>
            <button
              onClick={onClose}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Got it!
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AppleCalendarGuide; 