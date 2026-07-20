import { defineConfig } from 'cypress';
import { startMockBackend, type MockBackend } from './tests/support/mockBackend';

let mockBackend: MockBackend | undefined;

export default defineConfig({
    e2e: {
        baseUrl: 'http://127.0.0.1:3006',
        specPattern: 'tests/e2e/**/*.cy.{js,jsx,ts,tsx}',
        supportFile: 'tests/setup/cypress.ts',
        setupNodeEvents(on) {
            on('before:run', async () => {
                mockBackend = await startMockBackend();
            });

            on('after:run', async () => {
                await mockBackend?.close();
                mockBackend = undefined;
            });

        },
    },
    screenshotsFolder: 'tests/evidence/screenshots',
    videosFolder: 'tests/evidence/videos',
    video: false,
    viewportHeight: 900,
    viewportWidth: 1440,
});
