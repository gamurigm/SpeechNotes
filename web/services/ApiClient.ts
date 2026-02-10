/**
 * ApiClient - Singleton & Facade Pattern
 * 
 * Provides a unified interface for API communication.
 * Hides the complexity of fetch, headers, and error handling.
 * 
 * Design Patterns:
 * - Singleton: Ensures only one instance manages API configuration.
 * - Facade: Simplifies the fetch API into domain-specific methods.
 */

export class ApiClient {
    private static instance: ApiClient;
    private baseUrl: string = '/api';

    private constructor() { }

    public static getInstance(): ApiClient {
        if (!ApiClient.instance) {
            ApiClient.instance = new ApiClient();
        }
        return ApiClient.instance;
    }

    private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
        const url = `${this.baseUrl}${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            ...(options?.headers || {})
        };

        const response = await fetch(url, { ...options, headers });

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
            throw new Error(error.detail || `API Error: ${response.statusText}`);
        }

        return response.json();
    }

    public async getLatestTranscription() {
        return this.request('/transcriptions/latest/');
    }

    public async listTranscriptions(limit: number = 50) {
        return this.request(`/transcriptions/?limit=${limit}`);
    }

    public async getTranscription(id: string) {
        return this.request(`/transcriptions/${id}`);
    }

    public async updateTranscription(id: string, content: string) {
        return this.request(`/transcriptions/${id}`, {
            method: 'PUT',
            body: JSON.stringify({ content })
        });
    }

    public async deleteTranscription(id: string) {
        return this.request(`/transcriptions/${id}`, {
            method: 'DELETE'
        });
    }

    public async search(query: string) {
        return this.request(`/transcriptions/search?q=${encodeURIComponent(query)}`);
    }
}
