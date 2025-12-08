'use client';

import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Edit, Save, X, Download, ChevronLeft, ChevronRight } from 'lucide-react';
import dynamic from 'next/dynamic';

const MDEditor = dynamic(
    () => import('@uiw/react-md-editor').then((mod) => mod.default),
    { ssr: false }
);

interface Props {
    content: string;
    onSave: (content: string) => Promise<void>;
    nav?: {
        onPrev?: () => void;
        onNext?: () => void;
        hasPrev?: boolean;
        hasNext?: boolean;
        index?: number;
        total?: number;
    };
}

export function MarkdownViewer({ content, onSave, nav }: Props) {
    const [isEditing, setIsEditing] = useState(false);
    const [editedContent, setEditedContent] = useState(content);
    const [isSaving, setIsSaving] = useState(false);

    const handleSave = async () => {
        setIsSaving(true);
        try {
            await onSave(editedContent);
            setIsEditing(false);
        } catch (error) {
            console.error('Error saving:', error);
            alert('Error al guardar');
        } finally {
            setIsSaving(false);
        }
    };

    const handleCancel = () => {
        setEditedContent(content);
        setIsEditing(false);
    };

    return (
        <div className="h-full flex flex-col bg-white rounded-lg shadow">
            <div className="flex justify-between items-center p-4 border-b bg-white sticky top-0 z-10">
                <h2 className="text-xl font-bold text-gray-900">
                    Última Clase
                </h2>
                <div className="flex gap-2">
                    {nav && (
                        <div className="flex items-center mr-4">
                            <button
                                onClick={nav.onPrev}
                                disabled={!nav.hasPrev}
                                aria-label="Anterior"
                                className="p-2 rounded-md bg-gray-100 hover:bg-gray-200 disabled:opacity-50 mr-2"
                            >
                                <ChevronLeft size={18} />
                            </button>
                            <button
                                onClick={nav.onNext}
                                disabled={!nav.hasNext}
                                aria-label="Siguiente"
                                className="p-2 rounded-md bg-gray-100 hover:bg-gray-200 disabled:opacity-50"
                            >
                                <ChevronRight size={18} />
                            </button>
                            {typeof nav.index === 'number' && typeof nav.total === 'number' && (
                                <span className="ml-3 text-sm text-gray-600">{nav.index + 1}/{nav.total}</span>
                            )}
                        </div>
                    )}
                    {isEditing ? (
                        <>
                            <button
                                onClick={handleCancel}
                                className="flex items-center gap-2 px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition"
                            >
                                <X size={20} />
                                Cancelar
                            </button>
                            <button
                                onClick={handleSave}
                                disabled={isSaving}
                                className="flex items-center gap-2 px-4 py-2 text-white bg-blue-500 rounded-lg hover:bg-blue-600 transition disabled:opacity-50"
                            >
                                <Save size={20} />
                                {isSaving ? 'Guardando...' : 'Guardar'}
                            </button>
                        </>
                    ) : (
                        <>
                            <button
                                onClick={() => setIsEditing(true)}
                                className="flex items-center gap-2 px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition"
                            >
                                <Edit size={20} />
                                Editar
                            </button>
                            <button
                                className="flex items-center gap-2 px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition"
                            >
                                <Download size={20} />
                                PDF
                            </button>
                        </>
                    )}
                </div>
            </div>

            <div className="flex-1 overflow-y-auto p-6">
                {isEditing ? (
                    <div data-color-mode="light">
                        <MDEditor
                            value={editedContent}
                            onChange={(val) => setEditedContent(val || '')}
                            height="100%"
                            preview="edit"
                        />
                    </div>
                ) : (
                    <div className="markdown-content">
                        <ReactMarkdown 
                            remarkPlugins={[remarkGfm]}
                            components={{
                                h1: ({node, ...props}) => <h1 className="text-3xl font-bold mt-6 mb-4 text-gray-900" {...props} />,
                                h2: ({node, ...props}) => <h2 className="text-2xl font-bold mt-5 mb-3 text-gray-900" {...props} />,
                                h3: ({node, ...props}) => <h3 className="text-xl font-bold mt-4 mb-2 text-gray-800" {...props} />,
                                h4: ({node, ...props}) => <h4 className="text-lg font-bold mt-3 mb-2 text-gray-800" {...props} />,
                                h5: ({node, ...props}) => <h5 className="text-base font-bold mt-2 mb-1 text-gray-800" {...props} />,
                                h6: ({node, ...props}) => <h6 className="text-sm font-bold text-gray-800" {...props} />,
                                p: ({node, ...props}) => <p className="text-base leading-7 text-gray-700 mb-4" {...props} />,
                                ul: ({node, ...props}) => <ul className="list-disc list-inside text-gray-700 mb-4" {...props} />,
                                ol: ({node, ...props}) => <ol className="list-decimal list-inside text-gray-700 mb-4" {...props} />,
                                li: ({node, ...props}) => <li className="mb-1 ml-2" {...props} />,
                                strong: ({node, ...props}) => <strong className="font-bold text-gray-900" {...props} />,
                                em: ({node, ...props}) => <em className="italic text-gray-800" {...props} />,
                                code: ({node, inline, ...props}: any) => 
                                    inline 
                                        ? <code className="bg-gray-100 px-2 py-1 rounded text-sm text-red-600 font-mono" {...props} />
                                        : <code className="block bg-gray-100 p-4 rounded text-sm text-gray-900 font-mono overflow-x-auto mb-4" {...props} />,
                                blockquote: ({node, ...props}) => <blockquote className="border-l-4 border-blue-500 pl-4 italic text-gray-700 my-4" {...props} />,
                                hr: () => <hr className="my-6 border-gray-300" />,
                                table: ({node, ...props}) => <table className="w-full border-collapse border border-gray-300 my-4" {...props} />,
                                th: ({node, ...props}) => <th className="border border-gray-300 bg-gray-100 px-4 py-2 text-left font-bold" {...props} />,
                                td: ({node, ...props}) => <td className="border border-gray-300 px-4 py-2" {...props} />,
                                a: ({node, ...props}) => <a className="text-blue-600 hover:underline" {...props} />,
                            }}
                        >
                            {content}
                        </ReactMarkdown>
                    </div>
                )}
            </div>
        </div>
    );
}
