import { getSocket, connectSocket, disconnectSocket } from '../../utils/socket';
import { io } from 'socket.io-client';

jest.mock('socket.io-client', () => {
    const mockSocket = {
        connected: false,
        connect: jest.fn(function (this: { connected: boolean }) {
            this.connected = true;
        }),
        disconnect: jest.fn(function (this: { connected: boolean }) {
            this.connected = false;
        }),
    };
    return {
        io: jest.fn(() => mockSocket),
    };
});

describe('socket utility', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    test('getSocket initializes and returns socket singleton', () => {
        const s1 = getSocket();
        const s2 = getSocket();

        expect(io).toHaveBeenCalledTimes(1);
        expect(s1).toBe(s2);
    });

    test('connectSocket connects socket when not connected', () => {
        const socket = getSocket();
        socket.connected = false;

        connectSocket();
        expect(socket.connect).toHaveBeenCalledTimes(1);
    });

    test('disconnectSocket disconnects socket when connected', () => {
        const socket = getSocket();
        socket.connected = true;

        disconnectSocket();
        expect(socket.disconnect).toHaveBeenCalledTimes(1);
    });
});
