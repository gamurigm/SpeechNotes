'use client';

import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Edit, Save, X, Download } from 'lucide-react';
import dynamic from 'next/dynamic';

const MDEditor = dynamic(
    () => import('@uiw/react-md-editor').then((mod) => mod.default),
    { ssr: false }
);

interface Props {
    content: string;
    onSave: (content: string) => Promise<void>;
}

export function MarkdownViewer({ content, onSave }: Props) {
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
        <div className="h-full flex flex-col bg-white">
            <div className="flex justify-between items-center p-4 border-b bg-white sticky top-0 z-10">
                <h2 className="text-xl font-bold text-gray-900">
                    Última Clase
                </h2>
                <div className="flex gap-2">
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
                    <div className="prose prose-lg max-w-none">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {content}
                        </ReactMarkdown>
                    </div>
                )}
            </div>
        </div>
    );
}
