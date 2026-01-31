/**
 * ThemeToggle component for switching between light, dark, and system themes.
 * Provides a clean UI for theme selection with icons and labels.
 */

import React, { useState } from 'react';
import { useTheme } from '../contexts/ThemeContext';

export const ThemeToggle: React.FC = () => {
  const { theme, setTheme, isDark } = useTheme();
  const [isOpen, setIsOpen] = useState(false);

  const themes = [
    { value: 'light', label: 'Light', icon: '☀️' },
    { value: 'dark', label: 'Dark', icon: '🌙' },
    { value: 'system', label: 'System', icon: '💻' },
  ] as const;

  const currentTheme = themes.find((t) => t.value === theme) || themes[0];

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`
          flex items-center gap-2 px-3 py-2 rounded-lg transition-colors
          ${
            isDark
              ? 'bg-gray-800 text-gray-200 hover:bg-gray-700'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }
        `}
        aria-label="Toggle theme"
      >
        <span className="text-lg">{currentTheme.icon}</span>
        <span className="hidden sm:inline text-sm font-medium">{currentTheme.label}</span>
        <svg
          className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <>
          {/* Backdrop */}
          <div className="fixed inset-0 z-10" onClick={() => setIsOpen(false)} />

          {/* Dropdown */}
          <div
            className={`
            absolute right-0 mt-2 w-48 rounded-lg shadow-lg z-20 border
            ${isDark ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}
          `}
          >
            <div className="py-1">
              {themes.map((themeOption) => (
                <button
                  key={themeOption.value}
                  onClick={() => {
                    setTheme(themeOption.value);
                    setIsOpen(false);
                  }}
                  className={`
                    w-full px-4 py-2 text-left flex items-center gap-3 transition-colors
                    ${
                      theme === themeOption.value
                        ? isDark
                          ? 'bg-blue-600 text-white'
                          : 'bg-blue-50 text-blue-700'
                        : isDark
                          ? 'text-gray-200 hover:bg-gray-700'
                          : 'text-gray-700 hover:bg-gray-50'
                    }
                  `}
                >
                  <span className="text-lg">{themeOption.icon}</span>
                  <div className="flex-1">
                    <div className="font-medium">{themeOption.label}</div>
                    <div
                      className={`text-xs ${
                        theme === themeOption.value
                          ? isDark
                            ? 'text-blue-200'
                            : 'text-blue-600'
                          : isDark
                            ? 'text-gray-400'
                            : 'text-gray-500'
                      }`}
                    >
                      {themeOption.value === 'light' && 'Always use light theme'}
                      {themeOption.value === 'dark' && 'Always use dark theme'}
                      {themeOption.value === 'system' && 'Follow system preference'}
                    </div>
                  </div>
                  {theme === themeOption.value && (
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                      <path
                        fillRule="evenodd"
                        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                        clipRule="evenodd"
                      />
                    </svg>
                  )}
                </button>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
};
