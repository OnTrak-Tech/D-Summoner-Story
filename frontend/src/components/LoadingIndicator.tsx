/**
 * LoadingIndicator component with progress tracking and engaging animations.
 * Shows different states during the recap generation process.
 */

import React from 'react';

interface LoadingIndicatorProps {
  progress: number; // 0-100
  message: string;
  step: 'authenticating' | 'fetching' | 'processing' | 'generating';
  summonerName?: string;
  estimatedTimeRemaining?: number; 
}

interface StepInfo {
  icon: string;
  title: string;
  description: string;
  color: string;
}

const STEP_INFO: Record<LoadingIndicatorProps['step'], StepInfo> = {
  authenticating: {
    icon: '🔐',
    title: 'Authenticating',
    description: 'Verifying your summoner information',
    color: 'orange',
  },
  fetching: {
    icon: '📊',
    title: 'Fetching Data',
    description: 'Gathering your match history from Riot Games',
    color: 'burnt orange',
  },
  processing: {
    icon: '⚡',
    title: 'Processing',
    description: 'Analyzing your performance and calculating statistics',
    color: 'yellow',
  },
  generating: {
    icon: '🤖',
    title: 'Generating Insights',
    description: 'Creating your personalized year-in-review with AI',
    color: 'green',
  },
};

const formatTime = (seconds: number): string => {
  if (seconds < 60) {
    return `${seconds}s`;
  }
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return `${minutes}m ${remainingSeconds}s`;
};

export const LoadingIndicator: React.FC<LoadingIndicatorProps> = ({
  progress,
  message,
  step,
  summonerName,
  estimatedTimeRemaining,
}) => {
  const stepInfo = STEP_INFO[step];
  const progressPercentage = Math.max(0, Math.min(100, progress));

  return (
    <div className="w-full max-w-lg mx-auto">
      <div className="bg-white rounded-lg shadow-lg p-8">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="text-4xl mb-3 animate-bounce">
            {stepInfo.icon}
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            {stepInfo.title}
          </h2>
          {summonerName && (
            <p className="text-lg text-gray-600">
              Analyzing <span className="font-semibold text-blue-600">{summonerName}</span>'s year
            </p>
          )}
        </div>

        {/* Progress Bar */}
        <div className="mb-6">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium text-gray-700">
              Progress
            </span>
            <span className="text-sm font-medium text-gray-700">
              {Math.round(progressPercentage)}%
            </span>
          </div>
          
          <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
            <div
              className={`
                h-full rounded-full transition-all duration-500 ease-out
                bg-gradient-to-r from-blue-500 to-purple-600
                ${progressPercentage > 0 ? 'animate-pulse' : ''}
              `}
              style={{ width: `${progressPercentage}%` }}
            />
          </div>
        </div>

        {/* Current Step Info */}
        <div className="mb-6">
          <div className={`
            p-4 rounded-lg border-l-4 
            ${stepInfo.color === 'blue' ? 'bg-blue-50 border-blue-400' : ''}
            ${stepInfo.color === 'purple' ? 'bg-purple-50 border-purple-400' : ''}
            ${stepInfo.color === 'yellow' ? 'bg-yellow-50 border-yellow-400' : ''}
            ${stepInfo.color === 'green' ? 'bg-green-50 border-green-400' : ''}
          `}>
            <p className="font-medium text-gray-900 mb-1">
              {message}
            </p>
            <p className="text-sm text-gray-600">
              {stepInfo.description}
            </p>
          </div>
        </div>

        {/* Estimated Time */}
        {estimatedTimeRemaining && estimatedTimeRemaining > 0 && (
          <div className="text-center mb-6">
            <p className="text-sm text-gray-500">
              Estimated time remaining: {formatTime(estimatedTimeRemaining)}
            </p>
          </div>
        )}

        {/* Step Indicators */}
        <div className="flex justify-between items-center">
          {Object.entries(STEP_INFO).map(([stepKey, info], index) => {
            const isActive = stepKey === step;
            const isCompleted = Object.keys(STEP_INFO).indexOf(stepKey) < Object.keys(STEP_INFO).indexOf(step);
            
            return (
              <div key={stepKey} className="flex flex-col items-center">
                <div className={`
                  w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium
                  transition-all duration-300
                  ${isCompleted 
                    ? 'bg-green-500 text-white' 
                    : isActive 
                      ? 'bg-blue-500 text-white animate-pulse' 
                      : 'bg-gray-200 text-gray-500'
                  }
                `}>
                  {isCompleted ? '✓' : index + 1}
                </div>
                <span className={`
                  text-xs mt-1 text-center max-w-16
                  ${isActive ? 'text-blue-600 font-medium' : 'text-gray-500'}
                `}>
                  {info.title}
                </span>
              </div>
            );
          })}
        </div>

        {/* Fun Facts */}
        <div className="mt-8 p-4 bg-gray-50 rounded-lg">
          <h3 className="text-sm font-medium text-gray-900 mb-2">
            💡 Did you know?
          </h3>
          <p className="text-sm text-gray-600">
            {step === 'authenticating' && "We're securely connecting to Riot Games' servers to verify your account."}
            {step === 'fetching' && "We can analyze up to 1000 of your most recent matches to create comprehensive insights."}
            {step === 'processing' && "Our algorithms calculate over 50 different statistics to understand your playstyle."}
            {step === 'generating' && "AI is crafting a personalized narrative that captures your unique League journey this year."}
          </p>
        </div>

        {/* Loading Animation */}
        <div className="flex justify-center mt-6">
          <div className="flex space-x-1">
            {[0, 1, 2].map((i) => (
              <div
                key={i}
                className={`
                  w-2 h-2 rounded-full bg-blue-500
                  animate-bounce
                `}
                style={{
                  animationDelay: `${i * 0.1}s`,
                  animationDuration: '0.6s',
                }}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};