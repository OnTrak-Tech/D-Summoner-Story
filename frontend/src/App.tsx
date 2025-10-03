/**
 * Main App component for the League of Legends Year in Review application.
 * Orchestrates the complete user flow from input to recap display.
 */

import React, { useCallback, useEffect } from 'react';
import { ErrorBoundary } from './components/ErrorBoundary';
import { SummonerInput } from './components/SummonerInput';
import { LoadingIndicator } from './components/LoadingIndicator';
import { RecapViewer } from './components/RecapViewer';
import { ThemeToggle } from './components/ThemeToggle';
import { MobileMenu } from './components/MobileMenu';
import { useRecapGeneration } from './hooks/useRecapGeneration';
import { useRecapCache } from './hooks/useLocalStorage';
import { apiService } from './services/api';

const App: React.FC = () => {
  const {
    step,
    isLoading,
    progress,
    progressMessage,
    recapData,
    error,
    errorCode,
    summonerInfo,
    startGeneration,
    reset,
    retry,
  } = useRecapGeneration();

  const { storedValue: cachedRecap, setValue: setCachedRecap } = useRecapCache();

  // Cache recap data when completed
  useEffect(() => {
    if (recapData && step === 'completed') {
      setCachedRecap(recapData);
    }
  }, [recapData, step, setCachedRecap]);

  const handleSubmit = useCallback((summonerName: string, region: string) => {
    startGeneration(summonerName, region);
  }, [startGeneration]);

  const handleShare = useCallback(async () => {
    if (!recapData) return;
    
    try {
      const shareResponse = await apiService.generateShareLink(recapData.session_id);
      
      // Try to use Web Share API if available
      if (navigator.share) {
        await navigator.share({
          title: `${recapData.summoner_name}'s League of Legends Year in Review`,
          text: shareResponse.preview_text,
          url: shareResponse.share_url,
        });
      } else {
        // Fallback to copying to clipboard
        await navigator.clipboard.writeText(shareResponse.share_url);
        alert('Share link copied to clipboard!');
      }
    } catch (error) {
      console.error('Failed to share:', error);
      // Fallback sharing method
      const shareText = `Check out ${recapData.summoner_name}'s League of Legends Year in Review! ${recapData.statistics.win_rate.toFixed(1)}% win rate with ${recapData.statistics.avg_kda.toFixed(2)} KDA!`;
      
      if (navigator.clipboard) {
        try {
          await navigator.clipboard.writeText(shareText);
          alert('Share text copied to clipboard!');
        } catch {
          alert('Unable to share. Please copy the URL manually.');
        }
      }
    }
  }, [recapData]);

  const renderContent = () => {
    // Error state
    if (step === 'error') {
      return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
          <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-6">
            <div className="text-center mb-6">
              <div className="text-6xl mb-4">😔</div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                Something went wrong
              </h2>
              <p className="text-gray-600 mb-4">
                {error || 'An unexpected error occurred'}
              </p>
              
              {/* Specific error guidance */}
              {errorCode === 'SUMMONER_NOT_FOUND' && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                  <p className="text-sm text-blue-800">
                    💡 <strong>Tip:</strong> Make sure you've entered the correct summoner name and selected the right region.
                  </p>
                </div>
              )}
              
              {errorCode === 'INSUFFICIENT_DATA' && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
                  <p className="text-sm text-yellow-800">
                    🎮 <strong>Play more games!</strong> We need at least a few matches from this year to create your recap.
                  </p>
                </div>
              )}
              
              {errorCode === 'RATE_LIMITED' && (
                <div className="bg-orange-50 border border-orange-200 rounded-lg p-4 mb-4">
                  <p className="text-sm text-orange-800">
                    ⏰ <strong>Too many requests.</strong> Please wait a moment before trying again.
                  </p>
                </div>
              )}
            </div>
            
            <div className="space-y-3">
              <button
                onClick={retry}
                className="w-full py-3 px-4 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
              >
                Try Again
              </button>
              <button
                onClick={reset}
                className="w-full py-3 px-4 bg-gray-600 text-white rounded-lg font-medium hover:bg-gray-700 transition-colors"
              >
                Start Over
              </button>
            </div>
          </div>
        </div>
      );
    }

    // Loading states
    if (isLoading && step !== 'idle') {
      return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
          <LoadingIndicator
            progress={progress}
            message={progressMessage}
            step={step as any}
            summonerName={summonerInfo?.name}
          />
        </div>
      );
    }

    // Completed state - show recap
    if (step === 'completed' && recapData) {
      return (
        <div className="min-h-screen bg-gray-50 py-8 px-4">
          <RecapViewer
            recapData={recapData}
            onShare={handleShare}
            onStartNew={reset}
          />
        </div>
      );
    }

    // Default state - show input form
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 dark:from-gray-900 dark:to-purple-900 flex items-center justify-center p-4 transition-colors">
        {/* Mobile Menu */}
        <MobileMenu onRecentSearchSelect={handleSubmit} />
        
        <div className="w-full max-w-6xl">
          {/* Header with Theme Toggle */}
          <div className="hidden md:flex justify-end mb-4">
            <ThemeToggle />
          </div>
          
          {/* Main Header */}
          <div className="text-center mb-8">
            <h1 className="text-4xl md:text-6xl font-bold text-gray-900 dark:text-white mb-4">
              <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                D-Summoner-Story
              </span>
            </h1>
            <p className="text-xl text-gray-600 dark:text-gray-300 mb-2">
              Your League of Legends Year in Review
            </p>
            <p className="text-gray-500 dark:text-gray-400">
              Discover your gaming journey with AI-powered insights
            </p>
          </div>

          {/* Features */}
          <div className="grid md:grid-cols-3 gap-6 mb-8">
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm border border-gray-200 dark:border-gray-700 transition-colors">
              <div className="text-3xl mb-3">📊</div>
              <h3 className="font-semibold text-gray-900 dark:text-white mb-2">Performance Analytics</h3>
              <p className="text-sm text-gray-600 dark:text-gray-300">
                Deep dive into your KDA, win rates, and champion performance
              </p>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm border border-gray-200 dark:border-gray-700 transition-colors">
              <div className="text-3xl mb-3">🤖</div>
              <h3 className="font-semibold text-gray-900 dark:text-white mb-2">AI-Powered Insights</h3>
              <p className="text-sm text-gray-300 dark:text-gray-300">
                Get personalized narratives about your gaming journey
              </p>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm border border-gray-200 dark:border-gray-700 transition-colors">
              <div className="text-3xl mb-3">📈</div>
              <h3 className="font-semibold text-gray-900 dark:text-white mb-2">Trend Analysis</h3>
              <p className="text-sm text-gray-600 dark:text-gray-300">
                See how your skills evolved throughout the year
              </p>
            </div>
          </div>

          {/* Cached Recap Quick Access */}
          {cachedRecap && step === 'idle' && (
            <div className="mb-8 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-blue-900 dark:text-blue-100">
                    🎮 Previous Recap Available
                  </h3>
                  <p className="text-sm text-blue-700 dark:text-blue-300">
                    {cachedRecap.summoner_name}'s year in review from {cachedRecap.region.toUpperCase()}
                  </p>
                </div>
                <button
                  onClick={() => {
                    // You could implement a way to load cached recap here
                    console.log('Load cached recap:', cachedRecap);
                  }}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
                >
                  View Previous
                </button>
              </div>
            </div>
          )}

          {/* Input Form */}
          <SummonerInput
            onSubmit={handleSubmit}
            isLoading={isLoading}
          />

          {/* Footer */}
          <div className="text-center mt-8">
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Powered by Riot Games API • Built with ❤️ for the League community
            </p>
            <div className="mt-2 flex justify-center gap-4 text-xs text-gray-400 dark:text-gray-500">
              <span>🔒 Secure</span>
              <span>⚡ Fast</span>
              <span>🤖 AI-Powered</span>
              <span>📱 Mobile-Friendly</span>
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <ErrorBoundary
      onError={(error, errorInfo) => {
        console.error('Application error:', error, errorInfo);
        // In production, you might want to log this to an error reporting service
      }}
    >
      {renderContent()}
    </ErrorBoundary>
  );
};

export default App;
