'use client';

import { useState, useEffect } from 'react';
import { CheckCircle2, XCircle, Info, AlertCircle, X } from 'lucide-react';
import { useBackground } from '../../providers';

export type ToastType = 'success' | 'error' | 'info' | 'warning';

interface ToastProps {
    message: string;
    type: ToastType;
    onClose: () => void;
    duration?: number;
}

export function Toast({ message, type, onClose, duration = 3000 }: ToastProps) {
    const { themeType } = useBackground();
    const isLight = themeType === 'light';
    const [isVisible, setIsVisible] = useState(false);

    useEffect(() => {
        setIsVisible(true);
        const timer = setTimeout(() => {
            setIsVisible(false);
            setTimeout(onClose, 300); // Wait for fade-out animation
        }, duration);

        return () => clearTimeout(timer);
    }, [duration, onClose]);

    const icons = {
        success: <CheckCircle2 className="text-emerald-500" size={20} />,
        error: <XCircle className="text-rose-500" size={20} />,
        info: <Info className="text-blue-500" size={20} />,
        warning: <AlertCircle className="text-amber-500" size={20} />
    };

    const gradientColors = {
        success: 'from-emerald-500/10 to-emerald-500/5',
        error: 'from-rose-500/10 to-rose-500/5',
        info: 'from-blue-500/10 to-blue-500/5',
        warning: 'from-amber-500/10 to-amber-500/5'
    };

    return (
        <div
            className={`fixed bottom-8 left-1/2 -translate-x-1/2 z-[1000] transition-all duration-500 ease-[cubic-bezier(0.23,1,0.32,1)] ${isVisible ? 'translate-y-0 opacity-100 scale-100' : 'translate-y-10 opacity-0 scale-90'
                }`}
        >
            <div className={`
                glass-module min-w-[320px] max-w-md p-4 rounded-2xl flex items-center gap-4
                bg-gradient-to-br ${gradientColors[type]}
                border-white/20 shadow-2xl backdrop-blur-3xl
            `}>
                <div className={`w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center shadow-inner`}>
                    {icons[type]}
                </div>

                <div className="flex-1">
                    <p className={`text-[13px] font-bold leading-tight ${isLight ? 'text-slate-900' : 'text-white'}`}>
                        {message}
                    </p>
                </div>

                <button
                    onClick={() => {
                        setIsVisible(false);
                        setTimeout(onClose, 300);
                    }}
                    className={`p-1.5 rounded-lg hover:bg-white/10 transition-colors ${isLight ? 'text-slate-400' : 'text-slate-500'}`}
                >
                    <X size={16} />
                </button>
            </div>
        </div>
    );
}
