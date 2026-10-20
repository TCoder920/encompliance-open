/*
  Description: Terms of service page component. Outlines the application's terms, conditions, and user responsibilities.
  Purpose: Provides legal information and usage guidelines for users of the platform.
*/
import React from 'react';

const TermsPage: React.FC = () => {
  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <h1 className="text-3xl font-bold text-navy-blue dark:text-white mb-6">Terms of Service (ToS) for Encompliance.io</h1>
      <p className="text-gray-600 dark:text-gray-400 mb-6">Last Updated: March 7, 2025</p>
      
      <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6 mb-8">
        <h2 className="text-2xl font-bold text-navy-blue dark:text-white mb-4">Welcome to Encompliance.io</h2>
        <p className="mb-4 dark:text-gray-300">
          Encompliance.io ("Company," "we," "us," or "our") offers a compliance assistance tool for Texas daycare and General Residential Operation (GRO) operators. By accessing or using our service, you agree to these Terms of Service ("Terms"). Consult a legal professional if unsure. Non-acceptance prohibits use.
        </p>
        
        <h3 className="text-xl font-bold text-navy-blue dark:text-white mt-6 mb-3">1. Acceptance of Terms</h3>
        <p className="mb-4 dark:text-gray-300">
          Your use of Encompliance.io constitutes full acceptance of these Terms. Any violation results in immediate termination of access.
        </p>
        
        <h3 className="text-xl font-bold text-navy-blue dark:text-white mt-6 mb-3">2. Service Description</h3>
        <p className="mb-4 dark:text-gray-300">
          Encompliance.io provides access to Texas Minimum Standards PDFs and AI-generated compliance insights to assist operators. This is not legal advice, counsel, or a substitute for professional legal services. All information is for informational purposes only.
        </p>
        
        <h3 className="text-xl font-bold text-navy-blue dark:text-white mt-6 mb-3">3. Subscription and Payment</h3>
        <p className="mb-2 dark:text-gray-300">
          <strong>Pricing:</strong> $79/month for daycare operators, $129/month for GRO operators.
        </p>
        <p className="mb-2 dark:text-gray-300">
          <strong>Payment:</strong> Processed via Stripe, due on the 1st of each month. Late payment suspends access after 7 days' notice.
        </p>
        <p className="mb-4 dark:text-gray-300">
          <strong>Refunds:</strong> No refunds except if service is unavailable for 7+ consecutive days, at our sole discretion.
        </p>
        
        <h3 className="text-xl font-bold text-navy-blue dark:text-white mt-6 mb-3">4. User Responsibilities</h3>
        <ul className="list-disc pl-6 mb-4 dark:text-gray-300">
          <li className="mb-2">Use Encompliance.io solely for Texas compliance support.</li>
          <li className="mb-2">Independently verify all AI-generated information, as it may contain errors. You assume full responsibility for compliance decisions and any resulting consequences (e.g., fines, closures).</li>
          <li className="mb-2">Prohibit sharing account credentials with unauthorized users.</li>
        </ul>
        
        <h3 className="text-xl font-bold text-navy-blue dark:text-white mt-6 mb-3">5. Intellectual Property</h3>
        <p className="mb-4 dark:text-gray-300">
          All content (PDFs, AI outputs) is proprietary to Encompliance.io or licensed from HHSC. Usage is restricted to personal compliance purposes—any reproduction or distribution is strictly prohibited without written consent.
        </p>
        
        <h3 className="text-xl font-bold text-navy-blue dark:text-white mt-6 mb-3">6. Limitation of Liability</h3>
        <p className="mb-4 dark:text-gray-300">
          Encompliance.io is provided "as is" without warranties, express or implied. We disclaim all liability for inaccuracies, omissions, or damages arising from AI outputs, including but not limited to financial losses, regulatory penalties, or business interruptions. You waive any claims against us for reliance on AI information. Our maximum liability, if any, is limited to the amount you've paid in the prior 30 days.
        </p>
        
        <h3 className="text-xl font-bold text-navy-blue dark:text-white mt-6 mb-3">7. Indemnification</h3>
        <p className="mb-4 dark:text-gray-300">
          You agree to indemnify and hold Encompliance.io harmless from any claims, damages, or liabilities (including legal fees) resulting from your use of the service, including errors in AI-generated information.
        </p>
        
        <h3 className="text-xl font-bold text-navy-blue dark:text-white mt-6 mb-3">8. Termination</h3>
        <p className="mb-4 dark:text-gray-300">
          We may terminate access immediately for misuse, non-payment, or breach of Terms. You may cancel via Stripe with 30 days' notice. Terminated users forfeit all rights to data or services.
        </p>
        
        <h3 className="text-xl font-bold text-navy-blue dark:text-white mt-6 mb-3">9. Changes to Terms</h3>
        <p className="mb-4 dark:text-gray-300">
          Terms may be updated with 30 days' prior notice (email or app). Continued use post-update signifies acceptance.
        </p>
        
        <h3 className="text-xl font-bold text-navy-blue dark:text-white mt-6 mb-3">10. Governing Law and Dispute Resolution</h3>
        <p className="mb-4 dark:text-gray-300">
          These Terms are governed by Texas law. Any disputes will be resolved exclusively in Texas state or federal courts, and you waive trial by jury. Arbitration may be required at our discretion, per Texas law.
        </p>
        
        <h3 className="text-xl font-bold text-navy-blue dark:text-white mt-6 mb-3">Contact Us</h3>
        <p className="mb-4 dark:text-gray-300">
          For inquiries, email <a href="mailto:support@encompliance.io" className="text-blue-600 dark:text-blue-400 hover:underline">support@encompliance.io</a>. For legal matters, consult your attorney.
        </p>
      </div>
    </div>
  );
};

export default TermsPage; 