import React from 'react';
import { Link } from 'react-router-dom';
import { Timeframe } from './TimeframeSelector';

interface RecapPreviewProps {
    timeframe: Timeframe;
    stats: {
        games: number;
        winRate: number;
        kda: number;
    } | null;
    loading?: boolean;
}

export const RecapPreview: React.FC<RecapPreviewProps> = ({
    timeframe,
    stats,
    loading,
}) => {
    const timeframeLabels: Record<Timeframe, string> = {
        'all-time': 'All-Time',
        month: 'This Month',
        season: 'Season',
    };

    if (loading) {
        return (
            <div className="p-8 rounded-2xl bg-white/5 border border-white/10 animate-pulse">
                <div className="h-6 w-32 bg-white/10 rounded mb-6" />
                <div className="flex justify-around">
                    <div className="text-center">
                        <div className="h-12 w-20 bg-white/10 rounded mb-2 mx-auto" />
                        <div className="h-4 w-16 bg-white/10 rounded mx-auto" />
                    </div>
                    <div className="text-center">
                        <div className="h-12 w-20 bg-white/10 rounded mb-2 mx-auto" />
                        <div className="h-4 w-16 bg-white/10 rounded mx-auto" />
                    </div>
                    <div className="text-center">
                        <div className="h-12 w-20 bg-white/10 rounded mb-2 mx-auto" />
                        <div className="h-4 w-16 bg-white/10 rounded mx-auto" />
                    </div>
                </div>
            </div>
        );
    }

    if (!stats) {
        return (
            <div className="p-8 rounded-2xl bg-white/5 border border-white/10 text-center">
                <p className="text-gray-400 mb-4">No stats available for this timeframe</p>
                <Link to="/connect" className="text-purple-400 hover:text-purple-300">
                    Connect a platform →
                </Link>
            </div>
        );
    }

    return (
        <div className="p-8 rounded-2xl bg-gradient-to-br from-purple-900/30 to-cyan-900/30 border border-white/10">
            <h3 className="text-lg font-semibold text-gray-300 mb-6">
                {timeframeLabels[timeframe]} Recap
            </h3>

            {/* Stats Grid */}
            <div className="flex justify-around mb-8">
                <div className="text-center">
                    <p className="text-4xl font-bold text-white">{stats.games}</p>
                    <p className="text-sm text-gray-400">games</p>
                </div>
                <div className="text-center">
                    <p className="text-4xl font-bold text-white">{stats.winRate}%</p>
                    <p className="text-sm text-gray-400">win rate</p>
                </div>
                <div className="text-center">
                    <p className="text-4xl font-bold text-white">{stats.kda}</p>
                    <p className="text-sm text-gray-400">KDA</p>
                </div>
            </div>

            {/* Action Button */}
            <Link
                to={`/recap/${timeframe}`}
                className="block w-full py-3 text-center rounded-xl bg-gradient-to-r from-purple-600 to-cyan-600 font-medium text-white hover:opacity-90 transition-opacity"
            >
                View Full Recap →
            </Link>
        </div>
    );
};
