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
    private baseUrl: string = 'http://127.0.0.1:9443/api';

    private constructor() { }

    public static getInstance(): ApiClient {
        if (!ApiClient.instance) {
            ApiClient.instance = new ApiClient();
        }
        return ApiClient.instance;
    }

    private async request<T>(endpoint: string, options?: RequestInit, retries = 3): Promise<T> {
        const url = `${this.baseUrl}${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            'x-api-key': 'dev-secret-api-key',
            ...(options?.headers || {}),
        };

        let lastError;
        for (let i = 0; i < retries; i++) {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 15000); // 15s timeout

            try {
                const response = await fetch(url, {
                    ...options,
                    headers,
                    signal: controller.signal
                });
                clearTimeout(timeoutId);

                if (!response.ok) {
                    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
                    console.error(`[ApiClient] Error ${response.status}:`, error);
                    // Don't retry client errors (4xx), only server errors (5xx) or network errors
                    if (response.status >= 400 && response.status < 500) {
                        throw new Error(error.detail || `API Error: ${response.statusText}`);
                    }
                    throw new Error(error.detail || `Server Error: ${response.statusText}`);
                }

                return response.json();
            } catch (error: any) {
                clearTimeout(timeoutId);
                console.warn(`[ApiClient] Attempt ${i + 1}/${retries} failed for ${url}:`, error);
                lastError = error;
                if (error.name === 'AbortError') throw new Error('Request timeout');
                // Wait before retrying (exponential backoff: 500ms, 1000ms, 2000ms)
                if (i < retries - 1) await new Promise(r => setTimeout(r, 500 * Math.pow(2, i)));
            }
        }

        console.error(`[ApiClient] All ${retries} attempts failed for ${url}`);
        throw lastError;
    }

    private transcriptionCache: Map<string, any> = new Map();

    public async getLatestTranscription() {
        return this.request('/transcriptions/latest');
    }

    public async listTranscriptions(limit: number = 50) {
        return this.request(`/transcriptions?limit=${limit}`);
    }

    public async getTranscription(id: string) {
        if (this.transcriptionCache.has(id)) {
            console.log(`[ApiClient] Cache hit for ${id}`);
            return this.transcriptionCache.get(id);
        }

        const data = await this.request(`/transcriptions/${id}`);
        this.transcriptionCache.set(id, data);
        return data;
    }

    public async updateTranscription(id: string, content: string) {
        const response: any = await this.request(`/transcriptions/${id}`, {
            method: 'PUT',
            body: JSON.stringify({ content })
        });

        // Update cache with new content if successful
        if (this.transcriptionCache.has(id)) {
            const cached = this.transcriptionCache.get(id);
            this.transcriptionCache.set(id, { ...cached, content });
        }

        return response;
    }

    public async deleteTranscription(id: string) {
        const response = await this.request(`/transcriptions/${id}`, {
            method: 'DELETE'
        });

        // Remove from cache
        if (this.transcriptionCache.has(id)) {
            this.transcriptionCache.delete(id);
        }

        return response;
    }

    public async search(query: string) {
        return this.request(`/transcriptions/search?q=${encodeURIComponent(query)}`);
    }

    // Método para invalidar cache manualmente si es necesario (ej: desde componentes)
    public invalidateCache(id?: string) {
        if (id) {
            this.transcriptionCache.delete(id);
        } else {
            this.transcriptionCache.clear();
        }
    }
}
