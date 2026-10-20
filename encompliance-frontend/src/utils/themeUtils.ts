/*
  Description: Theme utility functions and constants for consistent styling and theming across the application.
  Purpose: Centralizes theme-related classes and helpers to ensure a unified look and feel for UI components.
*/

/**
 * Common theme classes for various UI elements
 */
export const themeClasses = {
  // Text colors
  text: {
    primary: 'text-navy-blue dark:text-white transition-colors duration-300',
    secondary: 'text-gray-600 dark:text-gray-300 transition-colors duration-300',
    muted: 'text-gray-500 dark:text-gray-400 transition-colors duration-300',
    link: 'text-navy-blue dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 transition-colors duration-300',
    danger: 'text-red-600 dark:text-red-400 transition-colors duration-300',
    success: 'text-green-600 dark:text-green-400 transition-colors duration-300',
  },
  
  // Background colors
  bg: {
    primary: 'bg-white dark:bg-dark-surface transition-colors duration-300',
    secondary: 'bg-gray-50 dark:bg-gray-800 transition-colors duration-300',
    accent: 'bg-navy-blue dark:bg-blue-600 transition-colors duration-300',
    danger: 'bg-red-600 dark:bg-red-700 transition-colors duration-300',
    success: 'bg-green-600 dark:bg-green-700 transition-colors duration-300',
    warning: 'bg-yellow-500 dark:bg-yellow-600 transition-colors duration-300',
  },
  
  // Border colors
  border: {
    primary: 'border-gray-200 dark:border-gray-700 transition-colors duration-300',
    secondary: 'border-gray-300 dark:border-gray-600 transition-colors duration-300',
    accent: 'border-navy-blue dark:border-blue-500 transition-colors duration-300',
  },
  
  // Common components
  components: {
    card: 'bg-white dark:bg-dark-surface rounded-lg shadow-md p-6 transition-colors duration-300',
    input: 'border border-gray-300 dark:border-gray-600 rounded-lg py-2 px-3 focus:outline-none focus:ring-2 focus:ring-navy-blue dark:focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-200 transition-colors duration-300',
    button: {
      primary: 'bg-navy-blue dark:bg-blue-600 text-white rounded hover:bg-blue-700 dark:hover:bg-blue-700 transition-colors duration-300',
      secondary: 'bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-300 dark:hover:bg-gray-500 transition-colors duration-300',
      danger: 'bg-red-600 dark:bg-red-700 text-white rounded hover:bg-red-700 dark:hover:bg-red-800 transition-colors duration-300',
    },
    divider: 'border-t border-gray-200 dark:border-gray-700 transition-colors duration-300',
    loader: 'animate-spin h-8 w-8 border-4 border-navy-blue dark:border-blue-500 border-t-transparent rounded-full transition-colors duration-300',
  },
  
  // Page layout
  layout: {
    container: 'container mx-auto px-4 py-8',
    section: 'mb-8',
    header: 'mb-6',
  },
};

/**
 * Apply theme classes to an element based on its type
 * @param type The type of element to style
 * @param variant Optional variant for the element
 * @returns The appropriate CSS classes
 */
export const getThemeClasses = (
  type: 'text' | 'bg' | 'border' | 'card' | 'input' | 'button' | 'divider' | 'loader',
  variant: 'primary' | 'secondary' | 'accent' | 'danger' | 'success' | 'warning' | 'muted' | 'link' = 'primary'
): string => {
  switch (type) {
    case 'text':
      return themeClasses.text[variant as keyof typeof themeClasses.text] || themeClasses.text.primary;
    case 'bg':
      return themeClasses.bg[variant as keyof typeof themeClasses.bg] || themeClasses.bg.primary;
    case 'border':
      return themeClasses.border[variant as keyof typeof themeClasses.border] || themeClasses.border.primary;
    case 'card':
      return themeClasses.components.card;
    case 'input':
      return themeClasses.components.input;
    case 'button':
      return themeClasses.components.button[variant as keyof typeof themeClasses.components.button] || themeClasses.components.button.primary;
    case 'divider':
      return themeClasses.components.divider;
    case 'loader':
      return themeClasses.components.loader;
    default:
      return '';
  }
};

/**
 * Combines multiple theme classes
 * @param classes Array of class objects with type and optional variant
 * @returns Combined CSS classes string
 */
export const combineThemeClasses = (
  classes: Array<{ type: 'text' | 'bg' | 'border' | 'card' | 'input' | 'button' | 'divider' | 'loader'; variant?: 'primary' | 'secondary' | 'accent' | 'danger' | 'success' | 'warning' | 'muted' | 'link' }>
): string => {
  return classes.map(c => getThemeClasses(c.type, c.variant)).join(' ');
};

export default themeClasses; 