import React from 'react';
import { Platform } from '../config/platforms';

interface BentoPlatformGridProps {
  platforms: Platform[];
  onPlatformSelect: (platform: Platform) => void;
}

export const BentoPlatformGrid: React.FC<BentoPlatformGridProps> = ({
  platforms,
  onPlatformSelect,
}) => {
  const getPlatformGlow = (platformId: string) => {
    switch (platformId) {
      case 'riot':
        return 'hover:shadow-2xl hover:shadow-blue-500/25 hover:border-blue-500/50';
      case 'steam':
        return 'hover:shadow-2xl hover:shadow-orange-500/25 hover:border-orange-500/50';
      case 'xbox':
        return 'hover:shadow-2xl hover:shadow-green-500/25 hover:border-green-500/50';
      case 'psn':
        return 'hover:shadow-2xl hover:shadow-purple-500/25 hover:border-purple-500/50';
      default:
        return 'hover:shadow-2xl hover:shadow-[#00FF85]/25 hover:border-[#00FF85]/50';
    }
  };

  const getPlatformAccent = (platformId: string) => {
    switch (platformId) {
      case 'riot':
        return 'from-blue-500 to-indigo-600';
      case 'steam':
        return 'from-orange-500 to-red-600';
      case 'xbox':
        return 'from-green-500 to-emerald-600';
      case 'psn':
        return 'from-purple-500 to-pink-600';
      default:
        return 'from-[#00FF85] to-cyan-400';
    }
  };

  return (
    <section className="py-16 sm:py-20 lg:py-24 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        {/* Section Header */}
        <div className="text-center mb-12 sm:mb-16">
          <h2 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-black text-[#E0E0E0] mb-4 sm:mb-6">
            Choose Your{' '}
            <span className="bg-gradient-to-r from-[#00FF85] to-cyan-400 bg-clip-text text-transparent">
              Platform
            </span>
          </h2>
          <p className="text-lg sm:text-xl text-[#E0E0E0]/70 max-w-3xl mx-auto px-4">
            Select your gaming platform to unlock AI-powered insights and cinematic storytelling
          </p>
        </div>

        {/* Bento Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
          {platforms.map((platform, index) => (
            <button
              key={platform.id}
              onClick={() => onPlatformSelect(platform)}
              className={`
                group relative overflow-hidden rounded-2xl sm:rounded-3xl p-6 sm:p-8 transition-all duration-500 transform hover:scale-105
                bg-[#0D1117]/60 backdrop-blur-xl border border-white/10
                ${getPlatformGlow(platform.id)}
                ${index === 0 ? 'sm:col-span-2 lg:col-span-2' : ''}
              `}
            >
              {/* Ken Burns Background Effect */}
              <div className="absolute inset-0 opacity-10 group-hover:opacity-20 transition-opacity duration-700">
                <div
                  className={`w-full h-full bg-gradient-to-br ${getPlatformAccent(platform.id)} transform group-hover:scale-110 transition-transform duration-[3000ms] ease-out`}
                />
              </div>

              {/* Glow Effect */}
              <div
                className={`
                absolute inset-0 opacity-0 group-hover:opacity-30 transition-opacity duration-500
                bg-gradient-to-br ${getPlatformAccent(platform.id)} blur-xl
              `}
              />

              {/* Content */}
              <div className="relative z-10">
                {/* Platform Icon */}
                <div className="text-5xl sm:text-6xl lg:text-8xl mb-4 sm:mb-6 group-hover:scale-110 transition-transform duration-500">
                  {platform.icon}
                </div>

                {/* Platform Info */}
                <div className="text-left">
                  <h3 className="text-xl sm:text-2xl font-black text-[#E0E0E0] mb-2 group-hover:text-white transition-colors duration-300">
                    {platform.displayName}
                  </h3>
                  <p className="text-[#E0E0E0]/60 mb-3 sm:mb-4 group-hover:text-[#E0E0E0]/80 transition-colors duration-300 text-sm sm:text-base">
                    {platform.name}
                  </p>

                  {/* Stats */}
                  <div className="flex items-center gap-3 sm:gap-4 text-xs sm:text-sm">
                    <span className="text-[#00FF85] font-bold">Active</span>
                    <span className="text-[#E0E0E0]/50">•</span>
                    <span className="text-[#E0E0E0]/60">Real-time data</span>
                  </div>
                </div>

                {/* Arrow */}
                <div className="absolute top-4 sm:top-6 right-4 sm:right-6 opacity-0 group-hover:opacity-100 transition-all duration-300 transform translate-x-2 group-hover:translate-x-0">
                  <svg
                    className="w-5 h-5 sm:w-6 sm:h-6 text-[#E0E0E0]"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z"
                      clipRule="evenodd"
                    />
                  </svg>
                </div>
              </div>
            </button>
          ))}

          {/* Coming Soon Cards */}
          {platforms.length < 4 && (
            <>
              <div className="group relative overflow-hidden rounded-2xl sm:rounded-3xl p-6 sm:p-8 bg-[#0D1117]/30 backdrop-blur-xl border border-white/5 opacity-60">
                <div className="text-4xl sm:text-5xl lg:text-6xl mb-4 sm:mb-6 opacity-50">🎮</div>
                <h3 className="text-lg sm:text-xl font-black text-[#E0E0E0]/50 mb-2">Steam</h3>
                <p className="text-[#E0E0E0]/30 mb-3 sm:mb-4 text-sm sm:text-base">Coming Soon</p>
                <div className="text-xs sm:text-sm text-[#E0E0E0]/30">Q2 2024</div>
              </div>

              <div className="group relative overflow-hidden rounded-2xl sm:rounded-3xl p-6 sm:p-8 bg-[#0D1117]/30 backdrop-blur-xl border border-white/5 opacity-60">
                <div className="text-4xl sm:text-5xl lg:text-6xl mb-4 sm:mb-6 opacity-50">🎯</div>
                <h3 className="text-lg sm:text-xl font-black text-[#E0E0E0]/50 mb-2">Xbox Live</h3>
                <p className="text-[#E0E0E0]/30 mb-3 sm:mb-4 text-sm sm:text-base">Coming Soon</p>
                <div className="text-xs sm:text-sm text-[#E0E0E0]/30">Q3 2024</div>
              </div>
            </>
          )}
        </div>
      </div>
    </section>
  );
};
