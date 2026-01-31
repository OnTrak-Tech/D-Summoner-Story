import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useStartRecapCallback, useRecapStatus } from '../hooks/recapHooks';
import { LoadingIndicator } from '../components/LoadingIndicator';
import { apiService } from '../services/api';

export const LoadingPage: React.FC = () => {
  const { platform, region, summonerName } = useParams<{
    platform: string;
    region: string;
    summonerName: string;
  }>();
  const navigate = useNavigate();

  // State for job management
  const [jobId, setJobId] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Mutations/Queries
  const startRecap = useStartRecapCallback();
  const { data: statusData, isError: isStatusError, error: statusError } = useRecapStatus(jobId);

  // Start process on mount
  useEffect(() => {
    if (summonerName && region && !jobId && !startRecap.isPending && !error) {
      startRecap.mutate(
        { summonerName, region, platform },
        {
          onSuccess: (data) => {
            setSessionId(data.sessionId);
            setJobId(data.jobId);
          },
          onError: (err) => {
            setError(err.message);
          },
        }
      );
    }
  }, [summonerName, region, platform, jobId, startRecap, error]);

  // Handle completion
  useEffect(() => {
    if (statusData?.status === 'completed' && sessionId) {
      // Small delay to let user see 100%
      setTimeout(() => {
        navigate(`/recap/${sessionId}`);
      }, 500);
    } else if (statusData?.status === 'failed') {
      setError(statusData.error_message || 'Processing failed');
    }
  }, [statusData, sessionId, navigate]);

  // Error State Render
  if (error || isStatusError || startRecap.isError) {
    return (
      <div className="min-h-screen bg-brand-dark flex items-center justify-center p-6 text-white">
        <div className="max-w-lg w-full bg-brand-secondary/80 backdrop-blur-xl border border-brand-vibrant/20 rounded-3xl p-10 shadow-2xl">
          <div className="text-center mb-8">
            <span className="text-4xl">⚠️</span>
            <h2 className="text-2xl font-bold mt-4 mb-2">Something went wrong</h2>
            <p className="text-slate-400">
              {error || statusError?.message || startRecap.error?.message}
            </p>
          </div>
          <button
            onClick={() => navigate('/')}
            className="w-full py-3 bg-brand-vibrant rounded-xl font-bold hover:bg-brand-deep transition-all"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  // Calculate props for LoadingIndicator
  let step: 'authenticating' | 'fetching' | 'processing' | 'generating' = 'authenticating';
  let progress = 5;
  let message = 'Initializing...';

  if (startRecap.isPending) {
    step = 'authenticating';
    progress = 10;
    message = 'Connecting to Riot API...';
  } else if (jobId && statusData) {
    // Map API status to UI step
    switch (statusData.status) {
      case 'fetching':
        step = 'fetching';
        progress = Math.max(20, statusData.progress || 20);
        message = 'Fetching match history...';
        break;
      case 'processing':
        step = 'processing';
        progress = Math.max(50, statusData.progress || 50);
        message = 'Analyzing performance data...';
        break;
      case 'generating':
        step = 'generating';
        progress = Math.max(80, statusData.progress || 80);
        message = 'Generating your unique story...';
        break;
      case 'completed':
        step = 'generating';
        progress = 100;
        message = 'Finalizing...';
        break;
      default: // pending
        step = 'fetching';
        progress = 15;
        message = 'Waiting in queue...';
    }
  }

  return (
    <div className="min-h-screen bg-brand-dark flex items-center justify-center p-6">
      <LoadingIndicator
        step={step}
        progress={progress}
        message={message}
        playerName={summonerName}
      />
    </div>
  );
};
