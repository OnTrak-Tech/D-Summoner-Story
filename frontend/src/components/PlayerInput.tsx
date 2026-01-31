import React, { useState, useEffect } from 'react';
import { Platform } from '../config/platforms';
import { PlayerInputSchema } from '../utils/validation';

interface PlayerInputProps {
  platform: Platform;
  onSubmit: (data: { platform: string; playerId: string; region?: string }) => void;
  isLoading?: boolean;
  onBack?: () => void;
}

export const PlayerInput: React.FC<PlayerInputProps> = ({
  platform,
  onSubmit,
  isLoading = false,
  onBack,
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

    const payload = {
      platform: platform.id as any, // Cast to any to let Zod handle the enum validation
      playerId: playerId.trim(),
      region: platform.regions ? region : undefined,
    };

    const result = PlayerInputSchema.safeParse(payload);

    if (!result.success) {
      // Prioritize specific field errors
      const fieldError = result.error.issues[0];
      setError(fieldError.message);
      return;
    }

    setError('');
    onSubmit({
      platform: platform.id,
      playerId: playerId.trim(),
      ...(platform.regions && { region }),
    });
  };

  return (
    <div className="w-full max-w-2xl mx-auto px-4">
      <div className="bg-brand-secondary/80 backdrop-blur-xl border border-brand-vibrant/20 rounded-2xl sm:rounded-3xl shadow-2xl p-6 sm:p-8 relative">
        {onBack && (
          <button
            onClick={onBack}
            className="absolute top-6 left-6 text-slate-400 hover:text-white transition-colors"
            title="Go Back"
          >
            ← Back
          </button>
        )}
        {/* Platform Header */}
        <div className="text-center mb-6 sm:mb-8">
          <div
            className={`inline-flex items-center justify-center w-12 h-12 sm:w-16 sm:h-16 rounded-xl sm:rounded-2xl bg-gradient-to-br ${platform.color.secondary} mb-3 sm:mb-4`}
          >
            <span className="text-xl sm:text-2xl">{platform.icon}</span>
          </div>
          <h2 className="text-xl sm:text-2xl font-semibold text-white mb-2">
            {platform.displayName}
          </h2>
          <p className="text-slate-400 text-sm sm:text-base">
            Enter your {platform.terminology.player.toLowerCase()} details to get started
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 sm:space-y-6">
          {/* Player ID Input */}
          <div>
            <label htmlFor="playerId" className="block text-sm font-medium text-white mb-2">
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
                w-full px-4 py-3 rounded-xl border-2 transition-all duration-200
                focus:outline-none focus:ring-4 focus:ring-opacity-20
                ${
                  error
                    ? 'border-red-400/50 focus:border-red-500 focus:ring-red-500 bg-red-500/5'
                    : 'border-brand-vibrant/30 focus:border-brand-vibrant focus:ring-brand-vibrant bg-brand-secondary/50'
                }
                backdrop-blur-sm text-white placeholder-slate-500
              `}
              disabled={isLoading}
            />
            <p className="mt-2 text-xs sm:text-sm text-slate-400">
              {platform.inputConfig.helpText}
            </p>
            {error && (
              <p className="mt-2 text-sm text-red-400 flex items-center gap-2">
                <span>⚠️</span>
                {error}
              </p>
            )}
          </div>

          {/* Region Selector (if platform has regions) */}
          {platform.regions && (
            <div>
              <label htmlFor="region" className="block text-sm font-medium text-white mb-2">
                Region
              </label>
              <select
                id="region"
                value={region}
                onChange={(e) => setRegion(e.target.value)}
                className="w-full px-4 py-3 rounded-xl border-2 border-brand-vibrant/30 focus:border-brand-vibrant focus:outline-none focus:ring-4 focus:ring-brand-vibrant focus:ring-opacity-20 bg-brand-secondary/50 backdrop-blur-sm transition-all duration-200 text-white"
                disabled={isLoading}
              >
                {platform.regions.map((r) => (
                  <option key={r.id} value={r.id} className="bg-brand-secondary text-white">
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
              w-full py-3 sm:py-4 px-6 rounded-xl sm:rounded-2xl font-semibold text-white transition-all duration-300
              ${
                isLoading || !playerId.trim()
                  ? 'bg-slate-500/20 cursor-not-allowed text-slate-500'
                  : `bg-gradient-to-r ${platform.color.primary} hover:shadow-xl hover:scale-105 active:scale-95`
              }
              shadow-lg text-sm sm:text-base
            `}
          >
            {isLoading ? (
              <div className="flex items-center justify-center gap-3">
                <div className="w-4 h-4 sm:w-5 sm:h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Analyzing Your Gaming Data...
              </div>
            ) : (
              `Generate My ${platform.name} Year in Review`
            )}
          </button>
        </form>

        {/* Platform-specific tips */}
        <div className="mt-4 sm:mt-6 p-4 bg-brand-secondary/30 rounded-xl border border-brand-vibrant/10">
          <h4 className="text-sm font-medium text-white mb-2 flex items-center gap-2">
            <span>💡</span>
            Tips for {platform.name}
          </h4>
          <ul className="text-xs sm:text-sm text-slate-400 space-y-1">
            {platform.id === 'riot' && (
              <>
                <li>• Make sure your summoner name is spelled correctly</li>
                <li>• We analyze your last 100 ranked and normal games</li>
                <li>• Processing takes about 30-60 seconds</li>
              </>
            )}
            {platform.id === 'steam' && (
              <>
                <li>• Your Steam profile must be public</li>
                <li>• We analyze your game library and achievements</li>
                <li>• Custom URLs work too (e.g., /id/yourname)</li>
              </>
            )}
            {platform.id === 'xbox' && (
              <>
                <li>• Your Xbox profile must be public</li>
                <li>• We analyze your recent gaming activity</li>
                <li>• Gamertag is case-insensitive</li>
              </>
            )}
            {platform.id === 'psn' && (
              <>
                <li>• Your PSN profile must be public</li>
                <li>• We analyze your trophy data and playtime</li>
                <li>• Online ID is case-sensitive</li>
              </>
            )}
          </ul>
        </div>
      </div>
    </div>
  );
};
