import { createServer, type ServerResponse } from 'node:http';
import { Server as SocketServer } from 'socket.io';

const HOST = '127.0.0.1';
const PORT = 9443;

function sendJson(response: ServerResponse, status: number, body: unknown) {
    response.writeHead(status, {
        'Access-Control-Allow-Headers': 'Content-Type,x-api-key',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
        'Access-Control-Allow-Origin': '*',
        'Content-Type': 'application/json',
    });
    response.end(JSON.stringify(body));
}

export type MockBackend = {
    close: () => Promise<void>;
};

export async function startMockBackend(): Promise<MockBackend> {
    const server = createServer((request, response) => {
        if (request.method === 'OPTIONS') {
            sendJson(response, 204, null);
            return;
        }

        const url = new URL(request.url ?? '/', `http://${HOST}:${PORT}`);

        if (url.pathname === '/api/config/vad') {
            sendJson(response, 200, { voice_threshold: 500, silence_threshold: 200 });
            return;
        }

        if (url.pathname === '/api/transcriptions') {
            sendJson(response, 200, {
                items: [{
                    id: 'e2e-transcription-1',
                    filename: 'Clase de calidad simulada',
                    date: '2026-07-19T12:00:00Z',
                    is_formatted: false,
                }],
            });
            return;
        }

        if (url.pathname === '/api/transcriptions/e2e-transcription-1') {
            sendJson(response, 200, {
                id: 'e2e-transcription-1',
                content: '# Clase de calidad simulada\n\nTranscripción histórica cargada por Cypress.',
            });
            return;
        }

        if (url.pathname === '/api/transcriptions/latest') {
            sendJson(response, 200, null);
            return;
        }

        sendJson(response, 404, { detail: `Ruta simulada no disponible: ${url.pathname}` });
    });

    const io = new SocketServer(server, {
        cors: { origin: '*' },
        transports: ['polling', 'websocket'],
    });

    io.on('connection', (socket) => {
        socket.emit('connected', { message: 'Backend Cypress conectado' });

        socket.on('start_recording', () => {
            socket.emit('recording_started', { max_segment_seconds: 8 });
            setTimeout(() => {
                socket.emit('transcription_status', {
                    event: 'transcription_received',
                    segment_id: 1,
                });
                socket.emit('transcription', {
                    text: 'Texto de prueba recibido desde el backend simulado.',
                    timestamp: '00:01',
                });
            }, 250);
        });

        socket.on('stop_recording', () => {
            socket.emit('recording_stopped', { success: true });
            setTimeout(() => socket.emit('processing_complete', { success: true }), 50);
        });
    });

    await new Promise<void>((resolve, reject) => {
        server.once('error', reject);
        server.listen(PORT, HOST, () => {
            server.off('error', reject);
            resolve();
        });
    });

    return {
        close: () => new Promise<void>((resolve, reject) => {
            io.close((error) => error ? reject(error) : resolve());
        }),
    };
}
