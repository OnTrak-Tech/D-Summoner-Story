/**
 * React hook for managing the complete recap generation workflow.
 * Handles authentication, data fetching, processing, and recap retrieval.
 */

import { useState, useCallback, useRef } from 'react';
import { 
  apiService, 
  AuthRequest, 
  AuthResponse, 
  FetchResponse, 
  JobStatus, 
  RecapData, 
  APIError 
} from '../services/api';

export interface RecapGenerationState {
  // Current step in the process
  step: 'idle' | 'authenticating' | 'fetching' | 'processing' | 'generating' | 'completed' | 'error';
  
  // Loading states
  isLoading: boolean;
  
  // Progress tracking
  progress: number;
  progressMessage: string;
  
  // Data
  sessionId: string | null;
  jobId: string | null;
  recapData: RecapData | null;
  
  // Error handling
  error: string | null;
  errorCode: string | null;
  
  // Summoner info
  summonerInfo: {
    name: string;
    level: number;
    region: string;
  } | null;
}

export interface RecapGenerationActions {
  startGeneration: (summonerName: string, region: string) => Promise<void>;
  reset: () => void;
  retry: () => void;
}

const initialState: RecapGenerationState = {
  step: 'idle',
  isLoading: false,
  progress: 0,
  progressMessage: '',
  sessionId: null,
  jobId: null,
  recapData: null,
  error: null,
  errorCode: null,
  summonerInfo: null,
};

export const useRecapGeneration = (): RecapGenerationState & RecapGenerationActions => {
  const [state, setState] = useState<RecapGenerationState>(initialState);
  const abortControllerRef = useRef<AbortController | null>(null);
  const lastRequestRef = useRef<{ summonerName: string; region: string } | null>(null);

  const updateState = useCallback((updates: Partial<RecapGenerationState>) => {
    setState(prev => ({ ...prev, ...updates }));
  }, []);

  const setError = useCallback((error: string, code?: string) => {
    updateState({
      step: 'error',
      isLoading: false,
      error,
      errorCode: code || null,
    });
  }, [updateState]);

  const setProgress = useCallback((progress: number, message: string, step?: RecapGenerationState['step']) => {
    updateState({
      progress,
      progressMessage: message,
      ...(step && { step }),
    });
  }, [updateState]);

  const startGeneration = useCallback(async (summonerName: string, region: string) => {
    // Cancel any existing request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    
    // Create new abort controller
    abortControllerRef.current = new AbortController();
    
    // Store request for retry functionality
    lastRequestRef.current = { summonerName, region };

    try {
      // Reset state
      updateState({
        ...initialState,
        step: 'authenticating',
        isLoading: true,
      });

      setProgress(5, 'Authenticating summoner...', 'authenticating');

      // Step 1: Authenticate
      const authRequest: AuthRequest = {
        summoner_name: summonerName,
        region: region.toLowerCase(),
      };

      const authResponse: AuthResponse = await apiService.authenticate(authRequest);
      
      if (authResponse.status !== 'valid') {
        throw new APIError('Authentication failed', 401, 'AUTH_FAILED');
      }

      updateState({ sessionId: authResponse.session_id });
      setProgress(15, 'Starting data fetch...', 'fetching');

      // Step 2: Start data fetching
      const fetchRequest = {
        session_id: authResponse.session_id,
        summoner_name: summonerName,
        region: region.toLowerCase(),
      };

      const fetchResponse: FetchResponse = await apiService.startDataFetch(fetchRequest);
      
      updateState({ 
        jobId: fetchResponse.job_id,
        summonerInfo: fetchResponse.summoner_info || null,
      });

      setProgress(25, 'Fetching match history...', 'processing');

      // Step 3: Poll job status
      const finalStatus = await apiService.pollJobStatus(
        fetchResponse.job_id,
        (status: JobStatus) => {
          // Update progress based on job status
          let progressValue = 25;
          let message = 'Processing...';
          let step: RecapGenerationState['step'] = 'processing';

          switch (status.status) {
            case 'fetching':
              progressValue = Math.max(25, status.progress || 25);
              message = 'Fetching match data from Riot API...';
              step = 'fetching';
              break;
            case 'processing':
              progressValue = Math.max(50, status.progress || 50);
              message = 'Analyzing your performance...';
              step = 'processing';
              break;
            case 'generating':
              progressValue = Math.max(75, status.progress || 75);
              message = 'Generating your personalized recap...';
              step = 'generating';
              break;
            case 'completed':
              progressValue = 90;
              message = 'Almost done...';
              step = 'generating';
              break;
          }

          setProgress(progressValue, message, step);
        }
      );

      if (finalStatus.status === 'failed') {
        throw new APIError(
          finalStatus.error_message || 'Processing failed',
          500,
          'PROCESSING_FAILED'
        );
      }

      setProgress(95, 'Loading your year in review...', 'generating');

      // Step 4: Get recap data
      const recapData = await apiService.getRecap(authResponse.session_id);

      // Complete
      updateState({
        step: 'completed',
        isLoading: false,
        progress: 100,
        progressMessage: 'Your year in review is ready!',
        recapData,
      });

    } catch (error) {
      console.error('Recap generation failed:', error);
      
      if (error instanceof APIError) {
        let userMessage = error.message;
        
        // Provide user-friendly error messages
        switch (error.code) {
          case 'SUMMONER_NOT_FOUND':
            userMessage = `Summoner "${summonerName}" not found in ${region.toUpperCase()}. Please check the spelling and region.`;
            break;
          case 'INSUFFICIENT_DATA':
            userMessage = 'Not enough match history found. Play more games and try again!';
            break;
          case 'RATE_LIMITED':
            userMessage = 'Too many requests right now. Please wait a moment and try again.';
            break;
          case 'NETWORK_ERROR':
            userMessage = 'Network connection error. Please check your internet and try again.';
            break;
          case 'TIMEOUT':
            userMessage = 'The request took too long. Please try again.';
            break;
          default:
            if (error.status >= 500) {
              userMessage = 'Server error occurred. Please try again later.';
            }
        }
        
        setError(userMessage, error.code);
      } else {
        setError('An unexpected error occurred. Please try again.');
      }
    }
  }, [updateState, setError, setProgress]);

  const reset = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setState(initialState);
    lastRequestRef.current = null;
  }, []);

  const retry = useCallback(() => {
    if (lastRequestRef.current) {
      const { summonerName, region } = lastRequestRef.current;
      startGeneration(summonerName, region);
    }
  }, [startGeneration]);

  return {
    ...state,
    startGeneration,
    reset,
    retry,
  };
};