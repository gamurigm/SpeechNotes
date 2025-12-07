/**
 * ConfigManager - Singleton Pattern Implementation
 * 
 * Propósito: Garantizar que una clase tenga una única instancia y proporcionar
 * un punto de acceso global a ella.
 * 
 * Esta clase centraliza la configuración de la aplicación, asegurando que
 * solo exista una instancia de configuración en todo el sistema.
 */

export class ConfigManager {
    private static _instance: ConfigManager | null = null;

    // Variables de configuración
    private readonly nextAuthUrl: string;
    private readonly nextAuthSecret: string;
    private readonly googleClientId: string;
    private readonly googleClientSecret: string;
    private readonly githubId: string;
    private readonly githubSecret: string;
    private readonly databaseUrl: string;

    /**
     * Constructor privado para prevenir instanciación directa
     */
    private constructor() {
        // Cargar variables de entorno
        this.nextAuthUrl = process.env.NEXTAUTH_URL || 'http://localhost:3006';
        this.nextAuthSecret = process.env.NEXTAUTH_SECRET || '';
        this.googleClientId = process.env.GOOGLE_CLIENT_ID || '';
        this.googleClientSecret = process.env.GOOGLE_CLIENT_SECRET || '';
        this.githubId = process.env.GITHUB_ID || '';
        this.githubSecret = process.env.GITHUB_SECRET || '';
        this.databaseUrl = process.env.DATABASE_URL || '';
    }

    /**
     * Método estático para obtener la única instancia de ConfigManager
     * @returns La única instancia de ConfigManager
     */
    public static getInstance(): ConfigManager {
        if (ConfigManager._instance === null) {
            ConfigManager._instance = new ConfigManager();
        }
        return ConfigManager._instance;
    }

    /**
     * Obtener configuración de NextAuth
     */
    public getNextAuthConfig() {
        return {
            url: this.nextAuthUrl,
            secret: this.nextAuthSecret,
        };
    }

    /**
     * Obtener configuración de Google OAuth
     */
    public getGoogleConfig() {
        return {
            clientId: this.googleClientId,
            clientSecret: this.googleClientSecret,
        };
    }

    /**
     * Obtener configuración de GitHub OAuth
     */
    public getGitHubConfig() {
        return {
            clientId: this.githubId,
            clientSecret: this.githubSecret,
        };
    }

    /**
     * Obtener configuración de la base de datos
     */
    public getDatabaseConfig() {
        return {
            url: this.databaseUrl,
        };
    }

    /**
     * Obtener todas las configuraciones
     */
    public getAllConfig() {
        return {
            nextAuth: this.getNextAuthConfig(),
            google: this.getGoogleConfig(),
            github: this.getGitHubConfig(),
            database: this.getDatabaseConfig(),
        };
    }
}

// Exportar una función helper para obtener la instancia
export const getConfig = () => ConfigManager.getInstance();
