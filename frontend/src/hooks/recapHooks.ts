import { useMutation, useQuery } from '@tanstack/react-query';
import { apiService, JobStatus, RecapData } from '../services/api';

/**
 * Mutation to authenticate and start the data fetching process.
 * Returns both session_id and job_id.
 */
export const useStartRecapCallback = () => {
  return useMutation({
    mutationFn: async ({
      summonerName,
      region,
      platform,
    }: {
      summonerName: string;
      region: string;
      platform?: string;
    }) => {
      // 1. Authenticate
      const authRes = await apiService.authenticate({ summoner_name: summonerName, region });

      if (authRes.status !== 'valid') {
        throw new Error('Authentication failed: Invalid summoner or region');
      }

      // 2. Start Data Fetch
      const fetchRes = await apiService.startDataFetch({
        session_id: authRes.session_id,
        summoner_name: summonerName,
        region,
      });

      return {
        sessionId: authRes.session_id,
        jobId: fetchRes.job_id,
        summonerInfo: fetchRes.summoner_info,
      };
    },
  });
};

/**
 * Query to poll the status of a running job.
 * auto-refetches until completed or failed.
 */
export const useRecapStatus = (jobId: string | null) => {
  return useQuery({
    queryKey: ['recapStatus', jobId],
    queryFn: async () => {
      if (!jobId) throw new Error('No job ID');
      return apiService.getJobStatus(jobId);
    },
    enabled: !!jobId,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (!data) return 1000;
      if (data.status === 'completed' || data.status === 'failed') return false;
      return 1000; // Poll every 1s
    },
    // We want to keep previous data while fetching next status to avoid flicker
    placeholderData: (previousData) => previousData,
  });
};

/**
 * Query to fetch the final recap data using session ID.
 */
export const useRecapData = (sessionId: string | null) => {
  return useQuery({
    queryKey: ['recapData', sessionId],
    queryFn: async () => {
      if (!sessionId) throw new Error('No session ID');
      return apiService.getRecap(sessionId);
    },
    enabled: !!sessionId,
    retry: 1,
  });
};
