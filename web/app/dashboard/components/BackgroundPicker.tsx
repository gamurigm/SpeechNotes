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

export function BackgroundPicker() {
    const { theme, setTheme, customBg, setCustomBg, glassOpacity, setGlassOpacity, themeType } = useBackground();
    const fileInputRef = useRef<HTMLInputElement>(null);
    const isLight = themeType === 'light';

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            const reader = new FileReader();
            reader.onloadend = () => {
                setCustomBg(reader.result as string);
            };
            reader.readAsDataURL(file);
        }
    };

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
            <PopoverContent className="p-3 backdrop-blur-2xl border rounded-2xl shadow-2xl glass border-white/10">
                <div className="space-y-3 w-56">
                    <div className="px-2 pt-1">
                        <h4 className="label-technical">Visual Theme</h4>
                    </div>

                    <div className="grid grid-cols-1 gap-1">
                        {themes.map((t) => (
                            <button
                                key={t.id}
                                onClick={() => setTheme(t.id)}
                                className={`flex items-center justify-between w-full px-3 py-2.5 rounded-xl transition-all duration-300 group ${theme === t.id
                                    ? (isLight ? 'bg-slate-100/80 text-slate-900 border-slate-200 shadow-sm' : 'bg-white/10 text-white border-white/20 shadow-lg backdrop-blur-md')
                                    : (isLight ? 'text-slate-600 hover:bg-slate-50 border-transparent' : 'text-slate-200 hover:bg-white/5 border-transparent')
                                    } border text-glow-contrast`}
                            >
                                <div className="flex items-center gap-3">
                                    <div className={`w-2 h-2 rounded-full ${t.color} ${theme === t.id ? 'ring-4 ring-current/10 animate-pulse' : ''}`} />
                                    <span className="text-xs font-bold">{t.name}</span>
                                </div>
                                {theme === t.id && <Check size={14} className="text-violet-500" />}
                            </button>
                        ))}
                    </div>

                    <Divider className={isLight ? 'bg-slate-100' : 'bg-white/5'} />

                    <div className="px-2 pb-1">
                        <h4 className="label-technical mb-2">Custom fondo</h4>

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
                                className={`w-full justify-start font-black h-10 rounded-xl transition-all ${isLight ? 'bg-slate-100 text-slate-700 hover:bg-slate-200' : 'bg-white/10 text-white hover:bg-white/20'
                                    } text-glow-contrast`}
                            >
                                Subir imagen
                            </Button>

                            {customBg && (
                                <button
                                    onClick={() => {
                                        if (theme === 'custom') setTheme('cyberpunk');
                                        setCustomBg(null);
                                    }}
                                    className={`flex items-center gap-2 px-3 py-2 rounded-xl text-[10px] font-black uppercase tracking-[0.1em] transition-colors ${isLight ? 'text-rose-600 hover:bg-rose-50' : 'text-rose-400 hover:bg-rose-500/10'
                                        } text-glow-contrast`}
                                >
                                    <X size={14} />
                                    Quitar Imagen
                                </button>
                            )}
                        </div>
                    </div>

                    {customBg && (
                        <button
                            onClick={() => setTheme('custom')}
                            className={`flex items-center justify-between w-full px-3 py-2 rounded-xl transition-all duration-300 group ${theme === 'custom'
                                ? (isLight ? 'bg-slate-100 text-slate-900 border-slate-200' : 'bg-white/10 text-white border-white/10 shadow-lg')
                                : (isLight ? 'text-slate-500 hover:bg-slate-50 border-transparent' : 'text-slate-400 hover:bg-white/5 border-transparent')
                                } border mb-2`}
                        >
                            <div className="flex items-center gap-3">
                                <div className={`w-4 h-4 rounded-md bg-cover bg-center border border-white/20`} style={{ backgroundImage: `url(${customBg})` }} />
                                <span className="text-xs font-bold">Imagen activa</span>
                            </div>
                            {theme === 'custom' && <Check size={14} className="text-violet-500" />}
                        </button>
                    )}

                    <Divider className={isLight ? 'bg-slate-100' : 'bg-white/5'} />

                    <div className="px-2 pt-1">
                        <div className="flex items-center justify-between mb-3">
                            <h4 className="label-technical">Transparencia</h4>
                            <span className={`text-[10px] font-black tracking-widest ${isLight ? 'text-slate-900' : 'text-white'} text-glow-contrast`}>{glassOpacity}%</span>
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
            </PopoverContent>
        </Popover>
    );
}
