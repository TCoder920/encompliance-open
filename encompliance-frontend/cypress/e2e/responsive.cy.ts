/**
 * Responsive testing with Cypress
 * Tests key pages at different viewport sizes
 */

import { BREAKPOINTS } from '../../src/tests/utils/responsive-test-utils';

// Key pages to test for responsive behavior
const PAGES = [
  '/',              // Home
  '/login',         // Login (if exists)
  '/dashboard',     // Dashboard (if exists)
  '/profile',       // Profile (if exists)
  '/settings'       // Settings (if exists)
];

describe('Responsive Layout Tests', () => {
  // Test each breakpoint
  Object.entries(BREAKPOINTS).forEach(([breakpoint, width]) => {
    context(`Viewport: ${breakpoint} (${width}px)`, () => {
      beforeEach(() => {
        // Set viewport size before each test
        cy.viewport(width, 800);
      });
      
      // Test each page at current breakpoint
      PAGES.forEach(page => {
        it(`should render ${page} correctly`, () => {
          // Visit the page
          cy.visit(page).then(() => {
            // Adds a small delay for any animations to complete
            cy.wait(500);
            
            // Take a screenshot for visual verification
            cy.screenshot(`${breakpoint}-${page.replace(/\//g, '-')}`);
            
            // Check for common responsive issues:
            
            // No horizontal overflow
            cy.document().then(doc => {
              const body = doc.body;
              expect(body.scrollWidth).to.be.lte(width);
            });
            
            // No elements extending beyond viewport
            cy.get('body *').each(($el) => {
              const rect = $el[0].getBoundingClientRect();
              
              // Element should not extend beyond viewport width
              expect(rect.right).to.be.lte(width + 5); // Small tolerance
              
              // Text should be readable (not too small)
              if ($el.is('p, h1, h2, h3, h4, h5, h6, span, a, button, label, input')) {
                const fontSize = parseFloat(window.getComputedStyle($el[0]).fontSize);
                expect(fontSize).to.be.gte(12); // Minimum font size
              }
            });
          });
        });
      });
    });
  });
}); 