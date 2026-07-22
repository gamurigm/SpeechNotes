import { ApiClient } from '../../services/ApiClient';

describe('ApiClient', () => {
    let client: ApiClient;
    const globalFetch = global.fetch;

    beforeEach(() => {
        client = ApiClient.getInstance();
        client.invalidateCache();
        jest.clearAllMocks();
        global.fetch = jest.fn();
    });

    afterAll(() => {
        global.fetch = globalFetch;
    });

    test('should return the same singleton instance', () => {
        const instance1 = ApiClient.getInstance();
        const instance2 = ApiClient.getInstance();
        expect(instance1).toBe(instance2);
    });

    test('getLatestTranscription makes GET request to /transcriptions/latest', async () => {
        const mockData = { id: '1', content: 'test transcription' };
        (global.fetch as jest.Mock).mockResolvedValueOnce({
            ok: true,
            json: async () => mockData,
        });

        const result = await client.getLatestTranscription();
        expect(result).toEqual(mockData);
        expect(global.fetch).toHaveBeenCalledWith(
            'http://127.0.0.1:9443/api/transcriptions/latest',
            expect.objectContaining({
                headers: expect.objectContaining({
                    'Content-Type': 'application/json',
                    'x-api-key': 'dev-secret-api-key',
                }),
            })
        );
    });

    test('listTranscriptions passes limit parameter', async () => {
        const mockData = [{ id: '1' }, { id: '2' }];
        (global.fetch as jest.Mock).mockResolvedValueOnce({
            ok: true,
            json: async () => mockData,
        });

        const result = await client.listTranscriptions(10);
        expect(result).toEqual(mockData);
        expect(global.fetch).toHaveBeenCalledWith(
            'http://127.0.0.1:9443/api/transcriptions?limit=10',
            expect.anything()
        );
    });

    test('getTranscription uses cache on repeated calls', async () => {
        const mockData = { id: 'abc', content: 'hello' };
        (global.fetch as jest.Mock).mockResolvedValueOnce({
            ok: true,
            json: async () => mockData,
        });

        const firstCall = await client.getTranscription('abc');
        expect(firstCall).toEqual(mockData);
        expect(global.fetch).toHaveBeenCalledTimes(1);

        // Second call should return from cache without fetching again
        const secondCall = await client.getTranscription('abc');
        expect(secondCall).toEqual(mockData);
        expect(global.fetch).toHaveBeenCalledTimes(1);
    });

    test('updateTranscription sends PUT request and updates cache', async () => {
        const initialData = { id: 'item1', content: 'old' };
        (global.fetch as jest.Mock).mockResolvedValueOnce({
            ok: true,
            json: async () => initialData,
        });

        // Seed cache
        await client.getTranscription('item1');

        const updateResponse = { id: 'item1', content: 'new' };
        (global.fetch as jest.Mock).mockResolvedValueOnce({
            ok: true,
            json: async () => updateResponse,
        });

        const result = await client.updateTranscription('item1', 'new');
        expect(result).toEqual(updateResponse);
        expect(global.fetch).toHaveBeenLastCalledWith(
            'http://127.0.0.1:9443/api/transcriptions/item1',
            expect.objectContaining({
                method: 'PUT',
                body: JSON.stringify({ content: 'new' }),
            })
        );

        // Verify cache updated
        const cached = await client.getTranscription('item1');
        expect(cached).toEqual({ id: 'item1', content: 'new' });
    });

    test('deleteTranscription sends DELETE request and removes from cache', async () => {
        const initialData = { id: 'del1', content: 'delete me' };
        (global.fetch as jest.Mock).mockResolvedValueOnce({
            ok: true,
            json: async () => initialData,
        });

        // Seed cache
        await client.getTranscription('del1');

        (global.fetch as jest.Mock).mockResolvedValueOnce({
            ok: true,
            json: async () => ({ success: true }),
        });

        await client.deleteTranscription('del1');
        expect(global.fetch).toHaveBeenLastCalledWith(
            'http://127.0.0.1:9443/api/transcriptions/del1',
            expect.objectContaining({ method: 'DELETE' })
        );

        // Next call should fetch again because cache entry was deleted
        (global.fetch as jest.Mock).mockResolvedValueOnce({
            ok: true,
            json: async () => ({ id: 'del1', content: 're-fetched' }),
        });

        const refetched = await client.getTranscription('del1');
        expect(refetched).toEqual({ id: 'del1', content: 're-fetched' });
        expect(global.fetch).toHaveBeenCalledTimes(3);
    });

    test('search encodes query string', async () => {
        (global.fetch as jest.Mock).mockResolvedValueOnce({
            ok: true,
            json: async () => [],
        });

        await client.search('hello world & more');
        expect(global.fetch).toHaveBeenCalledWith(
            'http://127.0.0.1:9443/api/transcriptions/search?q=hello%20world%20%26%20more',
            expect.anything()
        );
    });

    test('handles 4xx client errors', async () => {
        (global.fetch as jest.Mock).mockResolvedValue({
            ok: false,
            status: 404,
            statusText: 'Not Found',
            json: async () => ({ detail: 'Item not found' }),
        });

        await expect(client.getLatestTranscription()).rejects.toThrow('Item not found');
    });

    test('invalidateCache clears single item or all cache', async () => {
        (global.fetch as jest.Mock).mockResolvedValue({
            ok: true,
            json: async () => ({ data: 'ok' }),
        });

        await client.getTranscription('1');
        await client.getTranscription('2');

        client.invalidateCache('1');
        await client.getTranscription('2'); // Cache hit
        expect(global.fetch).toHaveBeenCalledTimes(2);

        await client.getTranscription('1'); // Cache miss, fetches
        expect(global.fetch).toHaveBeenCalledTimes(3);

        client.invalidateCache(); // Clears all
        await client.getTranscription('2');
        expect(global.fetch).toHaveBeenCalledTimes(4);
    });
});
