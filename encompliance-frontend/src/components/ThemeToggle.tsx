/*
  Description: ThemeToggle component. Allows users to switch between light and dark modes for the application UI.
  Purpose: Provides a user-friendly toggle for accessibility and personal preference in theme selection.
*/
import React, { useRef, useEffect } from 'react';
import { useTheme } from '../contexts/ThemeContext';

const ThemeToggle: React.FC = () => {
  let theme: string;
  let toggleTheme: () => void;
  let isTransitioning: boolean;
  try {
    const ctx = useTheme();
    theme = ctx.theme;
    toggleTheme = ctx.toggleTheme;
    isTransitioning = ctx.isTransitioning;
  } catch (e) {
    // No ThemeProvider in tree, skip rendering toggle
    return null;
  }
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!svgRef.current) return;
    
    const svg = svgRef.current;
    
    if (theme === 'light') {
      // Sun animation
      const rays = svg.querySelectorAll('.sun-ray');
      rays.forEach((ray, i) => {
        (ray as SVGElement).style.opacity = '1';
        (ray as SVGElement).style.transform = 'scale(1)';
        (ray as SVGElement).style.transitionDelay = `${i * 0.05}s`;
      });
      
      // Hide moon elements
      const moonElements = svg.querySelectorAll('.moon-element');
      moonElements.forEach(el => {
        (el as SVGElement).style.opacity = '0';
      });
      
      // Show sun circle
      const sunCircle = svg.querySelector('.sun-circle');
      if (sunCircle) {
        (sunCircle as SVGElement).style.fill = '#FFD700';
        (sunCircle as SVGElement).style.opacity = '1';
      }
    } else {
      // Moon animation
      const rays = svg.querySelectorAll('.sun-ray');
      rays.forEach(ray => {
        (ray as SVGElement).style.opacity = '0';
        (ray as SVGElement).style.transform = 'scale(0)';
      });
      
      // Show moon elements
      const moonElements = svg.querySelectorAll('.moon-element');
      moonElements.forEach((el, i) => {
        (el as SVGElement).style.opacity = '1';
        (el as SVGElement).style.transitionDelay = `${i * 0.1}s`;
      });
      
      // Change sun circle to moon
      const sunCircle = svg.querySelector('.sun-circle');
      if (sunCircle) {
        (sunCircle as SVGElement).style.fill = '#3B82F6';
        (sunCircle as SVGElement).style.opacity = '1';
      }
    }
  }, [theme]);

  return (
    <button
      onClick={toggleTheme}
      className={`relative p-2 rounded-full focus:outline-none transition-colors duration-500 ${
        isTransitioning ? 'animate-theme-transition' : ''}`}
      aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
    >
      <svg
        ref={svgRef}
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 32 32"
        width="32"
        height="32"
        className="transition-transform duration-1000"
      >
        {/* Sun/Moon Circle */}
        <circle
          className="sun-circle transition-all duration-1000"
          cx="16"
          cy="16"
          r="10"
          fill="#FFD700"
        />
        
        {/* Sun Rays */}
        <line
          className="sun-ray transition-all duration-500"
          x1="16"
          y1="2"
          x2="16"
          y2="6"
          stroke="#FFD700"
          strokeWidth="2.5"
          strokeLinecap="round"
        />
        <line
          className="sun-ray transition-all duration-500"
          x1="16"
          y1="26"
          x2="16"
          y2="30"
          stroke="#FFD700"
          strokeWidth="2.5"
          strokeLinecap="round"
        />
        <line
          className="sun-ray transition-all duration-500"
          x1="2"
          y1="16"
          x2="6"
          y2="16"
          stroke="#FFD700"
          strokeWidth="2.5"
          strokeLinecap="round"
        />
        <line
          className="sun-ray transition-all duration-500"
          x1="26"
          y1="16"
          x2="30"
          y2="16"
          stroke="#FFD700"
          strokeWidth="2.5"
          strokeLinecap="round"
        />
        <line
          className="sun-ray transition-all duration-500"
          x1="6"
          y1="6"
          x2="9"
          y2="9"
          stroke="#FFD700"
          strokeWidth="2.5"
          strokeLinecap="round"
        />
        <line
          className="sun-ray transition-all duration-500"
          x1="23"
          y1="23"
          x2="26"
          y2="26"
          stroke="#FFD700"
          strokeWidth="2.5"
          strokeLinecap="round"
        />
        <line
          className="sun-ray transition-all duration-500"
          x1="6"
          y1="26"
          x2="9"
          y2="23"
          stroke="#FFD700"
          strokeWidth="2.5"
          strokeLinecap="round"
        />
        <line
          className="sun-ray transition-all duration-500"
          x1="23"
          y1="9"
          x2="26"
          y2="6"
          stroke="#FFD700"
          strokeWidth="2.5"
          strokeLinecap="round"
        />
        
        {/* Moon Elements (initially hidden) */}
        <circle
          className="moon-element transition-all duration-500 opacity-0"
          cx="11"
          cy="12"
          r="2.5"
          fill="#FFFFFF"
        />
        <circle
          className="moon-element transition-all duration-500 opacity-0"
          cx="21"
          cy="18"
          r="2"
          fill="#FFFFFF"
        />
        <circle
          className="moon-element transition-all duration-500 opacity-0"
          cx="16"
          cy="9"
          r="1.8"
          fill="#FFFFFF"
        />
      </svg>
    </button>
  );
};

export default ThemeToggle; 