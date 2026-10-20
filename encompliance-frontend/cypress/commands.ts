// This file configures Cypress with custom commands

import 'cypress-axe';

/**
 * Overwrite cy.checkA11y to ensure axe is injected and violations grouped by impact.
 */
Cypress.Commands.overwrite(
  'checkA11y',
  (originalFn, context, options, violationCallback, skipFailures) => {
    cy.injectAxe();
    return originalFn(
      context,
      {
        runOnly: {
          type: 'tag',
          values: ['wcag2a', 'wcag2aa']
        },
        ...options
      },
      (violations) => {
        if (violations.length > 0) {
          cy.task('log', `${violations.length} accessibility violation(s) detected`);
          const grouped = violations.reduce<Record<string, any[]>>((acc, violation) => {
            const impact = violation.impact || 'unknown';
            if (!acc[impact]) {
              acc[impact] = [];
            }
            acc[impact].push(violation);
            return acc;
          }, {});

          Object.entries(grouped).forEach(([impact, violationsForImpact]) => {
            cy.task('log', `Impact ${impact}: ${violationsForImpact.length} violations`);
            violationsForImpact.forEach((violation) => {
              cy.task('log', `- ${violation.id}: ${violation.description} (${violation.nodes.length} elements)`);
            });
          });
        }

        violationCallback?.(violations);
      },
      skipFailures
    );
  }
);

// Type definitions for custom commands
declare global {
  namespace Cypress {
    interface Chainable {
      /**
       * Custom command to check accessibility on the current page
       * @example cy.checkA11y()
       */
      checkA11y(): Chainable<any>
    }
  }
} 