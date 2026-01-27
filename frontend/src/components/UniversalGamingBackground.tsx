import React from 'react';
import { Platform } from '../config/platforms';

interface UniversalGamingBackgroundProps {
  platform?: Platform;
}

export const UniversalGamingBackground: React.FC<UniversalGamingBackgroundProps> = ({ platform }) => {
  const getGradientForPlatform = () => {
    if (!platform) {
      return 'from-gray-900 via-black to-gray-900';
    }
    
    switch (platform.id) {
      case 'riot':
        return 'from-blue-900/50 via-black to-purple-900/50';
      case 'steam':
        return 'from-gray-900/50 via-black to-slate-900/50';
      case 'xbox':
        return 'from-green-900/50 via-black to-emerald-900/50';
      case 'psn':
        return 'from-blue-900/50 via-black to-purple-900/50';
      default:
        return 'from-gray-900 via-black to-gray-900';
    }
  };

  const getPlatformIcons = () => {
    if (!platform) {
      return ['🎮', '⚔️', '🎯', '🎪', '🏆', '⭐', '🎲', '🎨'];
    }
    
    switch (platform.id) {
      case 'riot':
        return ['⚔️', '🛡️', '🏹', '⚡', '🔥', '❄️', '🌟', '💎'];
      case 'steam':
        return ['🎮', '🖥️', '⚙️', '🔧', '💻', '🎯', '🏆', '⭐'];
      case 'xbox':
        return ['🎯', '🎮', '🏆', '⭐', '🎲', '🔥', '⚡', '💚'];
      case 'psn':
        return ['🎪', '🎮', '🏆', '⭐', '🎲', '💙', '⚡', '🌟'];
      default:
        return ['🎮', '⚔️', '🎯', '🎪', '🏆', '⭐', '🎲', '🎨'];
    }
  };

  const icons = getPlatformIcons();

  return (
    <div className="fixed inset-0 overflow-hidden pointer-events-none">
      {/* Main gradient background */}
      <div className={`absolute inset-0 bg-gradient-to-br ${getGradientForPlatform()}`} />
      
      {/* Subtle animated orbs */}
      <div className="absolute inset-0 opacity-20">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl animate-blob" />
        <div className="absolute top-3/4 right-1/4 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl animate-blob animation-delay-2000" />
        <div className="absolute bottom-1/4 left-1/2 w-96 h-96 bg-pink-500/10 rounded-full blur-3xl animate-blob animation-delay-4000" />
      </div>
      
      {/* Floating gaming icons - more subtle */}
      <div className="absolute inset-0">
        {icons.slice(0, 6).map((icon, index) => (
          <div
            key={index}
            className="absolute text-white/5 text-4xl animate-float"
            style={{
              left: `${15 + (index * 15) % 70}%`,
              top: `${20 + (index * 12) % 60}%`,
              animationDelay: `${index * 1}s`,
              animationDuration: `${6 + (index % 2)}s`
            }}
          >
            {icon}
          </div>
        ))}
      </div>
      
      {/* Noise texture overlay */}
      <div className="absolute inset-0 opacity-[0.015] mix-blend-overlay" style={{
        backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")`
      }} />
    </div>
  );
};