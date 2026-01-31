import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Layout } from '../components/layout';
import { useAuth } from '../contexts/AuthContext';

interface PlatformConfig {
    id: string;
    name: string;
    description: string;
    inputLabel: string;
    inputPlaceholder: string;
    color: string;
}

const platforms: PlatformConfig[] = [
    {
        id: 'riot',
        name: 'Riot Games',
        description: 'League of Legends, Valorant, TFT',
        inputLabel: 'Riot ID',
        inputPlaceholder: 'GameName#TAG',
        color: 'from-red-500 to-orange-500',
    },
    {
        id: 'fortnite',
        name: 'Fortnite',
        description: 'Battle Royale stats',
        inputLabel: 'Epic Username',
        inputPlaceholder: 'YourEpicName',
        color: 'from-purple-500 to-blue-500',
    },
];

// Platform logo paths
const getPlatformLogo = (id: string) => {
    switch (id) {
        case 'riot':
            return <img src="/002_RG_2021_FULL_LOCKUP_RED.png" alt="Riot Games" className="h-12 object-contain" />;
        case 'fortnite':
            return <img src="/fortnite-seeklogo.png" alt="Fortnite" className="h-16 object-contain" />;
        default:
            return null;
    }
};

export const Connect: React.FC = () => {
    const [selectedPlatform, setSelectedPlatform] = useState<string | null>(null);
    const [username, setUsername] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [connectedPlatforms, setConnectedPlatforms] = useState<string[]>([]);

    const { getIdToken } = useAuth();
    const navigate = useNavigate();

    const handleConnect = async () => {
        if (!selectedPlatform || !username.trim()) return;

        setLoading(true);
        setError(null);

        try {
            const token = await getIdToken();
            if (!token) throw new Error('Not authenticated');

            const endpoint = selectedPlatform === 'riot' ? 'auth/riot' : 'auth/fortnite';

            const body =
                selectedPlatform === 'riot'
                    ? { summoner_name: username.split('#')[0], tag_line: username.split('#')[1] || 'NA1', region: 'na1' }
                    : { epic_username: username };

            const response = await fetch(
                `${import.meta.env.VITE_API_ENDPOINT}/api/v1/${endpoint}`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        Authorization: `Bearer ${token}`,
                    },
                    body: JSON.stringify(body),
                }
            );

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.message || 'Failed to connect platform');
            }

            setConnectedPlatforms((prev) => [...prev, selectedPlatform]);
            setSelectedPlatform(null);
            setUsername('');
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Connection failed');
        } finally {
            setLoading(false);
        }
    };

    const handleContinue = () => {
        navigate('/dashboard');
    };

    return (
        <Layout showFooter={false}>
            <div className="min-h-[90vh] flex items-center justify-center px-4 py-12">
                <div className="w-full max-w-2xl">
                    {/* Header */}
                    <div className="text-center mb-10">
                        <h1 className="text-3xl font-bold mb-2">Connect Your Platforms</h1>
                        <p className="text-gray-400">
                            Link your gaming accounts to start getting personalized insights
                        </p>
                    </div>

                    {/* Platform Cards */}
                    <div className="grid md:grid-cols-2 gap-6 mb-8">
                        {platforms.map((platform) => {
                            const isConnected = connectedPlatforms.includes(platform.id);
                            const isSelected = selectedPlatform === platform.id;

                            return (
                                <button
                                    key={platform.id}
                                    onClick={() => !isConnected && setSelectedPlatform(platform.id)}
                                    disabled={isConnected}
                                    className={`relative p-6 rounded-2xl border-2 transition-all text-left ${isConnected
                                        ? 'border-green-500 bg-green-500/10'
                                        : isSelected
                                            ? 'border-purple-500 bg-purple-500/10'
                                            : 'border-white/10 bg-white/5 hover:border-white/30'
                                        }`}
                                >
                                    {isConnected && (
                                        <div className="absolute top-3 right-3 text-green-400">✓</div>
                                    )}
                                    <div className="mb-3">{getPlatformLogo(platform.id)}</div>
                                    <h3 className="text-xl font-bold mb-1">{platform.name}</h3>
                                    <p className="text-sm text-gray-400">{platform.description}</p>
                                </button>
                            );
                        })}
                    </div>

                    {/* Input Form */}
                    {selectedPlatform && (
                        <div className="p-6 rounded-2xl bg-white/5 border border-white/10 mb-8">
                            {error && (
                                <div className="mb-4 p-3 rounded-lg bg-red-500/20 border border-red-500/50 text-red-300 text-sm">
                                    {error}
                                </div>
                            )}

                            <label className="block text-sm font-medium text-gray-300 mb-2">
                                {platforms.find((p) => p.id === selectedPlatform)?.inputLabel}
                            </label>
                            <div className="flex space-x-3">
                                <input
                                    type="text"
                                    value={username}
                                    onChange={(e) => setUsername(e.target.value)}
                                    placeholder={platforms.find((p) => p.id === selectedPlatform)?.inputPlaceholder}
                                    className="flex-1 px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-gray-500 focus:outline-none focus:border-purple-500"
                                />
                                <button
                                    onClick={handleConnect}
                                    disabled={loading || !username.trim()}
                                    className="px-6 py-3 rounded-xl bg-gradient-to-r from-purple-600 to-cyan-600 font-medium text-white hover:opacity-90 disabled:opacity-50"
                                >
                                    {loading ? 'Linking...' : 'Link'}
                                </button>
                            </div>
                        </div>
                    )}

                    {/* Continue Button */}
                    {connectedPlatforms.length > 0 && (
                        <div className="text-center">
                            <button
                                onClick={handleContinue}
                                className="px-8 py-4 rounded-xl bg-gradient-to-r from-purple-600 to-cyan-600 font-bold text-lg text-white hover:opacity-90"
                            >
                                Continue to Dashboard →
                            </button>
                            <p className="mt-3 text-sm text-gray-500">
                                You can add more platforms later
                            </p>
                        </div>
                    )}

                    {/* Skip */}
                    {connectedPlatforms.length === 0 && (
                        <p className="text-center text-sm text-gray-500">
                            <button
                                onClick={handleContinue}
                                className="text-purple-400 hover:text-purple-300"
                            >
                                Skip for now
                            </button>
                        </p>
                    )}
                </div>
            </div>
        </Layout>
    );
};
