/*
  Description: SurveyPromptIcon component. Displays an icon to prompt users to participate in a compliance survey.
  Purpose: Encourages user feedback and engagement for improving compliance features.
*/
import React from 'react';
import { HelpCircle } from 'lucide-react';

interface SurveyPromptIconProps {
  onClick: () => void;
}

const SurveyPromptIcon: React.FC<SurveyPromptIconProps> = ({ onClick }) => {
  return (
    <button
      onClick={onClick}
      className="relative p-2 rounded-full focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 group"
      aria-label="Open compliance survey"
    >
      {/* Pulsing gradient background */}
      <span
        className="absolute inset-0 block w-full h-full rounded-full opacity-75 animate-pulse bg-gradient-to-r from-blue-400 via-purple-500 to-sky-500 group-hover:opacity-100 transition-opacity duration-300"
        aria-hidden="true"
      ></span>
      {/* Icon */}
      <HelpCircle className="relative z-10 w-6 h-6 text-white" />

      {/* Tooltip (optional, shown on hover) */}
      <span
        className="absolute top-full left-1/2 transform -translate-x-1/2 mt-2 px-2 py-1 text-xs text-white bg-gray-700 rounded opacity-0 group-hover:opacity-100 transition-opacity duration-300 whitespace-nowrap"
      >
        Compliance Survey
      </span>
    </button>
  );
};

export default SurveyPromptIcon; 