/// <reference types="cypress" />

/**
 * End-to-end test for the login to dashboard flow
 */
describe('Login to Dashboard Flow', () => {
  beforeEach(() => {
    // Intercept API calls to mock responses
    cy.intercept('POST', '/api/auth/login', {
      statusCode: 200,
      body: {
        success: true,
        token: 'test-token',
        user: {
          id: 1,
          username: 'testuser',
          email: 'test@example.com',
        },
      },
    }).as('loginRequest');

    cy.intercept('GET', '/api/user/me', {
      statusCode: 200,
      body: {
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
      },
    }).as('getUserRequest');

    cy.intercept('GET', '/api/user/documents', {
      statusCode: 200,
      body: [
        {
          id: 'doc1',
          name: 'Test Document 1',
          date_uploaded: '2023-06-01T10:00:00Z',
          size: 1024,
        },
        {
          id: 'doc2',
          name: 'Test Document 2',
          date_uploaded: '2023-06-02T11:00:00Z',
          size: 2048,
        },
      ],
    }).as('getDocumentsRequest');

    cy.intercept('GET', '/api/user/queries', {
      statusCode: 200,
      body: [
        {
          id: 1,
          query: 'What is compliance?',
          timestamp: '2023-06-01T10:00:00Z',
          response: 'Compliance refers to following regulations and standards.',
        },
      ],
    }).as('getQueriesRequest');

    // Visit the login page
    cy.visit('/login');
  });

  it('should login and navigate to dashboard successfully', () => {
    // Check login page elements
    cy.contains('h1', 'Login').should('be.visible');
    cy.get('input[type="email"]').should('be.visible');
    cy.get('input[type="password"]').should('be.visible');
    cy.contains('button', 'Login').should('be.visible');

    // Fill in login form
    cy.get('input[type="email"]').type('test@example.com');
    cy.get('input[type="password"]').type('password123');

    // Submit login form
    cy.contains('button', 'Login').click();

    // Wait for login request to complete
    cy.wait('@loginRequest');

    // Verify redirection to dashboard
    cy.url().should('include', '/dashboard');

    // Check dashboard elements
    cy.contains('h1', 'Dashboard').should('be.visible');
    cy.contains('Welcome back, testuser').should('be.visible');

    // Wait for dashboard data to load
    cy.wait('@getDocumentsRequest');
    cy.wait('@getQueriesRequest');

    // Verify documents section
    cy.contains('h2', 'Your Documents').should('be.visible');
    cy.contains('Test Document 1').should('be.visible');
    cy.contains('Test Document 2').should('be.visible');

    // Verify recent queries section
    cy.contains('h2', 'Recent Queries').should('be.visible');
    cy.contains('What is compliance?').should('be.visible');

    // Test navigation to another page
    cy.contains('a', 'Upload Document').click();
    cy.url().should('include', '/upload');

    // Go back to dashboard
    cy.go('back');
    cy.url().should('include', '/dashboard');

    // Test logout functionality
    cy.contains('button', 'Logout').click();
    cy.url().should('include', '/login');
  });

  it('should show error message with invalid credentials', () => {
    // Override login intercept to return error
    cy.intercept('POST', '/api/auth/login', {
      statusCode: 401,
      body: {
        success: false,
        message: 'Invalid email or password',
      },
    }).as('failedLoginRequest');

    // Fill in login form with invalid credentials
    cy.get('input[type="email"]').type('wrong@example.com');
    cy.get('input[type="password"]').type('wrongpassword');

    // Submit login form
    cy.contains('button', 'Login').click();

    // Wait for login request to complete
    cy.wait('@failedLoginRequest');

    // Verify error message is displayed
    cy.contains('Invalid email or password').should('be.visible');

    // Verify URL is still login page
    cy.url().should('include', '/login');
  });
}); 