import { defineConfig } from 'cypress';

export default defineConfig({
  e2e: {
    baseUrl: 'http://localhost:5174',
    supportFile: 'cypress/commands.ts',
    specPattern: 'cypress/e2e/**/*.cy.{js,jsx,ts,tsx}',
    setupNodeEvents(on, config) {
      on('task', {
        log(message) {
          console.log(message);
          return null;
        }
      });
      return config;
    }
  },
  video: false,
  viewportWidth: 1280,
  viewportHeight: 800,
  screenshotOnRunFailure: true,
  screenshotsFolder: 'cypress/screenshots',
}); 