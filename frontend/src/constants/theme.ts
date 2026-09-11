/**
 * Below are the colors that are used in the app. The colors are defined in the light and dark mode.
 * There are many other ways to style your app. For example, [Nativewind](https://www.nativewind.dev/), [Tamagui](https://tamagui.dev/), [unistyles](https://reactnativeunistyles.vercel.app), etc.
 */

import '@/global.css';

import { Platform } from 'react-native';

export const Colors = {
  light: {
    text: '#211B3A',
    background: '#F7F1E5',
    backgroundElement: '#FFFFFF',
    backgroundSelected: '#FFF0B8',
    textSecondary: '#756D83',
    textPrimary: '#211B3A',
    surface: '#FFFFFF',
    surfaceElevated: '#FFFFFF',
    accent: '#F4D36A',
    accentText: '#211B3A',
    border: '#DED7E5',
    inputBackground: '#FFFFFF',
    tabInactive: '#8F879B',
  },
  dark: {
    text: '#FFF9E8',
    background: '#17152C',
    backgroundElement: '#25213D',
    backgroundSelected: '#302B4C',
    textSecondary: '#B9B4C8',
    textPrimary: '#FFF9E8',
    surface: '#25213D',
    surfaceElevated: '#302B4C',
    accent: '#F7D77A',
    accentText: '#17152C',
    border: '#403A5A',
    inputBackground: '#25213D',
    tabInactive: '#9B94AA',
  },
} as const;

export type ThemeColor = keyof typeof Colors.light & keyof typeof Colors.dark;

export const Fonts = Platform.select({
  ios: {
    /** iOS `UIFontDescriptorSystemDesignDefault` */
    sans: 'system-ui',
    /** iOS `UIFontDescriptorSystemDesignSerif` */
    serif: 'ui-serif',
    /** iOS `UIFontDescriptorSystemDesignRounded` */
    rounded: 'ui-rounded',
    /** iOS `UIFontDescriptorSystemDesignMonospaced` */
    mono: 'ui-monospace',
  },
  default: {
    sans: 'normal',
    serif: 'serif',
    rounded: 'normal',
    mono: 'monospace',
  },
  web: {
    sans: 'var(--font-display)',
    serif: 'var(--font-serif)',
    rounded: 'var(--font-rounded)',
    mono: 'var(--font-mono)',
  },
});

export const Spacing = {
  half: 2,
  one: 4,
  two: 8,
  three: 16,
  four: 24,
  five: 32,
  six: 64,
} as const;

export const BottomTabInset = Platform.select({ ios: 60, android: 80, default: 80 }) ?? 80;
export const MaxContentWidth = 800;
