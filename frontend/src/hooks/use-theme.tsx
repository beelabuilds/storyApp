import React, { createContext, useContext, useEffect, useState } from 'react';
import { Platform } from 'react-native';

import { Colors } from '@/constants/theme';
import { useColorScheme } from '@/hooks/use-color-scheme';

type ThemeMode = 'light' | 'dark';

type ThemeContextValue = {
  mode: ThemeMode;
  setMode: (mode: ThemeMode) => void;
  toggleMode: () => void;
};

const ThemeContext = createContext<ThemeContextValue | null>(null);

export function AppThemeProvider({ children }: { children: React.ReactNode }) {
  const systemScheme = useColorScheme();
  const [mode, setMode] = useState<ThemeMode>(() => {
    if (Platform.OS === 'web') {
      const stored = localStorage.getItem('@storyapp_theme');
      if (stored === 'light' || stored === 'dark') return stored;
    }
    return systemScheme === 'dark' ? 'dark' : 'light';
  });

  useEffect(() => {
    if (Platform.OS === 'web') localStorage.setItem('@storyapp_theme', mode);
  }, [mode]);

  const toggleMode = () => setMode((current) => current === 'dark' ? 'light' : 'dark');

  return (
    <ThemeContext.Provider value={{ mode, setMode, toggleMode }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useThemeMode() {
  const context = useContext(ThemeContext);
  if (!context) throw new Error('useThemeMode must be used inside AppThemeProvider');
  return context;
}

export function useTheme() {
  const { mode } = useThemeMode();
  return Colors[mode];
}
