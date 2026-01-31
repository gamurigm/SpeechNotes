'use client';

import React from 'react';
import { useBackground } from '../../providers';

export function BackgroundSystem() {
    const { theme, customBg, themeType } = useBackground();
    const isLight = themeType === 'light';

    return (
        <div className={`mesh-gradient-container select-none theme-${theme}`}>
            {/* Custom Background Image - Rendered "Tal Cual" */}
            {customBg && (
                <div
                    className="absolute inset-0 z-[-1] bg-cover bg-center bg-no-repeat transition-opacity duration-1000"
                    style={{ backgroundImage: `url(${customBg})` }}
                />
            )}

            {/* Mesh Balls - Hide them when customBg is present to avoid blur clusters */}
            {!customBg && (
                <>
                    <div className={`mesh-ball mesh-ball-1 ${isLight ? 'opacity-[0.15]' : 'opacity-40'}`} />
                    <div className={`mesh-ball mesh-ball-2 ${isLight ? 'opacity-[0.15]' : 'opacity-40'}`} />
                    <div className={`mesh-ball mesh-ball-3 ${isLight ? 'opacity-[0.15]' : 'opacity-40'}`} />
                </>
            )}

            {/* Tech overlays - Subtler when customBg is active */}
            <div className={`bg-grid-overlay transition-opacity duration-500 ${customBg ? 'opacity-[0.05]' : 'opacity-[0.3]'}`} />
            <div className={`bg-noise-overlay transition-opacity duration-500 ${customBg ? 'opacity-[0.01]' : 'opacity-[0.02]'}`} />

            {/* Premium overlays for readability and depth */}
            <div className={`absolute inset-0 pointer-events-none transition-opacity duration-1000 ${isLight ? 'bg-white/30' : 'bg-black/10'}`} />

            {/* Subtle Vignette - Preserving image quality but helping UI contrast */}
            <div className="absolute inset-0 pointer-events-none"
                style={{
                    background: isLight
                        ? 'radial-gradient(circle at center, transparent 0%, rgba(255,255,255,0.1) 100%)'
                        : 'radial-gradient(circle at center, transparent 0%, rgba(0,0,0,0.4) 100%)'
                }} />
        </div>
    );
}
