import { defineConfig } from 'cypress';
import { startMockBackend, type MockBackend } from './tests/support/mockBackend';

let mockBackend: MockBackend | undefined;

export default defineConfig({
    allowCypressEnv: false,
    e2e: {
        baseUrl: 'http://127.0.0.1:3006',
        specPattern: 'tests/e2e/**/*.cy.{js,jsx,ts,tsx}',
        supportFile: 'tests/setup/cypress.ts',
        async setupNodeEvents(on, config) {
            mockBackend ??= await startMockBackend();

            if (!config.isInteractive) {
                on('after:run', async () => {
                    await mockBackend?.close();
                    mockBackend = undefined;
                });
            }

            return config;
        },
    },
    screenshotsFolder: 'tests/evidence/screenshots',
    trashAssetsBeforeRuns: false,
    videosFolder: 'tests/evidence/videos',
    video: false,
    viewportHeight: 900,
    viewportWidth: 1440,
});
