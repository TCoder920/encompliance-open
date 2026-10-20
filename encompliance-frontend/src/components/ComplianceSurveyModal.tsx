/*
  Description: ComplianceSurveyModal component. Presents a modal survey to collect user feedback on compliance challenges.
  Purpose: Gathers insights from users to improve compliance features and support.
*/
import React, { useState } from 'react';

interface ComplianceSurveyModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (response: string, otherText?: string) => void;
  userId: string | null; // Assuming userId is available when the modal is open
}

const ComplianceSurveyModal: React.FC<ComplianceSurveyModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  userId,
}) => {
  const [selectedOption, setSelectedOption] = useState<string>('');
  const [otherText, setOtherText] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const options = [
    'Too time-consuming',
    'Fear of fines',
    'Staff training',
    'Other',
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedOption) {
      setError('Please select an option.');
      return;
    }
    if (selectedOption === 'Other' && !otherText.trim()) {
      setError('Please specify your challenge in the text box.');
      return;
    }
    if (!userId) {
      setError('User not identified. Cannot submit.');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      await onSubmit(selectedOption, selectedOption === 'Other' ? otherText : undefined);
      // onClose will likely be called by the parent component after successful submission
    } catch (err) {
      console.error('Survey submission error:', err);
      setError('Failed to submit survey. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleOptionChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedOption(e.target.value);
    setError(null); // Clear error when option changes
    if (e.target.value !== 'Other') {
      setOtherText(''); // Clear other text if 'Other' is not selected
    }
  };

  const handleOtherTextChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setOtherText(e.target.value);
    if (selectedOption === 'Other') {
      setError(null); // Clear error when typing in 'Other'
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50">
      <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-xl w-full max-w-md">
        <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">Compliance Challenge Survey</h2>
        <p className="mb-4 text-gray-600 dark:text-gray-300">
          Please answer this compliance questionnaire to help us better serve you.
        </p>
        <p className="mb-4 text-lg font-medium text-gray-700 dark:text-gray-200">
          What's your biggest compliance challenge?
        </p>
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <select
              value={selectedOption}
              onChange={handleOptionChange}
              className="w-full p-2 border border-gray-300 rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              aria-label="Select your biggest compliance challenge"
            >
              <option value="" disabled>Select an option...</option>
              {options.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </div>

          {selectedOption === 'Other' && (
            <div className="mb-4">
              <input
                type="text"
                value={otherText}
                onChange={handleOtherTextChange}
                placeholder="Please specify your challenge"
                className="w-full p-2 border border-gray-300 rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                aria-label="Specify your challenge if Other selected"
              />
            </div>
          )}

          {error && <p className="text-red-500 text-sm mb-4">{error}</p>}

          <div className="flex justify-end space-x-2">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 disabled:opacity-50 dark:bg-gray-600 dark:text-gray-200 dark:hover:bg-gray-500"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting || !selectedOption || (selectedOption === 'Other' && !otherText.trim())}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? 'Submitting...' : 'Submit'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ComplianceSurveyModal; 