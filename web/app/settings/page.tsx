'use client';

import { useState, useEffect } from 'react';
import { Card, CardBody, CardHeader, Input, Button, Divider, Chip, Accordion, AccordionItem } from "@heroui/react";
import { Settings, Key, Brain, Mic, Shield, Eye, EyeOff, Save, CheckCircle, AlertTriangle, ArrowLeft } from 'lucide-react';
import Link from 'next/link';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface AppSetting {
    key: string;
    value: string;
    category: string;
    label: string;
    required: number;
    secret: number;
}

interface ValidationResult {
    valid: boolean;
    missing: string[];
}

// ---------------------------------------------------------------------------
// Category metadata
// ---------------------------------------------------------------------------

const CATEGORY_META: Record<string, { label: string; icon: React.ReactNode; description: string }> = {
    llm: {
        label: 'IA / LLM',
        icon: <Brain className="w-5 h-5" />,
        description: 'Claves de API para modelos de lenguaje (NVIDIA NIM, Minimax)',
    },
    models: {
        label: 'Modelos',
        icon: <Settings className="w-5 h-5" />,
        description: 'Nombres de modelos y parámetros de generación',
    },
    voice: {
        label: 'Voz / Riva',
        icon: <Mic className="w-5 h-5" />,
        description: 'Speech-to-text con NVIDIA Riva y NGC',
    },
    auth: {
        label: 'Autenticación',
        icon: <Shield className="w-5 h-5" />,
        description: 'Secretos de NextAuth y proveedores OAuth',
    },
    observability: {
        label: 'Observabilidad',
        icon: <Eye className="w-5 h-5" />,
        description: 'Logfire y trazabilidad (opcional)',
    },
    pipeline: {
        label: 'Pipeline',
        icon: <Settings className="w-5 h-5" />,
        description: 'Configuración del pipeline de transcripciones',
    },
};

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function SettingsPage() {
    const [settings, setSettings] = useState<AppSetting[]>([]);
    const [editedValues, setEditedValues] = useState<Record<string, string>>({});
    const [revealedKeys, setRevealedKeys] = useState<Set<string>>(new Set());
    const [validation, setValidation] = useState<ValidationResult | null>(null);
    const [saving, setSaving] = useState(false);
    const [saved, setSaved] = useState(false);
    const [loading, setLoading] = useState(true);

    // Fetch all settings on mount
    useEffect(() => {
        fetchSettings();
        fetchValidation();
    }, []);

    async function fetchSettings() {
        try {
            const res = await fetch('/api/settings/', { credentials: 'include' });
            const data = await res.json();
            setSettings(data.settings || []);
        } catch (err) {
            console.error('Failed to fetch settings:', err);
        } finally {
            setLoading(false);
        }
    }

    async function fetchValidation() {
        try {
            const res = await fetch('/api/settings/validate', { credentials: 'include' });
            const data = await res.json();
            setValidation(data);
        } catch (err) {
            console.error('Failed to validate settings:', err);
        }
    }

    function handleChange(key: string, value: string) {
        setEditedValues(prev => ({ ...prev, [key]: value }));
        setSaved(false);
    }

    function toggleReveal(key: string) {
        setRevealedKeys(prev => {
            const next = new Set(prev);
            if (next.has(key)) next.delete(key);
            else next.add(key);
            return next;
        });
    }

    async function saveAll() {
        setSaving(true);
        try {
            const updates = Object.entries(editedValues).map(([key, value]) => ({ key, value }));
            if (updates.length === 0) return;

            await fetch('/api/settings/', {
                method: 'PUT',
                credentials: 'include',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ settings: updates }),
            });

            setSaved(true);
            setEditedValues({});
            // Refresh
            await fetchSettings();
            await fetchValidation();
        } catch (err) {
            console.error('Failed to save settings:', err);
        } finally {
            setSaving(false);
        }
    }

    // Group settings by category
    const grouped = settings.reduce<Record<string, AppSetting[]>>((acc, s) => {
        (acc[s.category] ??= []).push(s);
        return acc;
    }, {});

    const hasChanges = Object.keys(editedValues).length > 0;

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
            </div>
        );
    }

    return (
        <div className="max-w-4xl mx-auto p-6 space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <Link href="/dashboard">
                        <Button isIconOnly variant="light" size="sm">
                            <ArrowLeft className="w-5 h-5" />
                        </Button>
                    </Link>
                    <div>
                        <h1 className="text-2xl font-bold">Configuración</h1>
                        <p className="text-sm text-default-500">
                            Administra tus claves de API y parámetros del sistema
                        </p>
                    </div>
                </div>

                <div className="flex items-center gap-2">
                    {validation && !validation.valid && (
                        <Chip
                            color="warning"
                            variant="flat"
                            startContent={<AlertTriangle className="w-3 h-3" />}
                        >
                            {validation.missing.length} clave(s) faltante(s)
                        </Chip>
                    )}
                    {validation?.valid && (
                        <Chip
                            color="success"
                            variant="flat"
                            startContent={<CheckCircle className="w-3 h-3" />}
                        >
                            Todo configurado
                        </Chip>
                    )}
                </div>
            </div>

            {/* Missing keys alert */}
            {validation && !validation.valid && (
                <Card className="border border-warning-200 bg-warning-50/50">
                    <CardBody className="p-4">
                        <div className="flex items-start gap-3">
                            <AlertTriangle className="w-5 h-5 text-warning mt-0.5" />
                            <div>
                                <p className="font-medium text-warning-700">Claves requeridas faltantes</p>
                                <p className="text-sm text-warning-600 mt-1">
                                    Configura las siguientes claves para que la aplicación funcione correctamente:
                                </p>
                                <div className="flex flex-wrap gap-1 mt-2">
                                    {validation.missing.map(k => (
                                        <Chip key={k} size="sm" variant="flat" color="warning">{k}</Chip>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </CardBody>
                </Card>
            )}

            {/* Settings by category */}
            <Accordion variant="splitted" selectionMode="multiple" defaultExpandedKeys={["llm", "voice"]}>
                {Object.entries(grouped).map(([category, items]) => {
                    const meta = CATEGORY_META[category] || {
                        label: category,
                        icon: <Settings className="w-5 h-5" />,
                        description: '',
                    };

                    return (
                        <AccordionItem
                            key={category}
                            aria-label={meta.label}
                            title={
                                <div className="flex items-center gap-2">
                                    {meta.icon}
                                    <span className="font-semibold">{meta.label}</span>
                                    <Chip size="sm" variant="flat">{items.length}</Chip>
                                </div>
                            }
                            subtitle={meta.description}
                        >
                            <div className="space-y-4 pb-2">
                                {items.map(setting => {
                                    const isSecret = setting.secret === 1;
                                    const isRevealed = revealedKeys.has(setting.key);
                                    const currentValue = editedValues[setting.key] ?? setting.value;
                                    const isEdited = setting.key in editedValues;
                                    const isMissing = validation?.missing.includes(setting.key);

                                    return (
                                        <div key={setting.key} className="flex items-end gap-2">
                                            <Input
                                                label={setting.label || setting.key}
                                                placeholder={`Ingresa ${setting.label || setting.key}`}
                                                type={isSecret && !isRevealed ? 'password' : 'text'}
                                                value={currentValue}
                                                onChange={e => handleChange(setting.key, e.target.value)}
                                                variant="bordered"
                                                className="flex-1"
                                                color={isMissing ? 'warning' : isEdited ? 'primary' : 'default'}
                                                description={
                                                    setting.required
                                                        ? '⚡ Requerido'
                                                        : 'Opcional'
                                                }
                                                endContent={
                                                    isSecret ? (
                                                        <button
                                                            type="button"
                                                            onClick={() => toggleReveal(setting.key)}
                                                            className="text-default-400 hover:text-default-600"
                                                        >
                                                            {isRevealed
                                                                ? <EyeOff className="w-4 h-4" />
                                                                : <Eye className="w-4 h-4" />
                                                            }
                                                        </button>
                                                    ) : null
                                                }
                                            />
                                        </div>
                                    );
                                })}
                            </div>
                        </AccordionItem>
                    );
                })}
            </Accordion>

            {/* Save button */}
            <div className="sticky bottom-4 flex justify-end">
                <Button
                    color={saved ? 'success' : 'primary'}
                    size="lg"
                    isDisabled={!hasChanges && !saving}
                    isLoading={saving}
                    onPress={saveAll}
                    startContent={saved ? <CheckCircle className="w-5 h-5" /> : <Save className="w-5 h-5" />}
                    className="shadow-lg"
                >
                    {saved ? 'Guardado' : `Guardar cambios (${Object.keys(editedValues).length})`}
                </Button>
            </div>
        </div>
    );
}
