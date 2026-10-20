import React from 'react';
import { Link } from 'react-router-dom';

const InstructionsPage: React.FC = () => {
  return (
    <div className="container mx-auto px-4 py-12 max-w-3xl text-navy-blue dark:text-white">
      <h1 className="text-3xl font-bold mb-6">How to Use Encompliance.io</h1>
      <section className="mb-8">
        <h2 className="text-xl font-semibold mb-2">Purpose of the Application</h2>
        <p>
          Encompliance.io is designed to help childcare providers and organizations simplify and streamline their compliance with regulatory requirements. Our platform leverages AI-powered tools to analyze documents, answer compliance questions, and provide actionable insights, making it easier to stay up-to-date and audit-ready.
        </p>
      </section>
      <section className="mb-8">
        <h2 className="text-xl font-semibold mb-2">Getting Started</h2>
        <ol className="list-decimal list-inside space-y-2">
          <li>Sign up for an account or log in if you already have one.</li>
          <li>Upload your compliance documents for instant AI analysis.</li>
          <li>Use the dashboard to view results, track compliance status, and access recommendations.</li>
          <li>Ask compliance-related questions using the AI chat feature.</li>
          <li>Review your compliance history and download reports as needed.</li>
        </ol>
      </section>
      <section className="mb-8">
        <h2 className="text-xl font-semibold mb-2">Links & Resources</h2>
        <ul className="list-disc list-inside space-y-1">
          <li>
            <Link to="/terms" className="text-blue-600 dark:text-blue-400 underline hover:text-blue-800">Terms of Service</Link>
          </li>
          <li>
            <Link to="/privacy" className="text-blue-600 dark:text-blue-400 underline hover:text-blue-800">Privacy Policy</Link>
          </li>
          <li>
            <Link to="/contact" className="text-blue-600 dark:text-blue-400 underline hover:text-blue-800">Contact Support</Link>
          </li>
        </ul>
      </section>
      <section className="mb-8">
        <h2 className="text-xl font-semibold mb-2">Pro & Enterprise Features</h2>
        <p>
          Stay tuned! We will be adding detailed instructions for advanced features available in our Pro and Enterprise tiers as they are rolled out. These will include enhanced analytics, team management, API access, and more.
        </p>
      </section>
      <div className="mt-12 text-sm text-gray-500 dark:text-gray-400">
        For more information, please visit our <Link to="/contact" className="underline">Contact</Link> page.
      </div>
    </div>
  );
};

export default InstructionsPage; 