import React, { useState, useEffect } from 'react';
import { Platform } from '../config/platforms';

interface PlayerInputProps {
  platform: Platform;
  onSubmit: (data: { platform: string; playerId: string; region?: string }) => void;
  isLoading?: boolean;
}

export const PlayerInput: React.FC<PlayerInputProps> = ({
  platform,
  onSubmit,
  isLoading = false
}) => {
  const [playerId, setPlayerId] = useState('');
  const [region, setRegion] = useState(platform.regions?.[0]?.id || '');
  const [error, setError] = useState('');

  useEffect(() => {
    setPlayerId('');
    setError('');
    if (platform.regions) {
      setRegion(platform.regions[0].id);
    }
  }, [platform]);

  const validateInput = (value: string): boolean => {
    return platform.inputConfig.validation.test(value);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!playerId.trim()) {
      setError(`${platform.inputConfig.label} is required`);
      return;
    }

    if (!validateInput(playerId.trim())) {
      setError(platform.inputConfig.errorMessage);
      return;
    }

    setError('');
    onSubmit({
      platform: platform.id,
      playerId: playerId.trim(),
      ...(platform.regions && { region })
    });
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div className="bg-gray-900/60 backdrop-blur-xl border border-gray-800 rounded-3xl p-10 shadow-2xl">
        {/* Platform Header */}
        <div className="text-center mb-10">
          <div className={`inline-flex items-center justify-center w-20 h-20 rounded-2xl mb-6 bg-gradient-to-br ${
            platform.id === 'riot' ? 'from-blue-500 to-purple-500' :
            platform.id === 'steam' ? 'from-gray-500 to-slate-500' :
            platform.id === 'xbox' ? 'from-green-500 to-emerald-500' :
            'from-blue-500 to-purple-500'
          }`}>
            <span className="text-4xl">{platform.icon}</span>
          </div>
          <h2 className="text-3xl font-black text-white mb-3">
            {platform.displayName}
          </h2>
          <p className="text-gray-400 text-lg">
            Enter your {platform.terminology.player.toLowerCase()} details to begin analysis
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-8">
          {/* Player ID Input */}
          <div>
            <label htmlFor="playerId" className="block text-sm font-bold text-gray-300 mb-3 uppercase tracking-wide">
              {platform.inputConfig.label}
            </label>
            <input
              type="text"
              id="playerId"
              value={playerId}
              onChange={(e) => {
                setPlayerId(e.target.value);
                if (error) setError('');
              }}
              placeholder={platform.inputConfig.placeholder}
              className={`
                w-full px-6 py-4 rounded-xl border-2 transition-all duration-300 text-lg font-medium
                bg-gray-800/50 backdrop-blur-sm text-white placeholder-gray-500
                focus:outline-none focus:ring-4 focus:ring-opacity-50
                ${error 
                  ? 'border-red-500 focus:border-red-400 focus:ring-red-500' 
                  : 'border-gray-700 focus:border-cyan-400 focus:ring-cyan-400'
                }
              `}
              disabled={isLoading}
            />
            <p className="mt-3 text-sm text-gray-500">
              {platform.inputConfig.helpText}
            </p>
            {error && (
              <div className="mt-3 p-4 bg-red-500/10 border border-red-500/20 rounded-lg">
                <p className="text-sm text-red-400 flex items-center gap-2">
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                  {error}
                </p>
              </div>
            )}
          </div>

          {/* Region Selector (if platform has regions) */}
          {platform.regions && (
            <div>
              <label htmlFor="region" className="block text-sm font-bold text-gray-300 mb-3 uppercase tracking-wide">
                Region
              </label>
              <select
                id="region"
                value={region}
                onChange={(e) => setRegion(e.target.value)}
                className="w-full px-6 py-4 rounded-xl border-2 border-gray-700 focus:border-cyan-400 focus:outline-none focus:ring-4 focus:ring-cyan-400 focus:ring-opacity-50 bg-gray-800/50 backdrop-blur-sm text-white text-lg font-medium transition-all duration-300"
                disabled={isLoading}
              >
                {platform.regions.map((r) => (
                  <option key={r.id} value={r.id} className="bg-gray-800">
                    {r.name}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Submit Button */}
          <button
            type="submit"
            disabled={isLoading || !playerId.trim()}
            className={`
              w-full py-5 px-8 rounded-2xl font-bold text-lg transition-all duration-300 transform
              ${isLoading || !playerId.trim()
                ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                : `bg-gradient-to-r ${
                    platform.id === 'riot' ? 'from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600' :
                    platform.id === 'steam' ? 'from-gray-600 to-slate-600 hover:from-gray-700 hover:to-slate-700' :
                    platform.id === 'xbox' ? 'from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600' :
                    'from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600'
                  } text-white hover:scale-105 hover:shadow-2xl active:scale-95`
              }
            `}
          >
            {isLoading ? (
              <div className="flex items-center justify-center gap-3">
                <div className="w-6 h-6 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Analyzing Gaming Data...
              </div>
            ) : (
              `Generate ${platform.name} Wrapped`
            )}
          </button>
        </form>

        {/* Platform-specific tips */}
        <div className="mt-8 p-6 bg-gray-800/30 rounded-2xl border border-gray-700/50">
          <h4 className="text-sm font-bold text-gray-300 mb-4 flex items-center gap-2 uppercase tracking-wide">
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
            Pro Tips
          </h4>
          <ul className="text-sm text-gray-400 space-y-2">
            {platform.id === 'riot' && (
              <>
                <li className="flex items-start gap-2">
                  <span className="text-cyan-400 mt-1">•</span>
                  Make sure your summoner name is spelled correctly
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-cyan-400 mt-1">•</span>
                  We analyze your last 100 ranked and normal games
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-cyan-400 mt-1">•</span>
                  Processing takes about 30-60 seconds
                </li>
              </>
            )}
            {platform.id === 'steam' && (
              <>
                <li className="flex items-start gap-2">
                  <span className="text-cyan-400 mt-1">•</span>
                  Your Steam profile must be public
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-cyan-400 mt-1">•</span>
                  We analyze your game library and achievements
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-cyan-400 mt-1">•</span>
                  Custom URLs work too (e.g., /id/yourname)
                </li>
              </>
            )}
          </ul>
        </div>
      </div>
    </div>
  );
};