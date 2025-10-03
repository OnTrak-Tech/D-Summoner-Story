/**
 * SummonerInput component for entering summoner name and region.
 * Includes form validation, region selection, and loading states.
 */

import React, { useState, useCallback } from 'react';
import { isValidRegion, formatRegionDisplay, sanitizeSummonerName } from '../services/api';

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
  { value: 'na1', label: 'North America' },
  { value: 'euw1', label: 'Europe West' },
  { value: 'eun1', label: 'Europe Nordic & East' },
  { value: 'kr', label: 'Korea' },
  { value: 'br1', label: 'Brazil' },
  { value: 'la1', label: 'Latin America North' },
  { value: 'la2', label: 'Latin America South' },
  { value: 'oc1', label: 'Oceania' },
  { value: 'ru', label: 'Russia' },
  { value: 'tr1', label: 'Turkey' },
  { value: 'jp1', label: 'Japan' },
];

export const SummonerInput: React.FC<SummonerInputProps> = ({
  onSubmit,
  isLoading = false,
  disabled = false,
  initialSummonerName = '',
  initialRegion = 'na1',
}) => {
  const [summonerName, setSummonerName] = useState(initialSummonerName);
  const [region, setRegion] = useState(initialRegion);
  const [errors, setErrors] = useState<FormErrors>({});
  const [touched, setTouched] = useState<{ summonerName: boolean; region: boolean }>({
    summonerName: false,
    region: false,
  });

  const validateSummonerName = useCallback((name: string): string | undefined => {
    const trimmed = name.trim();
    
    if (!trimmed) {
      return 'Summoner name is required';
    }
    
    if (trimmed.length < 3) {
      return 'Summoner name must be at least 3 characters';
    }
    
    if (trimmed.length > 16) {
      return 'Summoner name must be 16 characters or less';
    }
    
    // Check for invalid characters (Riot allows letters, numbers, spaces, and some special chars)
    const validPattern = /^[a-zA-Z0-9\s._-]+$/;
    if (!validPattern.test(trimmed)) {
      return 'Summoner name contains invalid characters';
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
      onSubmit(sanitizedName, region);
    }
  }, [summonerName, region, validateForm, onSubmit]);

  const isFormDisabled = isLoading || disabled;

  return (
    <div className="w-full max-w-md mx-auto">
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="text-center mb-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            Get Your Year in Review
          </h2>
          <p className="text-gray-600">
            Enter your summoner name to see your League of Legends journey
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Summoner Name Input */}
          <div>
            <label 
              htmlFor="summoner-name" 
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Summoner Name
            </label>
            <input
              id="summoner-name"
              type="text"
              value={summonerName}
              onChange={handleSummonerNameChange}
              onBlur={handleSummonerNameBlur}
              disabled={isFormDisabled}
              placeholder="Enter your summoner name"
              className={`
                w-full px-3 py-2 border rounded-md shadow-sm placeholder-gray-400
                focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                disabled:bg-gray-50 disabled:text-gray-500 disabled:cursor-not-allowed
                ${errors.summonerName 
                  ? 'border-red-300 focus:ring-red-500 focus:border-red-500' 
                  : 'border-gray-300'
                }
              `}
            />
            {errors.summonerName && (
              <p className="mt-1 text-sm text-red-600" role="alert">
                {errors.summonerName}
              </p>
            )}
          </div>

          {/* Region Selection */}
          <div>
            <label 
              htmlFor="region" 
              className="block text-sm font-medium text-gray-700 mb-1"
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
                w-full px-3 py-2 border rounded-md shadow-sm
                focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                disabled:bg-gray-50 disabled:text-gray-500 disabled:cursor-not-allowed
                ${errors.region 
                  ? 'border-red-300 focus:ring-red-500 focus:border-red-500' 
                  : 'border-gray-300'
                }
              `}
            >
              {REGIONS.map(({ value, label }) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
            {errors.region && (
              <p className="mt-1 text-sm text-red-600" role="alert">
                {errors.region}
              </p>
            )}
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={isFormDisabled}
            className={`
              w-full py-3 px-4 rounded-md font-medium text-white
              focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500
              disabled:cursor-not-allowed disabled:opacity-50
              transition-colors duration-200
              ${isFormDisabled
                ? 'bg-gray-400'
                : 'bg-blue-600 hover:bg-blue-700 active:bg-blue-800'
              }
            `}
          >
            {isLoading ? (
              <div className="flex items-center justify-center">
                <svg 
                  className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" 
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
                Processing...
              </div>
            ) : (
              'Generate My Year in Review'
            )}
          </button>
        </form>

        {/* Help Text */}
        <div className="mt-4 text-center">
          <p className="text-xs text-gray-500">
            We'll analyze your ranked and normal games from the past year
          </p>
        </div>
      </div>
    </div>
  );
};