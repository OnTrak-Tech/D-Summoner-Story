/**
 * RecapViewer component for displaying the complete year-in-review.
 * Shows AI-generated narrative, statistics, and visualizations.
 */

import React, { useState } from 'react';
import { RecapData } from '../services/api';
import { StatisticsCharts } from './StatisticsCharts';
import { ShareModal } from './ShareModal';

interface RecapViewerProps {
  recapData: RecapData;
  onShare?: () => void;
  onStartNew?: () => void;
}

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: string;
  color?: 'blue' | 'green' | 'purple' | 'yellow' | 'red';
}

const StatCard: React.FC<StatCardProps> = ({ 
  title, 
  value, 
  subtitle, 
  icon, 
  color = 'blue' 
}) => {
  const colorClasses = {
    blue: 'bg-orange-50 border-orange-200 text-orange-800',
    green: 'bg-amber-50 border-amber-200 text-amber-800',
    purple: 'bg-orange-50 border-orange-200 text-orange-800',
    yellow: 'bg-yellow-50 border-yellow-200 text-yellow-800',
    red: 'bg-red-50 border-red-200 text-red-800',
  };

  return (
    <div className={`p-4 rounded-lg border-2 ${colorClasses[color]}`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium opacity-75">{title}</p>
          <p className="text-2xl font-bold">{value}</p>
          {subtitle && (
            <p className="text-xs opacity-60 mt-1">{subtitle}</p>
          )}
        </div>
        {icon && (
          <div className="text-2xl opacity-75">
            {icon}
          </div>
        )}
      </div>
    </div>
  );
};

export const RecapViewer: React.FC<RecapViewerProps> = ({
  recapData,
  onShare,
  onStartNew,
}) => {
  const [activeTab, setActiveTab] = useState<'overview' | 'stats' | 'charts' | 'achievements'>('overview');
  const [showShareModal, setShowShareModal] = useState(false);
  
  const { statistics, narrative, highlights, achievements, fun_facts, recommendations } = recapData;

  const formatKDA = (kda: number): string => {
    return kda.toFixed(2);
  };

  const formatWinRate = (winRate: number): string => {
    return `${winRate.toFixed(1)}%`;
  };

  const getPerformanceColor = (winRate: number): StatCardProps['color'] => {
    if (winRate >= 60) return 'green';
    if (winRate >= 50) return 'blue';
    if (winRate >= 40) return 'yellow';
    return 'red';
  };

  const getKDAColor = (kda: number): StatCardProps['color'] => {
    if (kda >= 2.0) return 'green';
    if (kda >= 1.5) return 'blue';
    if (kda >= 1.0) return 'yellow';
    return 'red';
  };

  return (
    <div className="w-full max-w-4xl mx-auto">
      {/* Header */}
      <div className="bg-gradient-to-r from-orange-600 to-amber-600 text-white rounded-t-lg p-6">
        <div className="text-center">
          <h1 className="text-3xl font-bold mb-2">
            🎮 {recapData.summoner_name}'s Year in Review
          </h1>
          <p className="text-orange-100">
            {recapData.region.toUpperCase()} • {new Date().getFullYear()}
          </p>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="bg-white border-b">
        <nav className="flex">
          {[
            { key: 'overview', label: 'Overview', icon: '📊' },
            { key: 'stats', label: 'Statistics', icon: '📈' },
            { key: 'charts', label: 'Charts', icon: '📊' },
            { key: 'achievements', label: 'Achievements', icon: '🏆' },
          ].map(({ key, label, icon }) => (
            <button
              key={key}
              onClick={() => setActiveTab(key as typeof activeTab)}
              className={`
                flex-1 py-3 px-4 text-center font-medium transition-colors
                ${activeTab === key
                  ? 'text-orange-600 border-b-2 border-orange-600 bg-orange-50'
                  : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                }
              `}
            >
              <span className="mr-2">{icon}</span>
              {label}
            </button>
          ))}
        </nav>
      </div>

      <div className="bg-white rounded-b-lg shadow-lg">
        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="p-6 space-y-6">
            {/* AI Narrative */}
            <div className="bg-gradient-to-r from-orange-50 to-amber-50 rounded-lg p-6 border border-orange-200">
              <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
                <span className="mr-2">🤖</span>
                Your Year in Review
              </h2>
              <div className="prose prose-lg text-gray-700 leading-relaxed">
                {narrative.split('\n').map((paragraph, index) => (
                  paragraph.trim() && (
                    <p key={index} className="mb-3">
                      {paragraph}
                    </p>
                  )
                ))}
              </div>
            </div>

            {/* Key Statistics Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <StatCard
                title="Total Games"
                value={statistics.total_games.toLocaleString()}
                icon="🎮"
                color="blue"
              />
              <StatCard
                title="Win Rate"
                value={formatWinRate(statistics.win_rate)}
                subtitle={`${statistics.total_wins}W / ${statistics.total_losses}L`}
                icon="🏆"
                color={getPerformanceColor(statistics.win_rate)}
              />
              <StatCard
                title="Average KDA"
                value={formatKDA(statistics.avg_kda)}
                subtitle={`${statistics.avg_kills}/${statistics.avg_deaths}/${statistics.avg_assists}`}
                icon="⚔️"
                color={getKDAColor(statistics.avg_kda)}
              />
              <StatCard
                title="Consistency"
                value={`${statistics.consistency_score.toFixed(0)}%`}
                subtitle="Performance stability"
                icon="📊"
                color={statistics.consistency_score >= 75 ? 'green' : 'yellow'}
              />
            </div>

            {/* Highlights */}
            {highlights && highlights.length > 0 && (
              <div>
                <h3 className="text-lg font-bold text-gray-900 mb-3 flex items-center">
                  <span className="mr-2">✨</span>
                  Year Highlights
                </h3>
                <div className="grid gap-3">
                  {highlights.map((highlight, index) => (
                    <div
                      key={index}
                      className="bg-yellow-50 border border-yellow-200 rounded-lg p-4"
                    >
                      <p className="text-gray-800">{highlight}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Charts Tab */}
        {activeTab === 'charts' && (
          <div className="p-6">
            <StatisticsCharts
              visualizations={recapData.visualizations || []}
              statistics={statistics}
            />
          </div>
        )}

        {/* Statistics Tab */}
        {activeTab === 'stats' && (
          <div className="p-6 space-y-6">
            {/* Performance Metrics */}
            <div>
              <h3 className="text-lg font-bold text-gray-900 mb-4">Performance Metrics</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <StatCard
                  title="Games Played"
                  value={statistics.total_games}
                  color="blue"
                />
                <StatCard
                  title="Wins"
                  value={statistics.total_wins}
                  subtitle={formatWinRate(statistics.win_rate)}
                  color="green"
                />
                <StatCard
                  title="Losses"
                  value={statistics.total_losses}
                  color="red"
                />
                <StatCard
                  title="Total Kills"
                  value={(statistics as any).total_kills || 0}
                  subtitle={`${(statistics.avg_kills || 0).toFixed(1)} avg`}
                  color="purple"
                />
                <StatCard
                  title="Total Deaths"
                  value={(statistics as any).total_deaths || 0}
                  subtitle={`${(statistics.avg_deaths || 0).toFixed(1)} avg`}
                  color="red"
                />
                <StatCard
                  title="Total Assists"
                  value={(statistics as any).total_assists || 0}
                  subtitle={`${(statistics.avg_assists || 0).toFixed(1)} avg`}
                  color="blue"
                />
              </div>
            </div>

            {/* Champion Statistics */}
            {statistics.champion_stats && statistics.champion_stats.length > 0 && (
              <div>
                <h3 className="text-lg font-bold text-gray-900 mb-4">Top Champions</h3>
                <div className="space-y-3">
                  {statistics.champion_stats.slice(0, 5).map((champion, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
                    >
                      <div className="flex items-center">
                        <div className="w-8 h-8 bg-blue-500 text-white rounded-full flex items-center justify-center text-sm font-bold mr-3">
                          {index + 1}
                        </div>
                        <div>
                          <p className="font-medium text-gray-900">{champion.champion_name}</p>
                          <p className="text-sm text-gray-500">{champion.games_played} games</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="font-medium text-gray-900">
                          {formatWinRate(champion.win_rate)}
                        </p>
                        <p className="text-sm text-gray-500">win rate</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Monthly Trends */}
            {statistics.monthly_trends && statistics.monthly_trends.length > 0 && (
              <div>
                <h3 className="text-lg font-bold text-gray-900 mb-4">Monthly Performance</h3>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Month
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Games
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Win Rate
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Avg KDA
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {statistics.monthly_trends.map((month, index) => (
                        <tr key={index}>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            {month.month} {month.year}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {(month as any).games || 0}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {formatWinRate(month.win_rate)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {formatKDA(month.avg_kda)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Achievements Tab */}
        {activeTab === 'achievements' && (
          <div className="p-6 space-y-6">
            {/* Achievements */}
            {achievements && achievements.length > 0 && (
              <div>
                <h3 className="text-lg font-bold text-gray-900 mb-4">🏆 Achievements Unlocked</h3>
                <div className="grid gap-3">
                  {achievements.map((achievement, index) => (
                    <div
                      key={index}
                      className="bg-gradient-to-r from-yellow-50 to-orange-50 border border-yellow-200 rounded-lg p-4 flex items-center"
                    >
                      <div className="text-2xl mr-3">🏆</div>
                      <p className="text-gray-800 font-medium">{achievement}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Fun Facts */}
            {fun_facts && fun_facts.length > 0 && (
              <div>
                <h3 className="text-lg font-bold text-gray-900 mb-4">🎉 Fun Facts</h3>
                <div className="grid gap-3">
                  {fun_facts.map((fact, index) => (
                    <div
                      key={index}
                      className="bg-blue-50 border border-blue-200 rounded-lg p-4 flex items-center"
                    >
                      <div className="text-2xl mr-3">💡</div>
                      <p className="text-gray-800">{fact}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Recommendations */}
            {recommendations && recommendations.length > 0 && (
              <div>
                <h3 className="text-lg font-bold text-gray-900 mb-4">🎯 Recommendations for Next Season</h3>
                <div className="grid gap-3">
                  {recommendations.map((recommendation, index) => (
                    <div
                      key={index}
                      className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-center"
                    >
                      <div className="text-2xl mr-3">💪</div>
                      <p className="text-gray-800">{recommendation}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Action Buttons */}
        <div className="p-6 border-t bg-gray-50 rounded-b-lg">
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <button
              onClick={() => setShowShareModal(true)}
              className="px-6 py-3 bg-orange-600 text-white rounded-lg font-medium hover:bg-orange-700 transition-colors flex items-center justify-center"
            >
              <span className="mr-2">📤</span>
              Share My Year in Review
            </button>
            {onStartNew && (
              <button
                onClick={onStartNew}
                className="px-6 py-3 bg-gray-600 text-white rounded-lg font-medium hover:bg-gray-700 transition-colors flex items-center justify-center"
              >
                <span className="mr-2">🔄</span>
                Generate Another
              </button>
            )}
          </div>
        </div>

        {/* Share Modal */}
        <ShareModal
          isOpen={showShareModal}
          onClose={() => setShowShareModal(false)}
          recapData={recapData}
          shareUrl={recapData.share_url}
        />
      </div>
    </div>
  );
};