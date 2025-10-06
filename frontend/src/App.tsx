/**
 * Main App component for the League of Legends Year in Review application.
 * Orchestrates the complete user flow from input to recap display.
 */

import React, { useCallback } from 'react';
import { ErrorBoundary } from './components/ErrorBoundary';
import { SummonerInput } from './components/SummonerInput';
import { LoadingIndicator } from './components/LoadingIndicator';
import { RecapViewer } from './components/RecapViewer';

import { useRecapGeneration } from './hooks/useRecapGeneration';

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
          title: `${recapData?.summoner_name || 'Player'}'s League of Legends Year in Review`,
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
      const shareText = `Check out ${recapData?.summoner_name || 'Player'}'s League of Legends Year in Review! ${recapData?.statistics?.win_rate?.toFixed(1) || 0}% win rate with ${recapData?.statistics?.avg_kda?.toFixed(2) || 0} KDA!`;
      
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
        <div className="min-h-screen bg-gradient-to-br from-rose-50 via-orange-50 to-amber-50 flex items-center justify-center p-6">
          <div className="max-w-lg w-full bg-white/80 backdrop-blur-sm rounded-3xl shadow-xl border border-white/20 p-8">
            <div className="text-center mb-8">
              <div className="w-20 h-20 mx-auto mb-6 bg-gradient-to-br from-rose-100 to-orange-100 rounded-full flex items-center justify-center">
                <span className="text-3xl">😔</span>
              </div>
              <h2 className="text-2xl font-semibold text-gray-800 mb-3">
                Oops, something went wrong
              </h2>
              <p className="text-gray-600 leading-relaxed">
                {error || 'An unexpected error occurred'}
              </p>
              
              {/* Specific error guidance */}
              {errorCode === 'SUMMONER_NOT_FOUND' && (
                <div className="bg-blue-50/80 border border-blue-100 rounded-2xl p-4 mt-6">
                  <p className="text-sm text-blue-700 leading-relaxed">
                    💡 <strong>Tip:</strong> Double-check your summoner name and region selection.
                  </p>
                </div>
              )}
              
              {errorCode === 'INSUFFICIENT_DATA' && (
                <div className="bg-amber-50/80 border border-amber-100 rounded-2xl p-4 mt-6">
                  <p className="text-sm text-amber-700 leading-relaxed">
                    🎮 <strong>Play more games!</strong> We need recent matches to create your recap.
                  </p>
                </div>
              )}
              
              {errorCode === 'RATE_LIMITED' && (
                <div className="bg-orange-50/80 border border-orange-100 rounded-2xl p-4 mt-6">
                  <p className="text-sm text-orange-700 leading-relaxed">
                    ⏰ <strong>Too many requests.</strong> Please wait a moment before trying again.
                  </p>
                </div>
              )}
            </div>
            
            <div className="space-y-3">
              <button
                onClick={retry}
                className="w-full py-4 px-6 bg-gradient-to-r from-blue-500 to-indigo-500 text-white rounded-2xl font-medium hover:from-blue-600 hover:to-indigo-600 transition-all duration-200 shadow-lg hover:shadow-xl"
              >
                Try Again
              </button>
              <button
                onClick={reset}
                className="w-full py-4 px-6 bg-gray-100 text-gray-700 rounded-2xl font-medium hover:bg-gray-200 transition-all duration-200"
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
        <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50 flex items-center justify-center p-6">
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
        <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-teal-50 to-cyan-50 py-8 px-4">
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
      <div className="min-h-screen bg-gradient-to-br from-amber-50 via-orange-50 to-rose-50 flex items-center justify-center p-6">
        <div className="w-full max-w-6xl">
          
          {/* Main Header */}
          <div className="text-center mb-12">
            <div className="mb-8">
              <h1 className="text-5xl md:text-7xl font-bold mb-4 leading-tight">
                <span className="bg-gradient-to-r from-amber-600 via-orange-600 to-rose-600 bg-clip-text text-transparent">
                  D-Summoner-Story
                </span>
              </h1>
              <div className="w-24 h-1 bg-gradient-to-r from-amber-400 to-rose-400 mx-auto rounded-full"></div>
            </div>
            <p className="text-2xl text-gray-700 mb-3 font-light">
              Your League of Legends Year in Review
            </p>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto leading-relaxed">
              Discover your gaming journey with beautiful insights and AI-powered storytelling
            </p>
          </div>

          {/* Input Form */}
          <div className="max-w-2xl mx-auto mb-16">
            <SummonerInput
              onSubmit={handleSubmit}
              isLoading={isLoading}
            />
          </div>

          {/* Features */}
          <div className="grid md:grid-cols-3 gap-8 mb-12">
            <div className="group bg-white/60 backdrop-blur-sm rounded-3xl p-8 shadow-lg border border-white/20 hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
              <div className="w-16 h-16 bg-gradient-to-br from-blue-100 to-indigo-100 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
                <span className="text-2xl">📊</span>
              </div>
              <h3 className="text-xl font-semibold text-gray-800 mb-3">Performance Analytics</h3>
              <p className="text-gray-600 leading-relaxed">
                Deep dive into your KDA, win rates, and champion mastery with beautiful visualizations
              </p>
            </div>
            <div className="group bg-white/60 backdrop-blur-sm rounded-3xl p-8 shadow-lg border border-white/20 hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
              <div className="w-16 h-16 bg-gradient-to-br from-purple-100 to-pink-100 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
                <span className="text-2xl">🤖</span>
              </div>
              <h3 className="text-xl font-semibold text-gray-800 mb-3">AI-Powered Insights</h3>
              <p className="text-gray-600 leading-relaxed">
                Get personalized narratives and meaningful stories about your gaming journey
              </p>
            </div>
            <div className="group bg-white/60 backdrop-blur-sm rounded-3xl p-8 shadow-lg border border-white/20 hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
              <div className="w-16 h-16 bg-gradient-to-br from-emerald-100 to-teal-100 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
                <span className="text-2xl">📈</span>
              </div>
              <h3 className="text-xl font-semibold text-gray-800 mb-3">Growth Tracking</h3>
              <p className="text-gray-600 leading-relaxed">
                See how your skills evolved throughout the year with trend analysis
              </p>
            </div>
          </div>

          {/* Footer */}
          <div className="text-center mt-16">
            <p className="text-gray-500 mb-4 text-lg">
              Powered by Riot Games API • Built with ❤️ for the League community
            </p>
            <div className="flex justify-center gap-8 text-sm text-gray-400">
              <span className="flex items-center gap-2">
                <span className="w-2 h-2 bg-green-400 rounded-full"></span>
                Secure
              </span>
              <span className="flex items-center gap-2">
                <span className="w-2 h-2 bg-blue-400 rounded-full"></span>
                Fast
              </span>
              <span className="flex items-center gap-2">
                <span className="w-2 h-2 bg-purple-400 rounded-full"></span>
                AI-Powered
              </span>
              <span className="flex items-center gap-2">
                <span className="w-2 h-2 bg-orange-400 rounded-full"></span>
                Mobile-Friendly
              </span>
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