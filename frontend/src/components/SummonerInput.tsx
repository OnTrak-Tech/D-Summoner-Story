/**
 * SummonerInput component for entering summoner name and region.
 * Includes form validation, region selection, and loading states.
 */

import React, { useState, useCallback, useEffect } from 'react';
import { isValidRegion, formatRegionDisplay, sanitizeSummonerName } from '../services/api';
import { useRecentSearches, useUserPreferences } from '../hooks/useLocalStorage';

interface SummonerInputProps {
  onSubmit: (summonerName: string, region: string) => void;
  isLoading?: boolean;
  disabled?: boolean;
  initialSummonerName?: string;
  initialRegion?: string;
}

interface FormErrors {
  summonerName?: string;
  region?: string;
}

const REGIONS = [
  { value: 'na1', label: 'North America', flag: '🇺🇸' },
  { value: 'euw1', label: 'Europe West', flag: '🇪🇺' },
  { value: 'eun1', label: 'Europe Nordic & East', flag: '🇪🇺' },
  { value: 'kr', label: 'Korea', flag: '🇰🇷' },
  { value: 'br1', label: 'Brazil', flag: '🇧🇷' },
  { value: 'la1', label: 'Latin America North', flag: '🌎' },
  { value: 'la2', label: 'Latin America South', flag: '🌎' },
  { value: 'oc1', label: 'Oceania', flag: '🇦🇺' },
  { value: 'ru', label: 'Russia', flag: '🇷🇺' },
  { value: 'tr1', label: 'Turkey', flag: '🇹🇷' },
  { value: 'jp1', label: 'Japan', flag: '🇯🇵' },
];

export const SummonerInput: React.FC<SummonerInputProps> = ({
  onSubmit,
  isLoading = false,
  disabled = false,
  initialSummonerName = '',
  initialRegion = 'na1',
}) => {
  const { storedValue: recentSearches, setValue: setRecentSearches } = useRecentSearches();
  const { storedValue: preferences, setValue: setPreferences } = useUserPreferences();
  
  const [summonerName, setSummonerName] = useState(initialSummonerName || preferences.lastSummonerName);
  const [region, setRegion] = useState(initialRegion || preferences.region);
  const [errors, setErrors] = useState<FormErrors>({});
  const [touched, setTouched] = useState<{ summonerName: boolean; region: boolean }>({
    summonerName: false,
    region: false,
  });
  const [showRecentSearches, setShowRecentSearches] = useState(false);

  const validateSummonerName = useCallback((name: string): string | undefined => {
    const trimmed = name.trim();
    
    if (!trimmed) {
      return 'Riot ID is required';
    }
    
    if (trimmed.length < 3) {
      return 'Riot ID must be at least 3 characters';
    }
    
    if (trimmed.length > 20) {
      return 'Riot ID must be 20 characters or less';
    }
    
    // Check for invalid characters (Riot ID allows letters, numbers, spaces, and # for tag)
    const validPattern = /^[a-zA-Z0-9\s._#-]+$/;
    if (!validPattern.test(trimmed)) {
      return 'Riot ID contains invalid characters';
    }
    
    return undefined;
  }, []);

  const validateRegion = useCallback((regionValue: string): string | undefined => {
    if (!regionValue) {
      return 'Region is required';
    }
    
    if (!isValidRegion(regionValue)) {
      return 'Invalid region selected';
    }
    
    return undefined;
  }, []);

  const validateForm = useCallback((): boolean => {
    const newErrors: FormErrors = {};
    
    const summonerNameError = validateSummonerName(summonerName);
    if (summonerNameError) {
      newErrors.summonerName = summonerNameError;
    }
    
    const regionError = validateRegion(region);
    if (regionError) {
      newErrors.region = regionError;
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [summonerName, region, validateSummonerName, validateRegion]);

  const handleSummonerNameChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSummonerName(value);
    
    // Clear error when user starts typing
    if (touched.summonerName && errors.summonerName) {
      const error = validateSummonerName(value);
      setErrors(prev => ({ ...prev, summonerName: error }));
    }
  }, [touched.summonerName, errors.summonerName, validateSummonerName]);

  const handleSummonerNameBlur = useCallback(() => {
    setTouched(prev => ({ ...prev, summonerName: true }));
    const error = validateSummonerName(summonerName);
    setErrors(prev => ({ ...prev, summonerName: error }));
  }, [summonerName, validateSummonerName]);

  const handleRegionChange = useCallback((e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value;
    setRegion(value);
    
    // Clear error when user changes selection
    if (touched.region && errors.region) {
      const error = validateRegion(value);
      setErrors(prev => ({ ...prev, region: error }));
    }
  }, [touched.region, errors.region, validateRegion]);

  const handleRegionBlur = useCallback(() => {
    setTouched(prev => ({ ...prev, region: true }));
    const error = validateRegion(region);
    setErrors(prev => ({ ...prev, region: error }));
  }, [region, validateRegion]);

  const handleSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    
    // Mark all fields as touched
    setTouched({ summonerName: true, region: true });
    
    if (validateForm()) {
      const sanitizedName = sanitizeSummonerName(summonerName);
      
      // Save to recent searches
      const newSearch = {
        summonerName: sanitizedName,
        region,
        timestamp: Date.now(),
      };
      
      const updatedSearches = [
        newSearch,
        ...recentSearches.filter(
          search => !(search.summonerName === sanitizedName && search.region === region)
        )
      ].slice(0, 5); // Keep only 5 recent searches
      
      setRecentSearches(updatedSearches);
      
      // Update preferences
      setPreferences({
        ...preferences,
        lastSummonerName: sanitizedName,
        region,
      });
      
      onSubmit(sanitizedName, region);
    }
  }, [summonerName, region, validateForm, onSubmit, recentSearches, setRecentSearches, preferences, setPreferences]);

  const handleRecentSearchClick = useCallback((search: typeof recentSearches[0]) => {
    setSummonerName(search.summonerName);
    setRegion(search.region);
    setShowRecentSearches(false);
  }, []);

  const isFormDisabled = isLoading || disabled;

  return (
    <div className="w-full">
      <div className="bg-white/70 backdrop-blur-sm rounded-3xl shadow-xl border border-white/20 p-8">
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-gradient-to-br from-amber-100 to-orange-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <span className="text-2xl">✨</span>
          </div>
          <h2 className="text-3xl font-bold text-gray-800 mb-3">
            Get Your Year in Review
          </h2>
          <p className="text-gray-600 text-lg leading-relaxed">
            Enter your Riot ID to discover your League of Legends journey
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Summoner Name Input */}
          <div className="relative">
            <label 
              htmlFor="summoner-name" 
              className="block text-sm font-semibold text-gray-700 mb-2"
            >
              Riot ID
            </label>
            <div className="relative">
              <input
                id="summoner-name"
                type="text"
                value={summonerName}
                onChange={handleSummonerNameChange}
                onBlur={handleSummonerNameBlur}
                onFocus={() => setShowRecentSearches(recentSearches.length > 0)}
                disabled={isFormDisabled}
                placeholder="Enter your Riot ID (e.g., PlayerName#TAG)"
                className={`
                  w-full px-4 py-4 border-2 rounded-2xl shadow-sm placeholder-gray-400 text-lg
                  focus:outline-none focus:ring-4 focus:ring-orange-200 focus:border-orange-400
                  disabled:bg-gray-50 disabled:text-gray-500 disabled:cursor-not-allowed
                  transition-all duration-200
                  ${errors.summonerName 
                    ? 'border-red-300 focus:ring-red-200 focus:border-red-400' 
                    : 'border-gray-200 hover:border-gray-300'
                  }
                `}
              />
              {recentSearches.length > 0 && (
                <button
                  type="button"
                  onClick={() => setShowRecentSearches(!showRecentSearches)}
                  className="absolute right-4 top-4 text-gray-400 hover:text-gray-600 transition-colors"
                >
                  🕒
                </button>
              )}
            </div>
            
            {/* Recent Searches Dropdown */}
            {showRecentSearches && recentSearches.length > 0 && (
              <div className="absolute z-10 w-full mt-2 bg-white/95 backdrop-blur-sm border border-gray-200 rounded-2xl shadow-xl">
                <div className="py-2">
                  <div className="px-4 py-2 text-xs font-semibold text-gray-500 bg-gray-50/80 rounded-t-2xl">
                    Recent Searches
                  </div>
                  {recentSearches.map((search, index) => (
                    <button
                      key={index}
                      type="button"
                      onClick={() => handleRecentSearchClick(search)}
                      className="w-full px-4 py-3 text-left hover:bg-gray-50/80 flex items-center justify-between transition-colors"
                    >
                      <span className="text-gray-900 font-medium">{search.summonerName}</span>
                      <span className="text-sm text-gray-500 bg-gray-100 px-2 py-1 rounded-lg">
                        {search.region.toUpperCase()}
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            )}
            
            {errors.summonerName && (
              <p className="mt-2 text-sm text-red-600 font-medium" role="alert">
                {errors.summonerName}
              </p>
            )}
          </div>

          {/* Region Selection */}
          <div>
            <label 
              htmlFor="region" 
              className="block text-sm font-semibold text-gray-700 mb-2"
            >
              Region
            </label>
            <select
              id="region"
              value={region}
              onChange={handleRegionChange}
              onBlur={handleRegionBlur}
              disabled={isFormDisabled}
              className={`
                w-full px-4 py-4 border-2 rounded-2xl shadow-sm text-lg
                focus:outline-none focus:ring-4 focus:ring-orange-200 focus:border-orange-400
                disabled:bg-gray-50 disabled:text-gray-500 disabled:cursor-not-allowed
                transition-all duration-200
                ${errors.region 
                  ? 'border-red-300 focus:ring-red-200 focus:border-red-400' 
                  : 'border-gray-200 hover:border-gray-300'
                }
              `}
            >
              {REGIONS.map(({ value, label, flag }) => (
                <option key={value} value={value}>
                  {flag} {label}
                </option>
              ))}
            </select>
            {errors.region && (
              <p className="mt-2 text-sm text-red-600 font-medium" role="alert">
                {errors.region}
              </p>
            )}
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={isFormDisabled}
            className={`
              w-full py-4 px-6 rounded-2xl font-semibold text-lg text-white
              focus:outline-none focus:ring-4 focus:ring-offset-2 focus:ring-orange-300
              disabled:cursor-not-allowed disabled:opacity-50
              transition-all duration-200 shadow-lg hover:shadow-xl
              ${isFormDisabled
                ? 'bg-gray-400'
                : 'bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 active:from-amber-700 active:to-orange-700'
              }
            `}
          >
            {isLoading ? (
              <div className="flex items-center justify-center">
                <svg 
                  className="animate-spin -ml-1 mr-3 h-6 w-6 text-white" 
                  xmlns="http://www.w3.org/2000/svg" 
                  fill="none" 
                  viewBox="0 0 24 24"
                >
                  <circle 
                    className="opacity-25" 
                    cx="12" 
                    cy="12" 
                    r="10" 
                    stroke="currentColor" 
                    strokeWidth="4"
                  />
                  <path 
                    className="opacity-75" 
                    fill="currentColor" 
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
                Creating your story...
              </div>
            ) : (
              <span className="flex items-center justify-center">
                <span className="mr-2">✨</span>
                Generate My Year in Review
              </span>
            )}
          </button>
        </form>

        {/* Help Text */}
        <div className="mt-6 text-center">
          <p className="text-sm text-gray-500 leading-relaxed">
            We'll analyze your ranked and normal games from the past year to create a beautiful, personalized story
          </p>
        </div>
      </div>
    </div>
  );
};