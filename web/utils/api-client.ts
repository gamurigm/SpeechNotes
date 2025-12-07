/**
 * API Client for REST endpoints
 */

const API_URL = 'http://localhost:8001/api';

export const apiClient = {
    async getLatestTranscription() {
        const res = await fetch(`${API_URL}/transcriptions/latest`);
        if (!res.ok) throw new Error('Failed to fetch');
        return res.json();
    },

    async updateTranscription(id: string, content: string) {
        const res = await fetch(`${API_URL}/transcriptions/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content })
        });
        if (!res.ok) throw new Error('Failed to update');
        return res.json();
    }
};
