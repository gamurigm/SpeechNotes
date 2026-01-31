'use client'

import React, { createContext, useContext, useState, useEffect } from 'react';
import { HeroUIProvider } from "@heroui/react";
import { useRouter } from 'next/navigation';

export type BackgroundTheme = 'cyberpunk' | 'midnight' | 'emerald' | 'abyss' | 'pure-light' | 'custom';

interface BackgroundContextType {
  theme: BackgroundTheme;
  setTheme: (theme: BackgroundTheme) => void;
  customBg: string | null;
  setCustomBg: (url: string | null) => void;
  glassOpacity: number;
  setGlassOpacity: (opacity: number) => void;
  themeType: 'light' | 'dark';
}

const BackgroundContext = createContext<BackgroundContextType | undefined>(undefined);

export function useBackground() {
  const context = useContext(BackgroundContext);
  if (!context) throw new Error('useBackground must be used within a BackgroundProvider');
  return context;
}

const themeColors: Record<BackgroundTheme, Record<string, string>> = {
  cyberpunk: {
    '--bg-color-1': '#020617',
    '--bg-color-2': '#0f172a',
    '--bg-color-3': '#1e1b4b',
    '--bg-gradient-spot-1': '#4f46e5',
    '--bg-gradient-spot-2': '#8b5cf6',
    '--bg-gradient-spot-3': '#0ea5e9',
    '--foreground': '#ededed',
    '--background': '#020617',
    '--theme-type': 'dark',
    '--theme-neon-color': '#0ea5e9'
  },
  midnight: {
    '--bg-color-1': '#08080a',
    '--bg-color-2': '#11111a',
    '--bg-color-3': '#1a1033',
    '--bg-gradient-spot-1': '#6d28d9',
    '--bg-gradient-spot-2': '#4338ca',
    '--bg-gradient-spot-3': '#312e81',
    '--foreground': '#ededed',
    '--background': '#08080a',
    '--theme-type': 'dark',
    '--theme-neon-color': '#a855f7'
  },
  emerald: {
    '--bg-color-1': '#022c22',
    '--bg-color-2': '#064e3b',
    '--bg-color-3': '#065f46',
    '--bg-gradient-spot-1': '#10b981',
    '--bg-gradient-spot-2': '#059669',
    '--bg-gradient-spot-3': '#34d399',
    '--foreground': '#ededed',
    '--background': '#022c22',
    '--theme-type': 'dark',
    '--theme-neon-color': '#10b981'
  },
  abyss: {
    '--bg-color-1': '#000000',
    '--bg-color-2': '#0a0a0a',
    '--bg-color-3': '#111111',
    '--bg-gradient-spot-1': '#312e81',
    '--bg-gradient-spot-2': '#1e1b4b',
    '--bg-gradient-spot-3': '#0f172a',
    '--foreground': '#ededed',
    '--background': '#000000',
    '--theme-type': 'dark',
    '--theme-neon-color': '#3b82f6'
  },
  'pure-light': {
    '--bg-color-1': '#f8fafc',
    '--bg-color-2': '#f1f5f9',
    '--bg-color-3': '#e2e8f0',
    '--bg-gradient-spot-1': '#8b5cf6',
    '--bg-gradient-spot-2': '#a78bfa',
    '--bg-gradient-spot-3': '#c4b5fd',
    '--foreground': '#1e293b',
    '--background': '#ffffff',
    '--theme-type': 'light',
    '--theme-neon-color': '#6366f1'
  },
  'custom': {
    '--foreground': '#ededed',
    '--background': '#08080a',
    '--theme-type': 'dark',
    '--theme-neon-color': '#8b5cf6'
  }
};

export function Providers({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [theme, setThemeState] = useState<BackgroundTheme>('cyberpunk');
  const [customBg, setCustomBgState] = useState<string | null>(null);
  const [glassOpacity, setGlassOpacityState] = useState<number>(10);
  const [themeType, setThemeType] = useState<'light' | 'dark'>('dark');

  // Load theme and custom image from localStorage on mount
  useEffect(() => {
    const savedTheme = localStorage.getItem('sn-bg-theme') as BackgroundTheme;
    const savedCustomBg = localStorage.getItem('sn-custom-bg');
    const savedOpacity = localStorage.getItem('sn-glass-opacity');

    if (savedTheme && (themeColors[savedTheme] || savedTheme === 'custom')) {
      setThemeState(savedTheme);
      setThemeType(themeColors[savedTheme]['--theme-type'] as 'light' | 'dark');
    }
    if (savedCustomBg) {
      setCustomBgState(savedCustomBg);
    }
    if (savedOpacity) {
      setGlassOpacityState(parseInt(savedOpacity));
    }
  }, []);

  // Apply theme variables to root
  useEffect(() => {
    const root = document.documentElement;
    const currentThemeProps = themeColors[theme];
    const type = currentThemeProps['--theme-type'] as 'light' | 'dark';
    setThemeType(type);

    // Apply all variables defined in themeColors
    Object.entries(currentThemeProps).forEach(([property, value]) => {
      root.style.setProperty(property, value);
    });

    // Set data-theme for third-party components (like HeroUI)
    root.setAttribute('data-theme', type);

    // Dynamic Glassmorphism Logic - Theme-Aware Tinting
    // Using color-mix to blend the theme's specific background color with transparency
    const presenceMultiplier = type === 'light' ? 1 : 0.7;
    root.style.setProperty('--theme-glass-bg', `color-mix(in srgb, var(--background) ${glassOpacity * presenceMultiplier}%, transparent)`);
    root.style.setProperty('--theme-glass-border', type === 'light' ? 'rgba(0, 0, 0, 0.05)' : 'rgba(255, 255, 255, 0.12)');

    localStorage.setItem('sn-bg-theme', theme);
  }, [theme, glassOpacity]);

  // Apply glass opacity to root
  useEffect(() => {
    document.documentElement.style.setProperty('--glass-opacity', (glassOpacity / 100).toString());
    localStorage.setItem('sn-glass-opacity', glassOpacity.toString());
  }, [glassOpacity]);

  const setTheme = (newTheme: BackgroundTheme) => {
    setThemeState(newTheme);
  };

  const setCustomBg = (url: string | null) => {
    setCustomBgState(url);
    if (url) {
      try {
        // Safe check for quota - ~2MB is usually safe for the custom bg 
        // given other data in localStorage.
        if (url.length > 2 * 1024 * 1024) {
          console.warn("La imagen es demasiado grande para guardarse permanentemente.");
        }
        localStorage.setItem('sn-custom-bg', url);
        setThemeState('custom');
      } catch (e) {
        console.error("Error saving custom background to localStorage:", e);
        // If it fails, we still set it in state so it works for the session,
        // but it won't persist.
      }
    } else {
      localStorage.removeItem('sn-custom-bg');
    }
  };

  const setGlassOpacity = (opacity: number) => {
    setGlassOpacityState(opacity);
  };

  return (
    <BackgroundContext.Provider value={{ theme, setTheme, customBg, setCustomBg, glassOpacity, setGlassOpacity, themeType }}>
      <HeroUIProvider navigate={router.push}>
        {children}
      </HeroUIProvider>
    </BackgroundContext.Provider>
  )
}
