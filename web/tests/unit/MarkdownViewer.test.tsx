import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MarkdownViewer } from '@/app/dashboard/components/MarkdownViewer';
import { useBackground } from '@/app/providers';

jest.mock('remark-gfm', () => ({ __esModule: true, default: jest.fn() }));

jest.mock('react-markdown', () => {
    const React = jest.requireActual<typeof import('react')>('react');
    return {
        __esModule: true,
        default: ({ components = {} }: { children: string; components?: Record<string, React.ElementType> }) => {
            const renderPart = (name: string, child?: React.ReactNode, props: Record<string, unknown> = {}) => (
                React.createElement(components[name] ?? name, { key: `${name}-${JSON.stringify(props)}`, ...props }, child)
            );
            return React.createElement('div', null,
                renderPart('h1', 'Introducción'), renderPart('h2', 'Detalles'), renderPart('h3', 'Subtema'),
                renderPart('p', 'Texto importante para buscar'),
                renderPart('ul', renderPart('li', 'Primer elemento')),
                renderPart('ol', renderPart('li', 'Segundo elemento')),
                renderPart('strong', 'importante'), renderPart('em', 'énfasis'),
                renderPart('blockquote', 'Una cita útil'),
                renderPart('pre', renderPart('code', 'const value = true;', { className: 'language-ts' })),
                renderPart('code', 'código corto'),
                renderPart('table', renderPart('tbody', renderPart('tr', renderPart('td', 'B')))),
                renderPart('a', 'enlace', { href: 'https://example.com' }), renderPart('hr'),
            );
        },
    };
});

jest.mock('@/app/providers', () => ({
    useBackground: jest.fn(),
}));

jest.mock('next/dynamic', () => ({
    __esModule: true,
    default: () => function EditorMock({ value, onChange }: {
        value: string;
        onChange: (value?: string) => void;
    }) {
        return (
            <textarea
                aria-label="Editor Markdown"
                value={value}
                onChange={(event) => onChange(event.target.value)}
            />
        );
    },
}));

const mockedUseBackground = jest.mocked(useBackground);
const clipboardWrite = jest.fn();

const richContent = `Original: 2026-07-21
# Introducción
Texto **importante** para buscar, con *énfasis* y [enlace](https://example.com).

## Detalles
- Primer elemento
- Segundo elemento

> Una cita útil

\`código corto\`

\`\`\`ts
const value = true;
\`\`\`

| Columna | Valor |
| --- | --- |
| A | B |

---`;

function defaultProps() {
    return {
        content: richContent,
        onSave: jest.fn(async () => undefined),
        onDelete: jest.fn(async () => undefined),
        onFormatProfessional: jest.fn(async () => undefined),
        nav: {
            onPrev: jest.fn(),
            onNext: jest.fn(),
            hasPrev: true,
            hasNext: true,
            index: 1,
            total: 4,
            onJump: jest.fn(),
        },
        title: 'Clase de Calidad',
        zoomLevel: 110,
        isFormatted: true,
        searchQuery: 'buscar',
    };
}

describe('MarkdownViewer', () => {
    beforeEach(() => {
        mockedUseBackground.mockReturnValue({ themeType: 'dark' } as ReturnType<typeof useBackground>);
        clipboardWrite.mockReset();
        Object.defineProperty(navigator, 'clipboard', {
            configurable: true,
            value: { writeText: clipboardWrite.mockResolvedValue(undefined) },
        });
        jest.spyOn(window, 'alert').mockImplementation(() => undefined);
    });

    afterEach(() => {
        jest.restoreAllMocks();
    });

    it('renderiza el documento, navegación, búsqueda y controles de lectura', async () => {
        const props = defaultProps();
        const { container } = render(<MarkdownViewer {...props} />);

        expect(screen.getByText('Clase de Calidad')).toBeInTheDocument();
        expect(screen.getByText('• 2026-07-21 •')).toBeInTheDocument();
        expect(screen.getByText('AI Formatted')).toBeInTheDocument();
        expect(screen.getByText('buscar')).toHaveClass('bg-blue-500/30');
        expect(screen.getByRole('table')).toBeInTheDocument();

        fireEvent.keyDown(window, { key: 'ArrowLeft' });
        fireEvent.keyDown(window, { key: 'ArrowRight' });
        expect(props.nav.onPrev).toHaveBeenCalledTimes(1);
        expect(props.nav.onNext).toHaveBeenCalledTimes(1);

        const jump = screen.getByLabelText('Ir a transcripción');
        await userEvent.type(jump, '3{Enter}');
        expect(props.nav.onJump).toHaveBeenCalledWith(2);

        await userEvent.click(screen.getByTitle('Esquema del documento'));
        expect(screen.getByText('Esquema')).toBeInTheDocument();
        await userEvent.click(screen.getAllByRole('button', { name: /Introducción/ }).at(-1) as HTMLElement);
        expect(HTMLElement.prototype.scrollIntoView).toHaveBeenCalled();

        await userEvent.click(screen.getByTitle('Copiar como Markdown'));
        await userEvent.click(screen.getByTitle('Copiar como texto plano'));
        expect(clipboardWrite).toHaveBeenNthCalledWith(1, richContent);
        expect(clipboardWrite.mock.calls[1][0]).not.toContain('# Introducción');

        await userEvent.click(screen.getByTitle('Modo lectura sin distracciones'));
        expect(screen.getByTitle('Salir del modo lectura (Esc)')).toBeInTheDocument();
        fireEvent.keyDown(document, { key: 'Escape' });

        const contentSection = screen.getByLabelText('Contenido de la transcripción');
        Object.defineProperties(contentSection, {
            scrollTop: { configurable: true, value: 50 },
            scrollHeight: { configurable: true, value: 200 },
            clientHeight: { configurable: true, value: 100 },
        });
        fireEvent.scroll(contentSection);
        expect(container.querySelector('[style*="width: 50%"]')).toBeInTheDocument();
    });

    it('permite personalizar, editar, guardar, formatear y eliminar', async () => {
        mockedUseBackground.mockReturnValue({ themeType: 'light' } as ReturnType<typeof useBackground>);
        const props = defaultProps();
        render(<MarkdownViewer {...props} />);

        await userEvent.click(screen.getByTitle('Personalizar Tipografía'));
        await userEvent.selectOptions(screen.getByLabelText('Familia'), 'Georgia, serif');
        fireEvent.change(screen.getByLabelText('Tamaño'), { target: { value: '20' } });
        expect(screen.getByText('20px')).toBeInTheDocument();

        await userEvent.click(screen.getByTitle('Volver a refinar con IA'));
        expect(props.onFormatProfessional).toHaveBeenCalledTimes(1);

        await userEvent.click(screen.getByTitle('Editar'));
        const editor = screen.getByLabelText('Editor Markdown');
        await userEvent.clear(editor);
        await userEvent.type(editor, '# Contenido actualizado');
        await userEvent.click(screen.getByRole('button', { name: 'Guardar Cambios' }));
        await waitFor(() => expect(props.onSave).toHaveBeenCalledWith('# Contenido actualizado'));

        await userEvent.click(screen.getByTitle('Eliminar clase'));
        await userEvent.click(screen.getByTitle('Confirmar eliminación'));
        await waitFor(() => expect(props.onDelete).toHaveBeenCalledTimes(1));
    });

    it('copia una selección y maneja exportación y errores de guardado', async () => {
        const props = defaultProps();
        props.onSave.mockRejectedValueOnce(new Error('fallo simulado'));
        const open = jest.spyOn(window, 'open').mockReturnValue(null);
        const error = jest.spyOn(console, 'error').mockImplementation(() => undefined);
        render(<MarkdownViewer {...props} />);

        const selection = {
            toString: () => 'texto seleccionado',
            rangeCount: 1,
            getRangeAt: () => ({
                getBoundingClientRect: () => ({ left: 10, width: 20, top: 30 }),
            }),
        } as unknown as Selection;
        jest.spyOn(window, 'getSelection').mockReturnValue(selection);
        fireEvent.mouseUp(screen.getByLabelText('Contenido de la transcripción'));
        await userEvent.click(await screen.findByRole('button', { name: /Copiar/ }));
        expect(clipboardWrite).toHaveBeenCalledWith('texto seleccionado');

        await userEvent.click(screen.getByTitle('Exportar / Imprimir PDF'));
        expect(open).toHaveBeenCalled();

        await userEvent.click(screen.getByTitle('Editar'));
        await userEvent.click(screen.getByRole('button', { name: 'Guardar Cambios' }));
        await waitFor(() => expect(window.alert).toHaveBeenCalledWith('Error al guardar'));
        expect(error).toHaveBeenCalled();
    });
});
