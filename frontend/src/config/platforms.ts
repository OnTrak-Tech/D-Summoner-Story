export interface Platform {
  id: string;
  name: string;
  displayName: string;
  icon: string;
  color: {
    primary: string;
    secondary: string;
    gradient: string;
  };
  inputConfig: {
    label: string;
    placeholder: string;
    helpText: string;
    validation: RegExp;
    errorMessage: string;
  };
  regions?: Array<{
    id: string;
    name: string;
  }>;
  metrics: {
    primary: string;
    secondary: string;
    performance: string;
  };
  terminology: {
    player: string;
    match: string;
    character: string;
    performance: string;
  };
}

export const PLATFORMS: Record<string, Platform> = {
  riot: {
    id: 'riot',
    name: 'League of Legends',
    displayName: 'League of Legends',
    icon: '⚔️',
    color: {
      primary: 'from-blue-500 to-indigo-600',
      secondary: 'from-blue-100 to-indigo-100',
      gradient: 'from-blue-50 via-indigo-50 to-purple-50',
    },
    inputConfig: {
      label: 'Summoner Name',
      placeholder: 'Enter your summoner name',
      helpText: 'Your in-game summoner name (case sensitive)',
      validation: /^[0-9\p{L} _\.]+$/u,
      errorMessage: 'Please enter a valid summoner name',
    },
    regions: [
      { id: 'na1', name: 'North America' },
      { id: 'euw1', name: 'Europe West' },
      { id: 'eun1', name: 'Europe Nordic & East' },
      { id: 'kr', name: 'Korea' },
      { id: 'jp1', name: 'Japan' },
      { id: 'br1', name: 'Brazil' },
      { id: 'la1', name: 'Latin America North' },
      { id: 'la2', name: 'Latin America South' },
      { id: 'oc1', name: 'Oceania' },
      { id: 'tr1', name: 'Turkey' },
      { id: 'ru', name: 'Russia' },
    ],
    metrics: {
      primary: 'Win Rate',
      secondary: 'KDA',
      performance: 'LP Gained',
    },
    terminology: {
      player: 'Summoner',
      match: 'Match',
      character: 'Champion',
      performance: 'KDA',
    },
  },
  steam: {
    id: 'steam',
    name: 'Steam',
    displayName: 'Steam Games',
    icon: '🎮',
    color: {
      primary: 'from-gray-600 to-gray-800',
      secondary: 'from-gray-100 to-gray-200',
      gradient: 'from-gray-50 via-slate-50 to-zinc-50',
    },
    inputConfig: {
      label: 'Steam ID',
      placeholder: 'Steam ID or Profile URL',
      helpText: 'Your Steam ID, custom URL, or profile link',
      validation:
        /^(https?:\/\/)?(www\.)?steamcommunity\.com\/(profiles|id)\/[a-zA-Z0-9_-]+\/?$|^[0-9]{17}$|^[a-zA-Z0-9_-]{2,32}$/,
      errorMessage: 'Please enter a valid Steam ID or profile URL',
    },
    metrics: {
      primary: 'Hours Played',
      secondary: 'Achievement Rate',
      performance: 'Games Completed',
    },
    terminology: {
      player: 'Player',
      match: 'Session',
      character: 'Character',
      performance: 'Score',
    },
  },
  xbox: {
    id: 'xbox',
    name: 'Xbox Live',
    displayName: 'Xbox Live',
    icon: '🎯',
    color: {
      primary: 'from-green-500 to-emerald-600',
      secondary: 'from-green-100 to-emerald-100',
      gradient: 'from-green-50 via-emerald-50 to-teal-50',
    },
    inputConfig: {
      label: 'Gamertag',
      placeholder: 'Enter your Xbox Gamertag',
      helpText: 'Your Xbox Live Gamertag',
      validation: /^[a-zA-Z0-9 ]{1,15}$/,
      errorMessage: 'Gamertag must be 1-15 characters (letters, numbers, spaces)',
    },
    metrics: {
      primary: 'Gamerscore',
      secondary: 'Achievement Rate',
      performance: 'Hours Played',
    },
    terminology: {
      player: 'Gamer',
      match: 'Game',
      character: 'Character',
      performance: 'Score',
    },
  },
  psn: {
    id: 'psn',
    name: 'PlayStation',
    displayName: 'PlayStation Network',
    icon: '🎪',
    color: {
      primary: 'from-blue-600 to-purple-600',
      secondary: 'from-blue-100 to-purple-100',
      gradient: 'from-blue-50 via-purple-50 to-pink-50',
    },
    inputConfig: {
      label: 'PSN ID',
      placeholder: 'Enter your PSN ID',
      helpText: 'Your PlayStation Network Online ID',
      validation: /^[a-zA-Z0-9_-]{3,16}$/,
      errorMessage: 'PSN ID must be 3-16 characters (letters, numbers, underscore, hyphen)',
    },
    metrics: {
      primary: 'Trophy Level',
      secondary: 'Platinum Trophies',
      performance: 'Hours Played',
    },
    terminology: {
      player: 'Player',
      match: 'Session',
      character: 'Character',
      performance: 'Score',
    },
  },
};

export const getActivePlatforms = (): Platform[] => {
  // For now, only Riot is active since backend only supports it
  return [PLATFORMS.riot];
};

export const getAllPlatforms = (): Platform[] => {
  return Object.values(PLATFORMS);
};

export const getPlatform = (id: string): Platform | undefined => {
  return PLATFORMS[id];
};
