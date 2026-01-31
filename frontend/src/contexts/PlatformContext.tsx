import React, { createContext, useContext, useState, ReactNode } from 'react';
import { Platform, getActivePlatforms } from '../config/platforms';

interface PlatformContextType {
  selectedPlatform: Platform | null;
  setSelectedPlatform: (platform: Platform | null) => void;
  activePlatforms: Platform[];
  isMultiPlatform: boolean;
}

const PlatformContext = createContext<PlatformContextType | undefined>(undefined);

interface PlatformProviderProps {
  children: ReactNode;
}

export const PlatformProvider: React.FC<PlatformProviderProps> = ({ children }) => {
  const [selectedPlatform, setSelectedPlatform] = useState<Platform | null>(null);
  const activePlatforms = getActivePlatforms();
  const isMultiPlatform = activePlatforms.length > 1;

  const value = {
    selectedPlatform,
    setSelectedPlatform,
    activePlatforms,
    isMultiPlatform,
  };

  return <PlatformContext.Provider value={value}>{children}</PlatformContext.Provider>;
};

export const usePlatform = (): PlatformContextType => {
  const context = useContext(PlatformContext);
  if (context === undefined) {
    throw new Error('usePlatform must be used within a PlatformProvider');
  }
  return context;
};
