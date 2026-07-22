import { POST } from '../../app/api/register/route';
import { prisma } from '../../lib/prisma';
import { hashPassword } from '../../lib/password';

jest.mock('next/server', () => ({
    NextResponse: {
        json: (body: unknown, init?: { status?: number }) => ({
            status: init?.status ?? 200,
            json: async () => body,
        }),
    },
}));

jest.mock('../../lib/prisma', () => ({
    prisma: {
        user: {
            create: jest.fn(),
            findFirst: jest.fn(),
        },
    },
}));

jest.mock('../../lib/password', () => ({
    hashPassword: jest.fn(async (password: string) => `hashed:${password}`),
}));

const prismaUser = prisma.user as unknown as {
    create: jest.Mock;
    findFirst: jest.Mock;
};
const hashPasswordMock = hashPassword as jest.MockedFunction<typeof hashPassword>;

function createRequest(body: unknown, origin = 'http://localhost:3006'): Request {
    const headers = new Map<string, string>([
        ['content-type', 'application/json'],
        ['origin', origin],
    ]);

    return {
        url: 'http://localhost:3006/api/register',
        headers: {
            get(name: string) {
                return headers.get(name.toLowerCase()) ?? null;
            },
        },
        json: async () => body,
    } as unknown as Request;
}

function validRegistration(overrides: Record<string, string> = {}) {
    return {
        name: 'Ana Perez',
        email: 'ana.perez@example.com',
        username: 'ana_perez',
        password: 'Valid123',
        ...overrides,
    };
}

describe('POST /api/register', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        delete process.env.NEXTAUTH_URL;
    });

    test('rejects usernames with script characters before touching the database', async () => {
        const response = await POST(createRequest(validRegistration({
            username: '<script>alert(1)</script>',
        })));

        expect(response.status).toBe(400);
        expect(prismaUser.findFirst).not.toHaveBeenCalled();
        expect(prismaUser.create).not.toHaveBeenCalled();
    });

    test('rejects cross-origin register requests', async () => {
        const response = await POST(createRequest(
            validRegistration({
                username: 'nuevo_usuario',
            }),
            'http://evil.example',
        ));

        expect(response.status).toBe(403);
        expect(prismaUser.findFirst).not.toHaveBeenCalled();
    });

    test('does not create duplicated usernames', async () => {
        prismaUser.findFirst.mockResolvedValue({ id: 'existing-user' });

        const response = await POST(createRequest(validRegistration({
            username: 'Usuario_1',
        })));
        const body = await response.json();

        expect(response.status).toBe(409);
        expect(body.error).toContain('ya esta registrado');
        expect(prismaUser.create).not.toHaveBeenCalled();
    });

    test('rejects invalid full names before touching the database', async () => {
        const response = await POST(createRequest(validRegistration({
            name: '<script>alert(1)</script>',
        })));

        expect(response.status).toBe(400);
        expect(prismaUser.findFirst).not.toHaveBeenCalled();
        expect(prismaUser.create).not.toHaveBeenCalled();
    });

    test('rejects invalid email addresses before touching the database', async () => {
        const response = await POST(createRequest(validRegistration({
            email: 'correo-invalido',
        })));

        expect(response.status).toBe(400);
        expect(prismaUser.findFirst).not.toHaveBeenCalled();
        expect(prismaUser.create).not.toHaveBeenCalled();
    });

    test('rejects weak passwords before touching the database', async () => {
        const response = await POST(createRequest(validRegistration({
            password: 'password',
        })));

        expect(response.status).toBe(400);
        expect(prismaUser.findFirst).not.toHaveBeenCalled();
        expect(prismaUser.create).not.toHaveBeenCalled();
    });

    test('hashes the password and creates a normalized local user', async () => {
        prismaUser.findFirst.mockResolvedValue(null);
        prismaUser.create.mockResolvedValue({ id: 'new-user' });

        const response = await POST(createRequest(validRegistration({
            name: '  Ana   Perez  ',
            email: 'ANA.PEREZ@EXAMPLE.COM',
            username: 'Usuario_1',
        })));

        expect(response.status).toBe(201);
        expect(hashPasswordMock).toHaveBeenCalledWith('Valid123');
        expect(prismaUser.create).toHaveBeenCalledWith({
            data: {
                username: 'usuario_1',
                email: 'ana.perez@example.com',
                name: 'Ana Perez',
                password: 'hashed:Valid123',
            },
            select: { id: true },
        });
    });
});
