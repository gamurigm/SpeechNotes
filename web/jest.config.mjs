import nextJest from 'next/jest.js';

const createJestConfig = nextJest({
    dir: './',
});

const config = {
    clearMocks: true,
    coverageDirectory: 'tests/evidence/coverage',
    collectCoverageFrom: [
        'app/dashboard/components/ChatSidebar.tsx',
        'app/dashboard/components/LiveTranscription.tsx',
        'app/dashboard/components/MarkdownViewer.tsx',
        'app/dashboard/components/RecordingPanel.tsx',
        'services/ApiClient.ts',
    ],
    coverageReporters: [
        ['lcov', { projectRoot: '..' }],
        'text-summary',
    ],
    coverageThreshold: {
        global: {
            branches: 75,
            functions: 80,
            lines: 85,
            statements: 80,
        },
    },
    moduleNameMapper: {
        '^@/(.*)$': '<rootDir>/$1',
    },
    setupFilesAfterEnv: ['<rootDir>/tests/setup/jest.setup.ts'],
    testEnvironment: 'jsdom',
    testMatch: ['<rootDir>/tests/unit/**/*.test.ts?(x)'],
};

export default createJestConfig(config);
