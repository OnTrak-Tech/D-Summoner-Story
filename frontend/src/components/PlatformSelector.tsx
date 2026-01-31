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
  disabled = false,
}) => {
  return (
    <div className="w-full max-w-4xl mx-auto mb-8">
      <div className="text-center mb-6">
        <h2 className="text-2xl font-semibold text-white mb-2 drop-shadow-lg">
          Choose Your Gaming Platform
        </h2>
        <p className="text-gray-200 drop-shadow-md">
          Select a platform to analyze your gaming performance
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {platforms.map((platform) => (
          <button
            key={platform.id}
            onClick={() => onPlatformSelect(platform)}
            disabled={disabled}
            className={`
              group relative overflow-hidden rounded-2xl p-6 transition-all duration-300
              ${
                selectedPlatform?.id === platform.id
                  ? `bg-gradient-to-br ${platform.color.primary} text-white shadow-2xl scale-105`
                  : 'bg-white/90 backdrop-blur-sm text-gray-800 hover:bg-white hover:scale-105 shadow-lg hover:shadow-xl'
              }
              ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
              border border-white/20
            `}
          >
            {/* Background gradient overlay */}
            <div
              className={`
              absolute inset-0 bg-gradient-to-br ${platform.color.primary} opacity-0 
              group-hover:opacity-10 transition-opacity duration-300
            `}
            />

            <div className="relative z-10 text-center">
              <div className="text-4xl mb-3 group-hover:scale-110 transition-transform duration-300">
                {platform.icon}
              </div>
              <h3 className="font-semibold text-lg mb-1">{platform.displayName}</h3>
              <p
                className={`text-sm ${
                  selectedPlatform?.id === platform.id ? 'text-white/80' : 'text-gray-600'
                }`}
              >
                {platform.name}
              </p>
            </div>

            {/* Selection indicator */}
            {selectedPlatform?.id === platform.id && (
              <div className="absolute top-2 right-2">
                <div className="w-6 h-6 bg-white/20 rounded-full flex items-center justify-center">
                  <div className="w-3 h-3 bg-white rounded-full" />
                </div>
              </div>
            )}
          </button>
        ))}
      </div>

      {/* Coming Soon Platforms */}
      {platforms.length < 4 && (
        <div className="mt-6 text-center">
          <p className="text-gray-300 text-sm mb-4 drop-shadow-md">More platforms coming soon</p>
          <div className="flex justify-center gap-4 opacity-50">
            <div className="bg-white/20 backdrop-blur-sm rounded-xl p-4 border border-white/10">
              <div className="text-2xl mb-2">🎮</div>
              <p className="text-xs text-gray-300">Steam</p>
            </div>
            <div className="bg-white/20 backdrop-blur-sm rounded-xl p-4 border border-white/10">
              <div className="text-2xl mb-2">🎯</div>
              <p className="text-xs text-gray-300">Xbox</p>
            </div>
            <div className="bg-white/20 backdrop-blur-sm rounded-xl p-4 border border-white/10">
              <div className="text-2xl mb-2">🎪</div>
              <p className="text-xs text-gray-300">PlayStation</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
