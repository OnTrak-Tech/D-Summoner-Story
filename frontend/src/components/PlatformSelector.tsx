import React from 'react';
import { Platform } from '../config/platforms';

interface PlatformSelectorProps {
  platforms: Platform[];
  selectedPlatform: Platform | null;
  onPlatformSelect: (platform: Platform) => void;
  disabled?: boolean;
}

export const PlatformSelector: React.FC<PlatformSelectorProps> = ({
  platforms,
  selectedPlatform,
  onPlatformSelect,
  disabled = false
}) => {
  return (
    <div className="w-full max-w-5xl mx-auto">
      <div className="text-center mb-12">
        <h2 className="text-4xl font-black text-white mb-4 tracking-tight">
          Choose Your <span className="bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent">Platform</span>
        </h2>
        <p className="text-xl text-gray-400 max-w-2xl mx-auto">
          Select your gaming platform to unlock advanced analytics and AI-powered insights
        </p>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {platforms.map((platform) => {
          const isSelected = selectedPlatform?.id === platform.id;
          return (
            <button
              key={platform.id}
              onClick={() => onPlatformSelect(platform)}
              disabled={disabled}
              className={`
                group relative overflow-hidden rounded-2xl p-8 transition-all duration-500 transform
                ${isSelected
                  ? 'bg-gradient-to-br from-cyan-500/20 to-purple-500/20 border-2 border-cyan-400 scale-105 shadow-2xl shadow-cyan-500/25'
                  : 'bg-gray-900/60 backdrop-blur-xl border-2 border-gray-800 hover:border-gray-600 hover:scale-105 hover:shadow-xl'
                }
                ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
              `}
            >
              {/* Glow effect */}
              <div className={`
                absolute inset-0 bg-gradient-to-br opacity-0 group-hover:opacity-20 transition-opacity duration-500
                ${platform.id === 'riot' ? 'from-blue-500 to-purple-500' : ''}
                ${platform.id === 'steam' ? 'from-gray-500 to-slate-500' : ''}
                ${platform.id === 'xbox' ? 'from-green-500 to-emerald-500' : ''}
                ${platform.id === 'psn' ? 'from-blue-500 to-purple-500' : ''}
              `} />
              
              <div className="relative z-10 text-center">
                <div className="text-6xl mb-6 group-hover:scale-110 transition-transform duration-300">
                  {platform.icon}
                </div>
                <h3 className="font-bold text-2xl text-white mb-2">
                  {platform.displayName}
                </h3>
                <p className="text-gray-400 text-sm">
                  {platform.name}
                </p>
              </div>
              
              {/* Selection indicator */}
              {isSelected && (
                <div className="absolute top-4 right-4">
                  <div className="w-8 h-8 bg-cyan-400 rounded-full flex items-center justify-center">
                    <svg className="w-5 h-5 text-black" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  </div>
                </div>
              )}
            </button>
          );
        })}
      </div>
      
      {/* Coming Soon Platforms */}
      {platforms.length < 4 && (
        <div className="mt-16 text-center">
          <h3 className="text-2xl font-bold text-white mb-8">Coming Soon</h3>
          <div className="flex justify-center gap-6">
            <div className="bg-gray-900/40 backdrop-blur-sm rounded-xl p-6 border border-gray-800">
              <div className="text-4xl mb-3 opacity-50">🎮</div>
              <p className="text-sm text-gray-500 font-medium">Steam</p>
            </div>
            <div className="bg-gray-900/40 backdrop-blur-sm rounded-xl p-6 border border-gray-800">
              <div className="text-4xl mb-3 opacity-50">🎯</div>
              <p className="text-sm text-gray-500 font-medium">Xbox</p>
            </div>
            <div className="bg-gray-900/40 backdrop-blur-sm rounded-xl p-6 border border-gray-800">
              <div className="text-4xl mb-3 opacity-50">🎪</div>
              <p className="text-sm text-gray-500 font-medium">PlayStation</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};