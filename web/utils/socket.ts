/**
 * Socket.IO Client
 */

import { io, Socket } from 'socket.io-client';

let socket: Socket | null = null;

export function getSocket(): Socket {
    if (!socket) {
        socket = io('http://localhost:8000', {
            transports: ['websocket', 'polling'],
            autoConnect: false
        });
    }
    return socket;
}

export function connectSocket(): void {
    const socket = getSocket();
    if (!socket.connected) {
        socket.connect();
    }
}

export function disconnectSocket(): void {
    if (socket?.connected) {
        socket.disconnect();
    }
}
