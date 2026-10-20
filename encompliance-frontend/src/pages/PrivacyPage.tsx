import React from 'react';

const PrivacyPage: React.FC = () => {
  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <h1 className="text-3xl font-bold text-navy-blue dark:text-white mb-6">Privacy Policy for Encompliance.io</h1>
      <p className="text-gray-600 dark:text-gray-400 mb-6">Last Updated: March 7, 2025</p>
      
      <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6 mb-8">
        <h2 className="text-2xl font-bold text-navy-blue dark:text-white mb-4">Your Privacy Matters</h2>
        <p className="mb-4 dark:text-gray-300">
          Encompliance.io ("Company," "we," "us") prioritizes your privacy while assisting Texas daycare and GRO operators with compliance. This Privacy Policy outlines our practices.
        </p>
        
        <h3 className="text-xl font-bold text-navy-blue dark:text-white mt-6 mb-3">1. Information We Collect</h3>
        <ul className="list-disc pl-6 mb-4 dark:text-gray-300">
          <li className="mb-2"><strong>Account Data:</strong> Email, password for signup/verification.</li>
          <li className="mb-2"><strong>Usage Data:</strong> AI queries, IP address for security and analytics.</li>
          <li className="mb-2">No sensitive data (e.g., child records) is collected.</li>
        </ul>
        
        <h3 className="text-xl font-bold text-navy-blue dark:text-white mt-6 mb-3">2. How We Use Your Data</h3>
        <ul className="list-disc pl-6 mb-4 dark:text-gray-300">
          <li className="mb-2">To deliver the service (e.g., AI responses from PDFs).</li>
          <li className="mb-2">To enhance functionality (e.g., query trend analysis).</li>
          <li className="mb-2">To process payments (via Stripe).</li>
        </ul>
        
        <h3 className="text-xl font-bold text-navy-blue dark:text-white mt-6 mb-3">3. How We Share Your Data</h3>
        <ul className="list-disc pl-6 mb-4 dark:text-gray-300">
          <li className="mb-2">With Stripe for payment processing.</li>
          <li className="mb-2">With law enforcement if required by subpoena or court order.</li>
          <li className="mb-2">Aggregated, anonymized data may be used for analytics—no personal identification.</li>
        </ul>
        
        <h3 className="text-xl font-bold text-navy-blue dark:text-white mt-6 mb-3">4. Data Security</h3>
        <ul className="list-disc pl-6 mb-4 dark:text-gray-300">
          <li className="mb-2">Data encrypted in transit (HTTPS) and at rest (Stripe/Bubble servers).</li>
          <li className="mb-2">Access limited to authorized personnel with strict protocols.</li>
        </ul>
        
        <h3 className="text-xl font-bold text-navy-blue dark:text-white mt-6 mb-3">5. Your Rights</h3>
        <ul className="list-disc pl-6 mb-4 dark:text-gray-300">
          <li className="mb-2">Request access, correction, or deletion of your data via <a href="mailto:support@encompliance.io" className="text-blue-600 dark:text-blue-400 hover:underline">support@encompliance.io</a> within 30 days.</li>
          <li className="mb-2">Opt-out of non-essential emails by replying "unsubscribe."</li>
        </ul>
        
        <h3 className="text-xl font-bold text-navy-blue dark:text-white mt-6 mb-3">6. Compliance</h3>
        <p className="mb-4 dark:text-gray-300">
          Adheres to Texas privacy laws. No HIPAA or GDPR applies (no health data collected).
        </p>
        
        <h3 className="text-xl font-bold text-navy-blue dark:text-white mt-6 mb-3">7. Data Retention</h3>
        <p className="mb-4 dark:text-gray-300">
          Data retained for 12 months post-account closure, then securely deleted, unless legally required.
        </p>
        
        <h3 className="text-xl font-bold text-navy-blue dark:text-white mt-6 mb-3">8. Changes to Policy</h3>
        <p className="mb-4 dark:text-gray-300">
          Updates posted here with 30 days' notice (email). Continued use signifies acceptance.
        </p>
        
        <h3 className="text-xl font-bold text-navy-blue dark:text-white mt-6 mb-3">Contact Us</h3>
        <p className="mb-4 dark:text-gray-300">
          Privacy concerns? Email <a href="mailto:support@encompliance.io" className="text-blue-600 dark:text-blue-400 hover:underline">support@encompliance.io</a>. For legal advice, consult your attorney.
        </p>
      </div>
    </div>
  );
};

export default PrivacyPage; 