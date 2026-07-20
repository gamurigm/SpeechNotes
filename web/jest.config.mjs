import nextJest from 'next/jest.js';

const createJestConfig = nextJest({
    dir: './',
});

const config = {
    clearMocks: true,
    coverageDirectory: 'tests/evidence/coverage',
    moduleNameMapper: {
        '^@/(.*)$': '<rootDir>/$1',
    },
    setupFilesAfterEnv: ['<rootDir>/tests/setup/jest.setup.ts'],
    testEnvironment: 'jsdom',
    testMatch: ['<rootDir>/tests/unit/**/*.test.ts?(x)'],
};

export default createJestConfig(config);
