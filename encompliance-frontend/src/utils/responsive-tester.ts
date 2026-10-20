/*
  Description: ResponsiveTester utility for development. Provides a UI overlay to test responsive breakpoints and viewport sizes.
  Purpose: Helps developers quickly verify layout behavior across device sizes during development.
*/

/**
 * ResponsiveTester - A utility to help test responsive layouts
 * 
 * This can be included in development mode and provides a simple
 * UI for switching between viewport sizes to test responsiveness.
 */

import { BREAKPOINTS, HEIGHTS } from '../tests/utils/responsive-test-utils';

class ResponsiveTester {
  private container: HTMLDivElement | null = null;
  private isVisible = false;

  constructor() {
    this.init();
  }

  private init(): void {
    // Create container UI
    this.container = document.createElement('div');
    this.container.style.position = 'fixed';
    this.container.style.bottom = '20px';
    this.container.style.right = '20px';
    this.container.style.backgroundColor = '#333';
    this.container.style.color = 'white';
    this.container.style.padding = '10px';
    this.container.style.borderRadius = '5px';
    this.container.style.boxShadow = '0 2px 10px rgba(0, 0, 0, 0.2)';
    this.container.style.zIndex = '9999';
    this.container.style.display = 'none';
    
    // Title
    const title = document.createElement('h4');
    title.textContent = 'Responsive Tester';
    title.style.margin = '0 0 10px 0';
    title.style.fontSize = '14px';
    this.container.appendChild(title);
    
    // Breakpoint buttons
    const buttonContainer = document.createElement('div');
    buttonContainer.style.display = 'flex';
    buttonContainer.style.flexWrap = 'wrap';
    buttonContainer.style.gap = '5px';
    
    Object.entries(BREAKPOINTS).forEach(([breakpoint, width]) => {
      const button = document.createElement('button');
      button.textContent = `${breakpoint} (${width}px)`;
      button.style.margin = '2px';
      button.style.padding = '4px 8px';
      button.style.fontSize = '12px';
      button.style.border = 'none';
      button.style.borderRadius = '3px';
      button.style.cursor = 'pointer';
      button.style.backgroundColor = '#555';
      button.style.color = 'white';
      
      button.addEventListener('click', () => {
        this.resizeViewport(breakpoint as keyof typeof BREAKPOINTS);
      });
      
      buttonContainer.appendChild(button);
    });
    
    this.container.appendChild(buttonContainer);
    
    // Toggle button (floating)
    const toggleButton = document.createElement('button');
    toggleButton.textContent = 'RWD';
    toggleButton.style.position = 'fixed';
    toggleButton.style.bottom = '20px';
    toggleButton.style.right = '20px';
    toggleButton.style.backgroundColor = '#007bff';
    toggleButton.style.color = 'white';
    toggleButton.style.width = '40px';
    toggleButton.style.height = '40px';
    toggleButton.style.borderRadius = '50%';
    toggleButton.style.border = 'none';
    toggleButton.style.cursor = 'pointer';
    toggleButton.style.boxShadow = '0 2px 5px rgba(0, 0, 0, 0.2)';
    toggleButton.style.zIndex = '10000';
    toggleButton.style.fontSize = '12px';
    toggleButton.style.fontWeight = 'bold';
    
    toggleButton.addEventListener('click', () => {
      this.toggleVisibility();
    });
    
    // Append to body
    document.body.appendChild(this.container);
    document.body.appendChild(toggleButton);
  }
  
  private toggleVisibility(): void {
    this.isVisible = !this.isVisible;
    if (this.container) {
      this.container.style.display = this.isVisible ? 'block' : 'none';
    }
  }
  
  private resizeViewport(breakpoint: keyof typeof BREAKPOINTS): void {
    const width = BREAKPOINTS[breakpoint];
    window.resizeTo(width, HEIGHTS.medium);
    
    // Log current dimensions
    console.log(`Viewport resized to ${width}x${HEIGHTS.medium} (${breakpoint})`);
    
    // Update document title with current breakpoint for easy reference
    const originalTitle = document.title.split(' | ')[0];
    document.title = `${originalTitle} | ${breakpoint} ${width}px`;
  }
}

// Initialize if in development mode
if (process.env.NODE_ENV !== 'production') {
  window.addEventListener('load', () => {
    new ResponsiveTester();
    console.log('ResponsiveTester initialized. Click the RWD button to toggle the panel.');
  });
}

export default ResponsiveTester; 