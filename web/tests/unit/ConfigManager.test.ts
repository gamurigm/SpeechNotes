import { ConfigManager, getConfig } from '../../config/ConfigManager';

describe('ConfigManager', () => {
    const originalEnv = process.env;

    beforeEach(() => {
        jest.resetModules();
        (ConfigManager as unknown as { _instance: null })._instance = null;
        process.env = { ...originalEnv };
    });

    afterAll(() => {
        process.env = originalEnv;
    });

    test('should return singleton instance', () => {
        const instance1 = ConfigManager.getInstance();
        const instance2 = getConfig();
        expect(instance1).toBe(instance2);
    });

    test('should use default configuration values when env vars are missing', () => {
        delete process.env.NEXTAUTH_URL;
        delete process.env.NEXTAUTH_SECRET;

        const config = ConfigManager.getInstance();
        expect(config.getNextAuthConfig()).toEqual({
            url: 'http://localhost:3006',
            secret: '',
        });
    });

    test('should load environment variables correctly', () => {
        process.env.NEXTAUTH_URL = 'http://example.com';
        process.env.GOOGLE_CLIENT_ID = 'google-id';
        process.env.GITHUB_ID = 'github-id';
        process.env.DATABASE_URL = 'file:./dev.db';

        const config = ConfigManager.getInstance();
        expect(config.getAllConfig()).toEqual({
            nextAuth: {
                url: 'http://example.com',
                secret: '',
            },
            google: {
                clientId: 'google-id',
                clientSecret: '',
            },
            github: {
                clientId: 'github-id',
                clientSecret: '',
            },
            database: {
                url: 'file:./dev.db',
            },
        });
    });
});
