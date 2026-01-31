/**
 * API Client for REST endpoints
 */

const API_URL = '/api';

export const apiClient = {
    async getLatestTranscription() {
        const res = await fetch(`${API_URL}/transcriptions/latest/`);
        if (!res.ok) throw new Error('Failed to fetch');
        return res.json();
    },

    async getTranscriptions(limit: number = 50) {
        const res = await fetch(`${API_URL}/transcriptions/?limit=${limit}`);
        if (!res.ok) throw new Error('Failed to fetch list');
        return res.json();
    },

    async getTranscription(id: string) {
        const res = await fetch(`${API_URL}/transcriptions/${id}`);
        if (!res.ok) throw new Error('Failed to fetch transcription');
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
    },

    async deleteTranscription(id: string) {
        const res = await fetch(`${API_URL}/transcriptions/${id}`, {
            method: 'DELETE'
        });
        if (!res.ok) throw new Error('Failed to delete');
        return res.json();
    }
};
