/**
 * Accessibility testing with Cypress and axe-core
 * Covers public surfaces plus authenticated role journeys.
 */

const PUBLIC_PAGES = ['/', '/login', '/support'];

const ROLE_SCENARIOS = [
  {
    name: 'Facility Admin workspace',
    user: {
      id: 1,
      full_name: 'Facility Admin',
      subscription_status: 'pro',
      user_role: 'facility_admin'
    },
    routes: ['/dashboard', '/tasks', '/training']
  },
  {
    name: 'Team Member workspace',
    user: {
      id: 2,
      full_name: 'Team Member',
      subscription_status: 'free',
      user_role: 'team_member'
    },
    routes: ['/notes', '/activities']
  }
];

const seedAuthenticatedState = (userFixture: any) => {
  cy.intercept('GET', '/api/users/me', {
    statusCode: 200,
    body: userFixture
  }).as('getCurrentUser');

  cy.intercept('GET', '/api/**', {
    statusCode: 200,
    body: []
  });

  cy.intercept('POST', '/api/**', {
    statusCode: 200,
    body: { success: true }
  });
};

const visitAndScan = (path: string, opts: { authenticated?: boolean } = {}) => {
  cy.visit(path, {
    onBeforeLoad(win) {
      if (opts.authenticated) {
        win.localStorage.setItem('token', 'test-token');
      }
    }
  });

  cy.wait(500);
  cy.checkA11y();
};

describe('Accessibility Tests', () => {
  PUBLIC_PAGES.forEach((page) => {
    it(`meets WCAG guidance on public page ${page}`, () => {
      visitAndScan(page);
    });
  });

  ROLE_SCENARIOS.forEach((scenario) => {
    describe(`${scenario.name}`, () => {
      beforeEach(() => {
        seedAuthenticatedState(scenario.user);
      });

      scenario.routes.forEach((route) => {
        it(`has no critical violations on ${route}`, () => {
          visitAndScan(route, { authenticated: true });
          cy.wait('@getCurrentUser');
        });
      });
    });
  });
});