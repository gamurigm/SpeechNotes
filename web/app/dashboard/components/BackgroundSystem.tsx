'use client';

import React from 'react';
import { useBackground } from '../../providers';

export function BackgroundSystem() {
    const { theme, customBg } = useBackground();

    return (
        <div className={`mesh-gradient-container select-none theme-${theme}`}>
            {/* Custom Background Image */}
            {customBg && (
                <div
                    className="absolute inset-0 z-[-2] bg-cover bg-center bg-no-repeat transition-opacity duration-1000"
                    style={{ backgroundImage: `url(${customBg})` }}
                />
            )}

            {/* Mesh Balls for the glow effect */}
            <div className={`mesh-ball mesh-ball-1 ${theme === 'pure-light' ? 'opacity-[0.15]' : 'opacity-40'}`} />
            <div className={`mesh-ball mesh-ball-2 ${theme === 'pure-light' ? 'opacity-[0.15]' : 'opacity-40'}`} />
            <div className={`mesh-ball mesh-ball-3 ${theme === 'pure-light' ? 'opacity-[0.15]' : 'opacity-40'}`} />

            {/* Tech overlays */}
            <div className="bg-grid-overlay opacity-[0.3]" />
            <div className="bg-noise-overlay" />

            {/* Light Theme specific overlay for readability */}
            {theme === 'pure-light' && (
                <div className="absolute inset-0 bg-white/40 pointer-events-none" />
            )}

            {/* Custom Theme specific overlay for readability */}
            {theme === 'custom' && (
                <div className="absolute inset-0 bg-black/40 pointer-events-none" />
            )}

            {/* Optional: Subtle vignette */}
            <div className="absolute inset-0 pointer-events-none"
                style={{
                    background: theme === 'pure-light'
                        ? 'radial-gradient(circle at center, transparent 0%, rgba(255,255,255,0.2) 100%)'
                        : 'radial-gradient(circle at center, transparent 0%, rgba(0,0,0,0.4) 100%)'
                }} />
        </div>
    );
}
