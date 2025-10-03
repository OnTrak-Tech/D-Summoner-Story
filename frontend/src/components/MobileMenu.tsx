/**
 * MobileMenu component for responsive navigation and settings.
 * Provides access to theme toggle, recent searches, and app info on mobile devices.
 */

import React, { useState } from 'react';
import { ThemeToggle } from './ThemeToggle';
import { useRecentSearches } from '../hooks/useLocalStorage';

interface MobileMenuProps {
  onRecentSearchSelect?: (summonerName: string, region: string) => void;
}

export const MobileMenu: React.FC<MobileMenuProps> = ({ onRecentSearchSelect }) => {
  const [isOpen, setIsOpen] = useState(false);
  const { storedValue: recentSearches } = useRecentSearches();

  const handleRecentSearchClick = (search: typeof recentSearches[0]) => {
    if (onRecentSearchSelect) {
      onRecentSearchSelect(search.summonerName, search.region);
    }
    setIsOpen(false);
  };

  return (
    <>
      {/* Mobile Menu Button */}
      <button
        onClick={() => setIsOpen(true)}
        className="md:hidden fixed top-4 right-4 z-40 p-2 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700"
        aria-label="Open menu"
      >
        <svg className="w-6 h-6 text-gray-600 dark:text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>

      {/* Mobile Menu Overlay */}
      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-black bg-opacity-50 z-50 md:hidden"
            onClick={() => setIsOpen(false)}
          />

          {/* Menu Panel */}
          <div className="fixed inset-y-0 right-0 w-80 max-w-full bg-white dark:bg-gray-900 shadow-xl z-50 md:hidden overflow-y-auto">
            <div className="p-6">
              {/* Header */}
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                  Menu
                </h2>
                <button
                  onClick={() => setIsOpen(false)}
                  className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              {/* Theme Toggle */}
              <div className="mb-6">
                <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                  Appearance
                </h3>
                <ThemeToggle />
              </div>

              {/* Recent Searches */}
              {recentSearches.length > 0 && (
                <div className="mb-6">
                  <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                    Recent Searches
                  </h3>
                  <div className="space-y-2">
                    {recentSearches.map((search, index) => (
                      <button
                        key={index}
                        onClick={() => handleRecentSearchClick(search)}
                        className="w-full p-3 text-left bg-gray-50 dark:bg-gray-800 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-medium text-gray-900 dark:text-white">
                            {search.summonerName}
                          </span>
                          <span className="text-xs text-gray-500 dark:text-gray-400">
                            {search.region.toUpperCase()}
                          </span>
                        </div>
                        <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                          {new Date(search.timestamp).toLocaleDateString()}
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* App Info */}
              <div className="mb-6">
                <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                  About
                </h3>
                <div className="space-y-3 text-sm text-gray-600 dark:text-gray-400">
                  <div className="flex items-center gap-2">
                    <span>🎮</span>
                    <span>League of Legends Year in Review</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span>🤖</span>
                    <span>AI-Powered Insights</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span>📊</span>
                    <span>Performance Analytics</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span>🔒</span>
                    <span>Secure & Private</span>
                  </div>
                </div>
              </div>

              {/* Quick Actions */}
              <div className="space-y-3">
                <button
                  onClick={() => {
                    window.open('https://developer.riotgames.com/', '_blank');
                    setIsOpen(false);
                  }}
                  className="w-full p-3 text-left bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 rounded-lg hover:bg-blue-100 dark:hover:bg-blue-900/30 transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <span>🔗</span>
                    <span className="font-medium">Riot Games API</span>
                  </div>
                  <div className="text-xs mt-1">
                    Learn more about the data source
                  </div>
                </button>

                <button
                  onClick={() => {
                    if (navigator.share) {
                      navigator.share({
                        title: 'D-Summoner-Story',
                        text: 'Check out this League of Legends Year in Review app!',
                        url: window.location.href,
                      });
                    }
                    setIsOpen(false);
                  }}
                  className="w-full p-3 text-left bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300 rounded-lg hover:bg-green-100 dark:hover:bg-green-900/30 transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <span>📤</span>
                    <span className="font-medium">Share App</span>
                  </div>
                  <div className="text-xs mt-1">
                    Tell your friends about this tool
                  </div>
                </button>
              </div>

              {/* Footer */}
              <div className="mt-8 pt-6 border-t border-gray-200 dark:border-gray-700">
                <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
                  Built with ❤️ for the League community
                </p>
              </div>
            </div>
          </div>
        </>
      )}
    </>
  );
};