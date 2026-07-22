import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ChatSidebar } from '@/app/dashboard/components/ChatSidebar';
import { useBackground } from '@/app/providers';

jest.mock('remark-gfm', () => ({ __esModule: true, default: jest.fn() }));

jest.mock('react-markdown', () => {
    const React = jest.requireActual<typeof import('react')>('react');
    return {
        __esModule: true,
        default: ({ children, components = {} }: { children: string; components?: Record<string, React.ElementType> }) => {
            const renderPart = (name: string, child?: React.ReactNode, props: Record<string, unknown> = {}) => (
                React.createElement(components[name] ?? name, { key: name, ...props }, child)
            );
            const text = String(children).replace(/^#+\s*/, '');
            return React.createElement('div', null,
                renderPart('h1', text), renderPart('h2', text), renderPart('h3', text),
                renderPart('p', text), renderPart('ul', renderPart('li', text)),
                renderPart('ol', renderPart('li', text)), renderPart('strong', text),
                renderPart('blockquote', text), renderPart('code', text), renderPart('hr'),
            );
        },
    };
});

jest.mock('@/app/providers', () => ({
    useBackground: jest.fn(),
}));

const mockedUseBackground = jest.mocked(useBackground);
const mockedFetch = jest.fn();

function streamResponse(events: string[]): Response {
    const chunks = events.map((event) => Uint8Array.from(Buffer.from(event)));
    let index = 0;

    return {
        ok: true,
        body: {
            getReader: () => ({
                read: jest.fn(async () => index < chunks.length
                    ? { done: false, value: chunks[index++] }
                    : { done: true, value: undefined }),
            }),
        },
    } as unknown as Response;
}

describe('ChatSidebar', () => {
    beforeEach(() => {
        mockedUseBackground.mockReturnValue({ themeType: 'dark' } as ReturnType<typeof useBackground>);
        mockedFetch.mockReset();
        global.fetch = mockedFetch;
    });

    it('muestra el contexto y ejecuta los controles del encabezado', async () => {
        const onClose = jest.fn();
        const onToggleExpand = jest.fn();

        render(
            <ChatSidebar
                activeDocId="doc-1"
                activeDocName="transcription_clase_prueba_formatted.md"
                isExpanded
                isFormatted
                onClose={onClose}
                onToggleExpand={onToggleExpand}
            />,
        );

        expect(screen.getByText('clase_prueba')).toBeInTheDocument();
        expect(screen.getByText('AI Formatted')).toBeInTheDocument();
        expect(screen.getByText(/listo para responder preguntas/i)).toBeInTheDocument();

        await userEvent.click(screen.getByTitle('Contraer'));
        await userEvent.click(screen.getByTitle('Cerrar'));
        await userEvent.click(screen.getByTitle(/Desactivar análisis profundo/i));

        expect(onToggleExpand).toHaveBeenCalledTimes(1);
        expect(onClose).toHaveBeenCalledTimes(1);
        expect(screen.getByText('Fast')).toBeInTheDocument();
    });

    it('consume la respuesta SSE y presenta Markdown y razonamiento', async () => {
        mockedFetch.mockResolvedValue(streamResponse([
            'evento ignorado\n\n',
            'data: {malformado}\n\n',
            'data: {"content":"[Analizando: clase] <think>Razonamiento"}\n\n',
            'data: {"content":" interno</think>\\n\\n## Respuesta"}\n\n',
            'data: {"content":" final"}',
        ]));
        const warn = jest.spyOn(console, 'warn').mockImplementation(() => undefined);

        render(
            <ChatSidebar
                activeDocId="doc-2"
                activeDocContent="Contenido cargado"
                activeFile="transcription_respaldo.md"
            />,
        );

        const input = screen.getByPlaceholderText('Analizar documentos...');
        await userEvent.type(input, 'Resume esta clase');
        fireEvent.submit(input.closest('form') as HTMLFormElement);

        expect((await screen.findAllByText('Resume esta clase')).length).toBeGreaterThan(0);
        expect((await screen.findAllByText(/Razonamiento interno/i)).length).toBeGreaterThan(0);
        expect((await screen.findAllByRole('heading', { name: /Respuesta final/i })).length).toBeGreaterThan(0);
        await waitFor(() => expect(input).toHaveFocus());

        const request = mockedFetch.mock.calls[0];
        const payload = JSON.parse((request[1] as RequestInit).body as string);
        expect(request[0]).toBe('/api/chat/stream');
        expect(payload).toMatchObject({
            doc_id: 'doc-2',
            active_file: 'transcription_respaldo.md',
            doc_content: 'Contenido cargado',
            thinking: true,
        });
        expect(warn).toHaveBeenCalled();
        warn.mockRestore();
    });

    it('muestra un error recuperable cuando el backend rechaza la consulta', async () => {
        mockedUseBackground.mockReturnValue({ themeType: 'light' } as ReturnType<typeof useBackground>);
        mockedFetch.mockResolvedValue({ ok: false } as Response);
        const error = jest.spyOn(console, 'error').mockImplementation(() => undefined);

        render(<ChatSidebar activeFile="transcription_fallback.md" />);

        const input = screen.getByPlaceholderText('Esperando documento...');
        await userEvent.type(input, 'Pregunta sin documento');
        fireEvent.submit(input.closest('form') as HTMLFormElement);

        expect((await screen.findAllByText(/Error: No se pudo obtener respuesta/i)).length).toBeGreaterThan(0);
        expect(screen.queryByText('Verified')).not.toBeInTheDocument();
        expect(error).toHaveBeenCalled();
        error.mockRestore();
    });
});
