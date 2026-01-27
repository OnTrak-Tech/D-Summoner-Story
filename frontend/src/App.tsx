/**
 * Main App component for the League of Legends Year in Review application.
 * Orchestrates the complete user flow from input to recap display.
 */

import React, { useCallback, useState, useEffect } from 'react';
import { ErrorBoundary } from './components/ErrorBoundary';
import { SummonerInput } from './components/SummonerInput';
import { PlatformSelector } from './components/PlatformSelector';
import { PlayerInput } from './components/PlayerInput';
import { LoadingIndicator } from './components/LoadingIndicator';
import { RecapViewer } from './components/RecapViewer';
import { GamingBackground } from './components/GamingBackground';
import { UniversalGamingBackground } from './components/UniversalGamingBackground';
import { useRecapGeneration } from './hooks/useRecapGeneration';
import { getActivePlatforms, Platform } from './config/platforms';
import { apiService } from './services/api';

const App: React.FC = () => {
  const [selectedPlatform, setSelectedPlatform] = useState<Platform | null>(null);
  const [showPlatformSelector, setShowPlatformSelector] = useState(true);
  const activePlatforms = getActivePlatforms();
  
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

  // Auto-select platform if only one is available
  useEffect(() => {
    if (activePlatforms.length === 1 && !selectedPlatform) {
      setSelectedPlatform(activePlatforms[0]);
      setShowPlatformSelector(false);
    }
  }, [activePlatforms, selectedPlatform]);

  const handlePlatformSelect = (platform: Platform) => {
    setSelectedPlatform(platform);
    setShowPlatformSelector(false);
  };

  const handlePlayerSubmit = (data: { platform: string; playerId: string; region?: string }) => {
    // Convert to legacy format for backward compatibility
    startGeneration(data.playerId, data.region || 'na1');
  };

  const handleStartOver = () => {
    reset();
    if (activePlatforms.length > 1) {
      setSelectedPlatform(null);
      setShowPlatformSelector(true);
    }
  };

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
                onClick={handleStartOver}
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
            onStartNew={handleStartOver}
          />
        </div>
      );
    }

    // Default state - show input form
    return (
      <div className="min-h-screen bg-black relative overflow-hidden">
        <UniversalGamingBackground platform={selectedPlatform || undefined} />
        
        {/* Cyberpunk grid overlay */}
        <div className="absolute inset-0 opacity-20">
          <div className="h-full w-full" style={{
            backgroundImage: `
              linear-gradient(rgba(0, 255, 255, 0.1) 1px, transparent 1px),
              linear-gradient(90deg, rgba(0, 255, 255, 0.1) 1px, transparent 1px)
            `,
            backgroundSize: '40px 40px'
          }} />
        </div>
        
        {/* Main content */}
        <div className="relative z-10 min-h-screen flex flex-col">
          {/* Header */}
          <div className="flex items-center justify-between p-8">
            <div className="flex items-center space-x-4">
              <div className="w-12 h-12 bg-gradient-to-r from-cyan-400 to-purple-500 rounded-lg flex items-center justify-center">
                <span className="text-2xl font-bold text-black">G</span>
              </div>
              <h1 className="text-3xl md:text-4xl font-black tracking-tight">
                <span className="bg-gradient-to-r from-cyan-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
                  GAMING WRAPPED
                </span>
              </h1>
            </div>
            {selectedPlatform && !showPlatformSelector && (
              <button
                onClick={() => setShowPlatformSelector(true)}
                className="px-6 py-3 bg-gray-900/80 backdrop-blur-sm border border-gray-700 rounded-lg text-gray-300 hover:text-white hover:border-cyan-400 transition-all duration-300 font-medium"
              >
                Switch Platform
              </button>
            )}
          </div>

          {/* Main content area */}
          <div className="flex-1 flex items-center justify-center px-8 pb-8">
            <div className="w-full max-w-7xl">
              
              {/* Platform Selection or Input Form */}
              <div className="mb-20">
                {showPlatformSelector ? (
                  <PlatformSelector
                    platforms={activePlatforms}
                    selectedPlatform={selectedPlatform}
                    onPlatformSelect={handlePlatformSelect}
                    disabled={isLoading}
                  />
                ) : selectedPlatform ? (
                  <PlayerInput
                    platform={selectedPlatform}
                    onSubmit={handlePlayerSubmit}
                    isLoading={isLoading}
                  />
                ) : (
                  <div className="max-w-2xl mx-auto">
                    <SummonerInput
                      onSubmit={handleSubmit}
                      isLoading={isLoading}
                    />
                  </div>
                )}
              </div>

              {/* Features Grid */}
              <div className="grid md:grid-cols-3 gap-8 mb-16">
                <div className="group relative">
                  <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/20 to-blue-500/20 rounded-2xl blur-xl group-hover:blur-2xl transition-all duration-500" />
                  <div className="relative bg-gray-900/60 backdrop-blur-xl border border-gray-800 rounded-2xl p-8 hover:border-cyan-500/50 transition-all duration-500">
                    <div className="w-14 h-14 bg-gradient-to-r from-cyan-400 to-blue-500 rounded-xl flex items-center justify-center mb-6">
                      <svg className="w-7 h-7 text-black" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M2 10a8 8 0 018-8v8h8a8 8 0 11-16 0z" />
                        <path d="M12 2.252A8.014 8.014 0 0117.748 8H12V2.252z" />
                      </svg>
                    </div>
                    <h3 className="text-xl font-bold text-white mb-3">Performance Analytics</h3>
                    <p className="text-gray-400 leading-relaxed">
                      Advanced metrics and insights across all your gaming platforms with real-time analysis
                    </p>
                  </div>
                </div>
                
                <div className="group relative">
                  <div className="absolute inset-0 bg-gradient-to-r from-purple-500/20 to-pink-500/20 rounded-2xl blur-xl group-hover:blur-2xl transition-all duration-500" />
                  <div className="relative bg-gray-900/60 backdrop-blur-xl border border-gray-800 rounded-2xl p-8 hover:border-purple-500/50 transition-all duration-500">
                    <div className="w-14 h-14 bg-gradient-to-r from-purple-400 to-pink-500 rounded-xl flex items-center justify-center mb-6">
                      <svg className="w-7 h-7 text-black" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M3 5a2 2 0 012-2h10a2 2 0 012 2v8a2 2 0 01-2 2h-2.22l.123.489.804.804A1 1 0 0113 18H7a1 1 0 01-.707-1.707l.804-.804L7.22 15H5a2 2 0 01-2-2V5zm5.771 7H5V5h10v7H8.771z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <h3 className="text-xl font-bold text-white mb-3">AI-Powered Insights</h3>
                    <p className="text-gray-400 leading-relaxed">
                      Machine learning algorithms analyze your gameplay patterns and provide personalized recommendations
                    </p>
                  </div>
                </div>
                
                <div className="group relative">
                  <div className="absolute inset-0 bg-gradient-to-r from-green-500/20 to-emerald-500/20 rounded-2xl blur-xl group-hover:blur-2xl transition-all duration-500" />
                  <div className="relative bg-gray-900/60 backdrop-blur-xl border border-gray-800 rounded-2xl p-8 hover:border-green-500/50 transition-all duration-500">
                    <div className="w-14 h-14 bg-gradient-to-r from-green-400 to-emerald-500 rounded-xl flex items-center justify-center mb-6">
                      <svg className="w-7 h-7 text-black" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M12 7a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0V8.414l-4.293 4.293a1 1 0 01-1.414 0L8 10.414l-4.293 4.293a1 1 0 01-1.414-1.414l5-5a1 1 0 011.414 0L11 10.586 14.586 7H12z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <h3 className="text-xl font-bold text-white mb-3">Growth Tracking</h3>
                    <p className="text-gray-400 leading-relaxed">
                      Track your skill progression over time with detailed performance metrics and trend analysis
                    </p>
                  </div>
                </div>
              </div>

              {/* Footer */}
              <div className="text-center">
                <p className="text-gray-500 mb-6 text-lg">
                  {selectedPlatform 
                    ? `Powered by ${selectedPlatform.name} API • Professional Gaming Analytics`
                    : 'Multi-Platform Gaming Analytics • Built for Competitive Gamers'
                  }
                </p>
                <div className="flex justify-center items-center space-x-8 text-sm">
                  <div className="flex items-center space-x-2 text-green-400">
                    <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                    <span>Secure</span>
                  </div>
                  <div className="flex items-center space-x-2 text-cyan-400">
                    <div className="w-2 h-2 bg-cyan-400 rounded-full animate-pulse" />
                    <span>Real-time</span>
                  </div>
                  <div className="flex items-center space-x-2 text-purple-400">
                    <div className="w-2 h-2 bg-purple-400 rounded-full animate-pulse" />
                    <span>AI-Powered</span>
                  </div>
                  <div className="flex items-center space-x-2 text-pink-400">
                    <div className="w-2 h-2 bg-pink-400 rounded-full animate-pulse" />
                    <span>Pro-Grade</span>
                  </div>
                </div>
              </div>
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