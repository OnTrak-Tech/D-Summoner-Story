import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { OnTrakAICoachLanding } from '../components/OnTrakAICoachLanding';
import { PlayerInput } from '../components/PlayerInput';
import { Platform, getActivePlatforms } from '../config/platforms';

export const LandingPage: React.FC = () => {
  const navigate = useNavigate();
  const [showLanding, setShowLanding] = useState(true);
  const [selectedPlatform, setSelectedPlatform] = useState<Platform | null>(null);
  const activePlatforms = getActivePlatforms();

  const handleGetStarted = (platform?: Platform) => {
    setShowLanding(false);
    if (platform) {
      setSelectedPlatform(platform);
    } else if (activePlatforms.length === 1) {
      setSelectedPlatform(activePlatforms[0]);
    }
  };

  const handlePlayerSubmit = (data: { platform: string; playerId: string; region?: string }) => {
    // Navigate to the recap page with parameters
    // Format: /id/:platform/:region/:summonerName
    const region = data.region || 'na1';
    // Using encodeURIComponent to ensure special characters in names don't break the URL
    navigate(
      `/recap/${encodeURIComponent(data.platform)}/${encodeURIComponent(region)}/${encodeURIComponent(data.playerId)}`
    );
  };

  if (showLanding) {
    return <OnTrakAICoachLanding onGetStarted={handleGetStarted} />;
  }

  if (selectedPlatform) {
    return (
      <div className="min-h-screen bg-brand-dark flex items-center justify-center p-4">
        <PlayerInput
          platform={selectedPlatform}
          onSubmit={handlePlayerSubmit}
          isLoading={false} // Loading state will be handled on the next page
          onBack={() => {
            setSelectedPlatform(null);
            setShowLanding(true);
          }}
        />
      </div>
    );
  }

  return null;
};
