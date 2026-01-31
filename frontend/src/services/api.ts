/**
 * API service layer for communicating with the backend Lambda functions.
 * Handles authentication, data fetching, processing status, and recap retrieval.
 */

export interface AuthRequest {
  summoner_name: string;
  region: string;
}

export interface AuthResponse {
  session_id: string;
  status: 'valid' | 'invalid';
}

export interface FetchRequest {
  session_id: string;
  summoner_name: string;
  region: string;
}

export interface FetchResponse {
  job_id: string;
  status: string;
  summoner_info?: {
    id: string;
    name: string;
    level: number;
    region: string;
  };
  match_count?: number;
  message: string;
}

export interface PersonalityProfile {
  type: string;
  description: string;
  traits: string[];
}

export interface ChampionSuggestion {
  champion: string;
  confidence: number;
  reason: string;
}

export interface SeasonPrediction {
  predicted_rank: string;
  timeline: string;
  confidence: number;
  key_factors: string[];
}

export interface RivalAnalysis {
  overall_ranking: string;
  comparison_group: string;
  strengths: string[];
  weaknesses: string[];
}

export interface HighlightMatch {
  champion: string;
  kills: number;
  deaths: number;
  assists: number;
  kda: number;
  win: boolean;
}

export interface JobStatus {
  job_id: string;
  status: 'pending' | 'fetching' | 'processing' | 'generating' | 'completed' | 'failed';
  progress: number;
  error_message?: string;
  created_at: string;
  updated_at: string;
}

export interface RecapData {
  session_id: string;
  summoner_name: string;
  region: string;
  narrative: string;
  statistics: {
    total_games: number;
    win_rate: number;
    avg_kda: number;
    total_wins: number;
    total_losses: number;
    avg_kills: number;
    avg_deaths: number;
    avg_assists: number;
    improvement_trend: number;
    consistency_score: number;
    champion_stats: Array<{
      champion_name: string;
      games_played: number;
      win_rate: number;
    }>;
    monthly_trends: Array<{
      month: string;
      year: number;
      win_rate: number;
      avg_kda: number;
      games: number;
    }>;
  };
  visualizations: Array<{
    chart_type: string;
    data: any;
    options: any;
  }>;
  highlights: string[];
  achievements: string[];
  fun_facts: string[];
  recommendations: string[];

  // Enhanced Fields
  personality_profile?: PersonalityProfile;
  champion_suggestions?: ChampionSuggestion[];
  next_season_prediction?: SeasonPrediction;
  rival_analysis?: RivalAnalysis;
  highlight_matches?: HighlightMatch[];
  champion_improvements?: string[];
  behavioral_patterns?: string[];

  share_url?: string;
  generated_at: string;
  served_at: string;
}

export interface ShareResponse {
  share_url: string;
  preview_text: string;
  message: string;
}

export class APIError extends Error {
  constructor(
    message: string,
    public status: number,
    public code?: string,
    public details?: any
  ) {
    super(message);
    this.name = 'APIError';
  }
}

class APIService {
  private baseURL: string;
  private timeout: number;

  constructor() {
    // Get API endpoint from environment or use default
    this.baseURL =
      (import.meta.env?.VITE_API_ENDPOINT as string) ||
      'https://your-api-gateway-url.execute-api.us-east-1.amazonaws.com';
    this.timeout = 30000; // 30 seconds
  }

  private async makeRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    const config: RequestInit = {
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      clearTimeout(timeoutId);

      if (!response.ok) {
        let errorData;
        try {
          errorData = await response.json();
        } catch {
          errorData = { message: 'Unknown error occurred' };
        }

        throw new APIError(
          errorData.message || `HTTP ${response.status}`,
          response.status,
          errorData.error,
          errorData.details
        );
      }

      return await response.json();
    } catch (error) {
      clearTimeout(timeoutId);
      if (error instanceof APIError) {
        throw error;
      }

      // Handle network errors, timeouts, etc.
      throw new APIError(
        error instanceof Error ? error.message : 'Network error occurred',
        0,
        'NETWORK_ERROR'
      );
    }
  }

  /**
   * Authenticate summoner and create session
   */
  async authenticate(request: AuthRequest): Promise<AuthResponse> {
    return this.makeRequest<AuthResponse>('/api/v1/auth', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  /**
   * Start data fetching process
   */
  async startDataFetch(request: FetchRequest): Promise<FetchResponse> {
    return this.makeRequest<FetchResponse>('/api/v1/fetch', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  /**
   * Check job status
   */
  async getJobStatus(jobId: string): Promise<JobStatus> {
    return this.makeRequest<JobStatus>(`/api/v1/status/${jobId}`, {
      method: 'GET',
    });
  }

  /**
   * Get complete recap data
   */
  async getRecap(sessionId: string): Promise<RecapData> {
    return this.makeRequest<RecapData>(`/api/v1/recap/${sessionId}`, {
      method: 'GET',
    });
  }

  /**
   * Generate share link
   */
  async generateShareLink(sessionId: string): Promise<ShareResponse> {
    return this.makeRequest<ShareResponse>(`/api/v1/share/${sessionId}`, {
      method: 'POST',
    });
  }

  /**
   * Poll job status until completion
   */
  async pollJobStatus(
    jobId: string,
    onProgress?: (status: JobStatus) => void,
    maxAttempts: number = 60,
    intervalMs: number = 2000
  ): Promise<JobStatus> {
    let attempts = 0;

    while (attempts < maxAttempts) {
      try {
        const status = await this.getJobStatus(jobId);

        if (onProgress) {
          onProgress(status);
        }

        if (status.status === 'completed' || status.status === 'failed') {
          return status;
        }

        // Wait before next poll
        await new Promise((resolve) => setTimeout(resolve, intervalMs));
        attempts++;
      } catch (error) {
        console.error('Error polling job status:', error);
        attempts++;

        if (attempts >= maxAttempts) {
          throw error;
        }

        // Wait before retry
        await new Promise((resolve) => setTimeout(resolve, intervalMs));
      }
    }

    throw new APIError('Job status polling timed out', 408, 'TIMEOUT');
  }
}

// Export singleton instance
export const apiService = new APIService();

// Export utility functions
export const isValidRegion = (region: string): boolean => {
  const validRegions = [
    'na1',
    'euw1',
    'eun1',
    'kr',
    'br1',
    'la1',
    'la2',
    'oc1',
    'ru',
    'tr1',
    'jp1',
    'sg2',
    'tw2',
    'vn2',
  ];
  return validRegions.includes(region.toLowerCase());
};

export const formatRegionDisplay = (region: string): string => {
  const regionMap: Record<string, string> = {
    na1: 'North America',
    euw1: 'Europe West',
    eun1: 'Europe Nordic & East',
    kr: 'Korea',
    br1: 'Brazil',
    la1: 'Latin America North',
    la2: 'Latin America South',
    oc1: 'Oceania',
    ru: 'Russia',
    tr1: 'Turkey',
    jp1: 'Japan',
    sg2: 'Singapore',
    tw2: 'Taiwan',
    vn2: 'Vietnam',
  };

  return regionMap[region.toLowerCase()] || region.toUpperCase();
};

export const sanitizeSummonerName = (name: string): string => {
  return name.trim().replace(/\s+/g, '');
};
