import React, { useState, useEffect } from 'react';
import { Layout } from '../components/layout';
import { TimeframeSelector, RecapPreview, Timeframe } from '../components/recap';
import { ChatBox } from '../components/ai';
import { useAuth } from '../contexts/AuthContext';

interface RecapStats {
    games: number;
    winRate: number;
    kda: number;
}

export const Dashboard: React.FC = () => {
    const [timeframe, setTimeframe] = useState<Timeframe>('all-time');
    const [stats, setStats] = useState<RecapStats | null>(null);
    const [loading, setLoading] = useState(true);
    const { user, getIdToken } = useAuth();

    useEffect(() => {
        const fetchStats = async () => {
            setLoading(true);
            try {
                const token = await getIdToken();

                // Fetch stats based on timeframe
                const response = await fetch(
                    `${import.meta.env.VITE_API_ENDPOINT}/api/v1/stats?timeframe=${timeframe}`,
                    {
                        headers: {
                            ...(token && { Authorization: `Bearer ${token}` }),
                        },
                    }
                );

                if (response.ok) {
                    const data = await response.json();
                    setStats({
                        games: data.total_games || 0,
                        winRate: data.win_rate || 0,
                        kda: data.kda || 0,
                    });
                } else {
                    // Demo data for now
                    setStats({
                        games: 234,
                        winRate: 57,
                        kda: 2.3,
                    });
                }
            } catch {
                // Demo data fallback
                setStats({
                    games: 234,
                    winRate: 57,
                    kda: 2.3,
                });
            } finally {
                setLoading(false);
            }
        };

        fetchStats();
    }, [timeframe, getIdToken]);

    return (
        <Layout>
            <div className="max-w-4xl mx-auto px-4 py-12">
                {/* Welcome Header */}
                <div className="mb-8">
                    <h1 className="text-3xl font-bold mb-2">
                        Welcome back{user?.email ? `, ${user.email.split('@')[0]}` : ''}! 👋
                    </h1>
                    <p className="text-gray-400">
                        Here's your gaming summary. Select a timeframe to explore.
                    </p>
                </div>

                {/* Timeframe Selector */}
                <div className="mb-8">
                    <TimeframeSelector selected={timeframe} onChange={setTimeframe} />
                </div>

                {/* Recap Preview */}
                <div className="mb-8">
                    <RecapPreview timeframe={timeframe} stats={stats} loading={loading} />
                </div>

                {/* Quick Stats Grid */}
                <div className="grid md:grid-cols-2 gap-6">
                    {/* Connected Platforms */}
                    <div className="p-6 rounded-2xl bg-white/5 border border-white/10">
                        <h3 className="font-semibold text-gray-300 mb-4">Connected Platforms</h3>
                        <div className="space-y-3">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center space-x-3">
                                    <span className="text-2xl">🎮</span>
                                    <span>Riot Games</span>
                                </div>
                                <span className="text-green-400 text-sm">Connected</span>
                            </div>
                            <div className="flex items-center justify-between">
                                <div className="flex items-center space-x-3">
                                    <span className="text-2xl">🏆</span>
                                    <span>Fortnite</span>
                                </div>
                                <span className="text-gray-500 text-sm">Not connected</span>
                            </div>
                        </div>
                    </div>

                    {/* AI Coach Teaser */}
                    <div className="p-6 rounded-2xl bg-gradient-to-br from-purple-900/30 to-cyan-900/30 border border-white/10">
                        <h3 className="font-semibold text-gray-300 mb-4">🤖 AI Coach Insight</h3>
                        <p className="text-gray-400 mb-4">
                            "Your win rate is 15% higher on weekends. Consider playing more during peak hours!"
                        </p>
                        <p className="text-xs text-purple-400">
                            Click the chat bubble to ask more questions →
                        </p>
                    </div>
                </div>
            </div>

            {/* AI ChatBox */}
            <ChatBox />
        </Layout>
    );
};
