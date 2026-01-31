'use client';

import React, { useRef } from 'react';
import { useBackground, BackgroundTheme } from '../../providers';
import { Palette, Check, Monitor, Moon, Sun, Zap, Upload, Image as ImageIcon, X } from 'lucide-react';
import { Button, Popover, PopoverTrigger, PopoverContent, Divider, Slider } from "@heroui/react";

const themes: { id: BackgroundTheme; name: string; icon: React.ReactNode; color: string }[] = [
    { id: 'cyberpunk', name: 'Cyber Blue', icon: <Zap size={14} />, color: 'bg-blue-600' },
    { id: 'midnight', name: 'Midnight', icon: <Moon size={14} />, color: 'bg-violet-700' },
    { id: 'emerald', name: 'Emerald', icon: <Zap size={14} />, color: 'bg-emerald-600' },
    { id: 'abyss', name: 'Abyss black', icon: <Monitor size={14} />, color: 'bg-slate-900' },
    { id: 'pure-light', name: 'Pure Light', icon: <Sun size={14} />, color: 'bg-slate-200' },
];

export function ThemeSettings() {
    const { theme, setTheme, customBg, setCustomBg, glassOpacity, setGlassOpacity, themeType } = useBackground();
    const fileInputRef = useRef<HTMLInputElement>(null);
    const isLight = themeType === 'light';

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            const reader = new FileReader();
            reader.onloadend = () => {
                const img = new Image();
                img.onload = () => {
                    const MAX_WIDTH = 1920;
                    const MAX_HEIGHT = 1080;
                    let width = img.width;
                    let height = img.height;

                    if (width > MAX_WIDTH) {
                        height *= MAX_WIDTH / width;
                        width = MAX_WIDTH;
                    }
                    if (height > MAX_HEIGHT) {
                        width *= MAX_HEIGHT / height;
                        height = MAX_HEIGHT;
                    }

                    const canvas = document.createElement('canvas');
                    canvas.width = width;
                    canvas.height = height;
                    const ctx = canvas.getContext('2d');
                    if (ctx) {
                        ctx.drawImage(img, 0, 0, width, height);
                        const compressedDataUrl = canvas.toDataURL('image/jpeg', 0.8);
                        setCustomBg(compressedDataUrl);
                    } else {
                        setCustomBg(reader.result as string);
                    }
                };
                img.src = reader.result as string;
            };
            reader.readAsDataURL(file);
        }
    };

    return (
        <div className="space-y-2">
            <div className="space-y-1">
                <h4 className="label-technical px-1">Temas</h4>
                <div className="grid grid-cols-6 gap-1.5 px-0.5">
                    {themes.map((t) => (
                        <div key={t.id} className="relative group">
                            <button
                                onClick={() => setTheme(t.id)}
                                className={`w-5 h-5 rounded-full transition-all duration-300 transform hover:scale-110 active:scale-95 ${t.color} ${theme === t.id
                                    ? 'ring-1 ring-violet-500 ring-offset-1 ring-offset-transparent scale-110 shadow-lg'
                                    : 'opacity-70 hover:opacity-100 border border-white/5 hover:border-white/10'
                                    } flex items-center justify-center relative`}
                            >
                                {theme === t.id && <Check size={8} className="text-white drop-shadow-md" />}
                            </button>

                            {/* Simple CSS Tooltip */}
                            <div className={`absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 rounded-md text-[9px] font-black uppercase tracking-widest pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-50 shadow-xl border ${isLight ? 'bg-slate-800 text-white border-slate-700' : 'bg-white text-slate-900 border-white'
                                }`}>
                                {t.name}
                                <div className={`absolute top-full left-1/2 -translate-x-1/2 border-x-[4px] border-x-transparent border-t-[4px] ${isLight ? 'border-t-slate-800' : 'border-t-white'
                                    }`} />
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            <Divider className={isLight ? 'bg-slate-100' : 'bg-white/5'} />

            <div className="space-y-2">
                <h4 className="label-technical">Fondo Personalizado</h4>
                <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleFileChange}
                    accept="image/*"
                    className="hidden"
                />
                <div className="flex flex-col gap-2">
                    <Button
                        size="sm"
                        variant="flat"
                        startContent={<Upload size={14} />}
                        onClick={() => fileInputRef.current?.click()}
                        className={`w-full justify-start font-black h-9 rounded-xl transition-all ${isLight ? 'bg-slate-100 text-slate-700 hover:bg-slate-200' : 'bg-white/10 text-white hover:bg-white/20'
                            } text-glow-contrast`}
                    >
                        Subir imagen
                    </Button>

                    {customBg && (
                        <div className="space-y-1.5">
                            <button
                                onClick={() => setTheme('custom')}
                                className={`flex items-center justify-between w-full px-3 py-1.5 rounded-xl transition-all duration-300 group ${theme === 'custom'
                                    ? (isLight ? 'bg-slate-100 text-slate-900 border-slate-200' : 'bg-white/10 text-white border-white/10 shadow-lg')
                                    : (isLight ? 'text-slate-500 hover:bg-slate-50 border-transparent' : 'text-slate-400 hover:bg-white/5 border-transparent')
                                    } border`}
                            >
                                <div className="flex items-center gap-3">
                                    <div className={`w-4 h-4 rounded-md bg-cover bg-center border border-white/20`} style={{ backgroundImage: `url(${customBg})` }} />
                                    <span className="text-[10px] font-bold">Imagen activa</span>
                                </div>
                                {theme === 'custom' && <Check size={12} className="text-violet-500" />}
                            </button>
                            <button
                                onClick={() => {
                                    if (theme === 'custom') setTheme('cyberpunk');
                                    setCustomBg(null);
                                }}
                                className={`flex items-center gap-2 px-3 py-1 rounded-xl text-[9px] font-black uppercase tracking-[0.1em] transition-colors ${isLight ? 'text-rose-600 hover:bg-rose-50' : 'text-rose-400 hover:bg-rose-500/10'
                                    } text-glow-contrast`}
                            >
                                <X size={12} />
                                Quitar Imagen
                            </button>
                        </div>
                    )}
                </div>
            </div>

            <Divider className={isLight ? 'bg-slate-100' : 'bg-white/5'} />

            <div className="space-y-2">
                <div className="flex items-center justify-between">
                    <h4 className="label-technical">Transparencia</h4>
                    <span className={`text-[9px] font-black tracking-widest ${isLight ? 'text-slate-900' : 'text-white'} text-glow-contrast`}>{glassOpacity}%</span>
                </div>
                <Slider
                    size="sm"
                    step={1}
                    maxValue={100}
                    minValue={0}
                    value={glassOpacity}
                    onChange={(val) => setGlassOpacity(val as number)}
                    className="max-w-md"
                    color="secondary"
                    hideValue
                    classNames={{
                        track: isLight ? "bg-slate-200" : "bg-white/10",
                        filler: "bg-gradient-to-r from-violet-500 to-indigo-500"
                    }}
                />
            </div>
        </div>
    );
}

export function BackgroundPicker() {
    const { themeType } = useBackground();
    const isLight = themeType === 'light';

    return (
        <Popover placement="bottom-end">
            <PopoverTrigger>
                <Button
                    isIconOnly
                    variant="light"
                    className={`transition-all border backdrop-blur-md rounded-xl ${isLight
                        ? 'text-slate-700 hover:text-slate-900 bg-black/5 hover:bg-black/10 border-black/5'
                        : 'text-slate-200 hover:text-white bg-white/10 hover:bg-white/20 border-white/10'
                        }`}
                    title="Configurar fondo"
                >
                    <Palette size={20} />
                </Button>
            </PopoverTrigger>
            <PopoverContent className="p-5 backdrop-blur-2xl border rounded-2xl shadow-2xl glass border-white/10 w-64">
                <ThemeSettings />
            </PopoverContent>
        </Popover>
    );
}
