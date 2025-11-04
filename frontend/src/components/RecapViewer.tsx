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
    blue: 'bg-gradient-to-br from-slate-50 to-slate-100 border-slate-200 text-slate-800',
    green: 'bg-gradient-to-br from-emerald-50 to-emerald-100 border-emerald-200 text-emerald-800',
    purple: 'bg-gradient-to-br from-violet-50 to-violet-100 border-violet-200 text-violet-800',
    yellow: 'bg-gradient-to-br from-amber-50 to-amber-100 border-amber-200 text-amber-800',
    red: 'bg-gradient-to-br from-rose-50 to-rose-100 border-rose-200 text-rose-800',
  };

  return (
    <div className={`p-5 rounded-xl border ${colorClasses[color]} shadow-sm hover:shadow-md transition-shadow`}>
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <p className="text-xs font-semibold uppercase tracking-wide opacity-60 mb-1">{title}</p>
          <p className="text-3xl font-bold mb-1">{value}</p>
          {subtitle && (
            <p className="text-xs opacity-70">{subtitle}</p>
          )}
        </div>
        {icon && (
          <div className="text-3xl opacity-40 ml-3">
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
  const [activeTab, setActiveTab] = useState<'overview' | 'stats' | 'charts' | 'achievements' | 'ai-insights' | 'ask-ai'>('overview');
  const [showShareModal, setShowShareModal] = useState(false);
  const [messages, setMessages] = useState<Array<{type: 'question' | 'answer', text: string}>>([]);
  const [currentQuestion, setCurrentQuestion] = useState('');
  const [isAsking, setIsAsking] = useState(false);
  
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

  const askAI = async (question: string) => {
    if (!question.trim() || isAsking) return;
    
    setIsAsking(true);
    setMessages(prev => [...prev, {type: 'question', text: question}]);
    setCurrentQuestion('');
    
    try {
      const baseURL = import.meta.env?.VITE_API_ENDPOINT || 'https://your-api-gateway-url.execute-api.us-east-1.amazonaws.com';
      const response = await fetch(`${baseURL}/api/v1/recap/${recapData.session_id}/ask`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({question})
      });
      const data = await response.json();
      setMessages(prev => [...prev, {type: 'answer', text: data.answer}]);
    } catch {
      setMessages(prev => [...prev, {type: 'answer', text: 'Sorry, I had trouble answering that. Please try again!'}]);
    }
    setIsAsking(false);
  };

  const suggestedQuestions = [
    "How can I improve my win rate?",
    "What are my biggest strengths?", 
    "Which champions should I focus on?",
    "Am I getting better over time?",
    "What should I work on next season?"
  ];

  return (
    <div className="w-full max-w-5xl mx-auto">
      {/* Header */}
      <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white rounded-t-2xl p-8 shadow-2xl">
        <div className="text-center">
          <div className="inline-block mb-3">
          </div>
          <h1 className="text-4xl font-bold mb-3 tracking-tight">
            {recapData.summoner_name}
          </h1>
          <p className="text-slate-300 text-lg">
            {recapData.region.toUpperCase()} • {new Date().getFullYear()} Year in Review
          </p>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="bg-white border-b border-slate-200">
        <nav className="flex">
          {[
            { key: 'overview', label: 'Overview', icon: '📊' },
            { key: 'stats', label: 'Statistics', icon: '📈' },
            { key: 'charts', label: 'Charts', icon: '📉' },
            { key: 'achievements', label: 'Achievements', icon: '🏆' },
            { key: 'ai-insights', label: 'AI Insights', icon: '🧠' },
            { key: 'ask-ai', label: 'Ask AI', icon: '🤖' },
          ].map(({ key, label, icon }) => (
            <button
              key={key}
              onClick={() => setActiveTab(key as typeof activeTab)}
              className={`
                flex-1 py-4 px-4 text-center font-semibold transition-all text-sm
                ${activeTab === key
                  ? 'text-slate-900 border-b-3 border-slate-900 bg-slate-50'
                  : 'text-slate-400 hover:text-slate-600 hover:bg-slate-50'
                }
              `}
            >
              <span className="mr-1.5 text-base">{icon}</span>
              <span className="hidden sm:inline">{label}</span>
            </button>
          ))}
        </nav>
      </div>

      <div className="bg-white rounded-b-lg shadow-lg">
        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="p-6 space-y-6">
            {/* AI Narrative */}
            <div className="bg-gradient-to-br from-slate-50 to-slate-100 rounded-2xl p-8 border border-slate-200 shadow-sm">
              <div className="flex items-center gap-3 mb-5">
                <div className="w-10 h-10 bg-slate-900 rounded-xl flex items-center justify-center">
                  <span className="text-xl">✨</span>
                </div>
                <h2 className="text-2xl font-bold text-slate-900">
                  Your Story
                </h2>
              </div>
              <div className="prose prose-slate max-w-none">
                {narrative.split('\n').map((paragraph, index) => (
                  paragraph.trim() && (
                    <p key={index} className="text-slate-700 leading-relaxed mb-4 text-base">
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
                <h3 className="text-xl font-bold text-slate-900 mb-4 flex items-center gap-2">
                  <span>🌟</span>
                  <span>Highlights</span>
                </h3>
                <div className="grid gap-3">
                  {highlights.map((highlight, index) => (
                    <div
                      key={index}
                      className="bg-gradient-to-r from-amber-50 to-yellow-50 border border-amber-200 rounded-xl p-5 shadow-sm hover:shadow-md transition-shadow"
                    >
                      <p className="text-slate-800 font-medium">{highlight}</p>
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

        {/* AI Insights Tab */}
        {activeTab === 'ai-insights' && (
          <div className="p-6 space-y-6">
            {/* Personality Profile */}
            {(recapData as any).personality_profile && (
              <div>
                <h3 className="text-2xl font-bold text-slate-900 mb-4 flex items-center gap-2">
                  <span>🧠</span>
                  <span>Your Gaming Personality</span>
                </h3>
                <div className="bg-gradient-to-br from-purple-50 to-indigo-50 border border-purple-200 rounded-2xl p-6 shadow-sm">
                  <div className="text-center mb-4">
                    <h4 className="text-2xl font-bold text-purple-900 mb-2">
                      {(recapData as any).personality_profile.type}
                    </h4>
                    <p className="text-purple-700 text-lg">
                      {(recapData as any).personality_profile.description}
                    </p>
                  </div>
                  <div className="flex flex-wrap justify-center gap-2 mb-4">
                    {(recapData as any).personality_profile.traits?.map((trait: string, index: number) => (
                      <span key={index} className="px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-sm font-medium">
                        {trait}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            )}
            
            {/* Champion Suggestions */}
            {(recapData as any).champion_suggestions && (recapData as any).champion_suggestions.length > 0 && (
              <div>
                <h3 className="text-2xl font-bold text-slate-900 mb-4 flex items-center gap-2">
                  <span>🎯</span>
                  <span>Perfect Champions for You</span>
                </h3>
                <div className="grid gap-4">
                  {(recapData as any).champion_suggestions.map((suggestion: any, index: number) => (
                    <div key={index} className="bg-gradient-to-br from-blue-50 to-cyan-50 border border-blue-200 rounded-xl p-5 shadow-sm">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="text-xl font-bold text-blue-900">{suggestion.champion}</h4>
                        <div className="flex items-center gap-1">
                          <span className="text-sm text-blue-600">Match:</span>
                          <span className="font-bold text-blue-800">{suggestion.confidence}%</span>
                        </div>
                      </div>
                      <p className="text-blue-700">{suggestion.reason}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {/* Next Season Prediction */}
            {(recapData as any).next_season_prediction && (
              <div>
                <h3 className="text-2xl font-bold text-slate-900 mb-4 flex items-center gap-2">
                  <span>🔮</span>
                  <span>Next Season Prediction</span>
                </h3>
                <div className="bg-gradient-to-br from-amber-50 to-yellow-50 border border-amber-200 rounded-2xl p-6 shadow-sm">
                  <div className="text-center mb-4">
                    <div className="text-4xl font-bold text-amber-900 mb-2">
                      {(recapData as any).next_season_prediction.predicted_rank}
                    </div>
                    <p className="text-amber-700 text-lg mb-2">
                      Expected by {(recapData as any).next_season_prediction.timeline}
                    </p>
                    <div className="flex items-center justify-center gap-2">
                      <span className="text-amber-600">Confidence:</span>
                      <span className="font-bold text-amber-800">
                        {(recapData as any).next_season_prediction.confidence}%
                      </span>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <h5 className="font-semibold text-amber-900">Key Factors:</h5>
                    {(recapData as any).next_season_prediction.key_factors?.map((factor: string, index: number) => (
                      <div key={index} className="flex items-center gap-2">
                        <span className="text-amber-500">•</span>
                        <span className="text-amber-700">{factor}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
            
            {/* Rival Analysis */}
            {(recapData as any).rival_analysis && (
              <div>
                <h3 className="text-2xl font-bold text-slate-900 mb-4 flex items-center gap-2">
                  <span>⚔️</span>
                  <span>How You Stack Up</span>
                </h3>
                <div className="bg-gradient-to-br from-green-50 to-emerald-50 border border-green-200 rounded-2xl p-6 shadow-sm">
                  <div className="text-center mb-6">
                    <div className="text-2xl font-bold text-green-900 mb-2">
                      {(recapData as any).rival_analysis.overall_ranking}
                    </div>
                    <p className="text-green-700">
                      Compared to {(recapData as any).rival_analysis.comparison_group}
                    </p>
                  </div>
                  
                  <div className="grid md:grid-cols-2 gap-6">
                    {/* Strengths */}
                    {(recapData as any).rival_analysis.strengths?.length > 0 && (
                      <div>
                        <h5 className="font-semibold text-green-900 mb-3 flex items-center gap-2">
                          <span>💪</span>
                          <span>Your Strengths</span>
                        </h5>
                        <div className="space-y-2">
                          {(recapData as any).rival_analysis.strengths.map((strength: string, index: number) => (
                            <div key={index} className="flex items-center gap-2">
                              <span className="text-green-500">✓</span>
                              <span className="text-green-700 text-sm">{strength}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    {/* Areas for Improvement */}
                    {(recapData as any).rival_analysis.weaknesses?.length > 0 && (
                      <div>
                        <h5 className="font-semibold text-green-900 mb-3 flex items-center gap-2">
                          <span>🎯</span>
                          <span>Growth Areas</span>
                        </h5>
                        <div className="space-y-2">
                          {(recapData as any).rival_analysis.weaknesses.map((weakness: string, index: number) => (
                            <div key={index} className="flex items-center gap-2">
                              <span className="text-orange-500">→</span>
                              <span className="text-green-700 text-sm">{weakness}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
        
        {/* Ask AI Tab */}
        {activeTab === 'ask-ai' && (
          <div className="p-6 space-y-6">
            <div className="text-center mb-6">
              <h2 className="text-2xl font-bold text-slate-900 mb-2">🤖 Ask Your AI Coach</h2>
              <p className="text-slate-600">Get personalized advice based on your performance data</p>
            </div>
            
            {/* Chat Messages */}
            <div className="bg-slate-50 rounded-xl p-4 min-h-[300px] max-h-[400px] overflow-y-auto space-y-3">
              {messages.length === 0 && (
                <div className="text-center text-slate-500 py-8">
                  <p>Ask me anything about your League performance!</p>
                </div>
              )}
              {messages.map((msg, i) => (
                <div key={i} className={`flex ${msg.type === 'question' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[80%] p-3 rounded-lg ${
                    msg.type === 'question' 
                      ? 'bg-slate-900 text-white' 
                      : 'bg-white border border-slate-200 text-slate-800'
                  }`}>
                    {msg.text}
                  </div>
                </div>
              ))}
              {isAsking && (
                <div className="flex justify-start">
                  <div className="bg-white border border-slate-200 p-3 rounded-lg text-slate-600">
                    Thinking...
                  </div>
                </div>
              )}
            </div>
            
            {/* Input */}
            <div className="flex gap-2">
              <input
                type="text"
                value={currentQuestion}
                onChange={(e) => setCurrentQuestion(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && askAI(currentQuestion)}
                placeholder="Ask about your performance..."
                className="flex-1 p-3 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-500"
                disabled={isAsking}
              />
              <button
                onClick={() => askAI(currentQuestion)}
                disabled={isAsking || !currentQuestion.trim()}
                className="px-6 py-3 bg-slate-900 text-white rounded-lg hover:bg-slate-800 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Ask
              </button>
            </div>
            
            {/* Suggested Questions */}
            <div>
              <p className="text-sm text-slate-600 mb-2">Suggested questions:</p>
              <div className="flex flex-wrap gap-2">
                {suggestedQuestions.map((q, i) => (
                  <button
                    key={i}
                    onClick={() => askAI(q)}
                    disabled={isAsking}
                    className="px-3 py-1 text-sm bg-white border border-slate-300 rounded-full hover:bg-slate-50 disabled:opacity-50"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}
        
        {/* Achievements Tab */}
        {activeTab === 'achievements' && (
          <div className="p-6 space-y-6">
            {/* Highlight Matches */}
            {(recapData as any).highlight_matches && (recapData as any).highlight_matches.length > 0 && (
              <div>
                <h3 className="text-xl font-bold text-slate-900 mb-4">✨ Epic Matches</h3>
                <div className="grid gap-3">
                  {(recapData as any).highlight_matches.map((match: any, index: number) => (
                    <div key={index} className="bg-gradient-to-br from-purple-50 to-indigo-50 border border-purple-200 rounded-xl p-5 shadow-sm">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-bold text-slate-900">{match.champion}</p>
                          <p className="text-slate-600">{match.kills}/{match.deaths}/{match.assists} - {match.kda} KDA</p>
                        </div>
                        <div className={`px-3 py-1 rounded-full text-sm font-medium ${match.win ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                          {match.win ? 'Victory' : 'Defeat'}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {/* Champion Improvements */}
            {(recapData as any).champion_improvements && (recapData as any).champion_improvements.length > 0 && (
              <div>
                <h3 className="text-xl font-bold text-slate-900 mb-4">📈 Biggest Improvements</h3>
                <div className="grid gap-3">
                  {(recapData as any).champion_improvements.map((improvement: string, index: number) => (
                    <div key={index} className="bg-gradient-to-br from-green-50 to-emerald-50 border border-green-200 rounded-xl p-5 shadow-sm">
                      <p className="text-slate-800 font-medium">{improvement}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {/* Behavioral Patterns */}
            {(recapData as any).behavioral_patterns && (recapData as any).behavioral_patterns.length > 0 && (
              <div>
                <h3 className="text-xl font-bold text-slate-900 mb-4">🧠 Your Playstyle</h3>
                <div className="grid gap-3">
                  {(recapData as any).behavioral_patterns.map((pattern: string, index: number) => (
                    <div key={index} className="bg-gradient-to-br from-blue-50 to-cyan-50 border border-blue-200 rounded-xl p-5 shadow-sm">
                      <p className="text-slate-800 font-medium">{pattern}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {/* Achievements */}
            {achievements && achievements.length > 0 && (
              <div>
                <h3 className="text-xl font-bold text-slate-900 mb-4">🏆 Achievements Unlocked</h3>
                <div className="grid gap-3">
                  {achievements.map((achievement, index) => (
                    <div
                      key={index}
                      className="bg-gradient-to-br from-amber-50 to-yellow-50 border border-amber-200 rounded-xl p-5 flex items-center shadow-sm hover:shadow-md transition-shadow"
                    >
                      <div className="text-3xl mr-4">🏆</div>
                      <p className="text-slate-800 font-semibold">{achievement}</p>
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
                      className="bg-gradient-to-br from-violet-50 to-purple-50 border border-violet-200 rounded-xl p-5 flex items-center shadow-sm hover:shadow-md transition-shadow"
                    >
                      <div className="text-3xl mr-4">💡</div>
                      <p className="text-slate-800 font-medium">{fact}</p>
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
                      className="bg-gradient-to-br from-emerald-50 to-teal-50 border border-emerald-200 rounded-xl p-5 flex items-center shadow-sm hover:shadow-md transition-shadow"
                    >
                      <div className="text-3xl mr-4">💪</div>
                      <p className="text-slate-800 font-medium">{recommendation}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Action Buttons */}
        <div className="p-6 border-t border-slate-200 bg-slate-50 rounded-b-2xl">
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <button
              onClick={() => setShowShareModal(true)}
              className="px-8 py-4 bg-slate-900 text-white rounded-xl font-semibold hover:bg-slate-800 transition-all shadow-lg hover:shadow-xl flex items-center justify-center gap-2"
            >
              <span className="text-lg">📤</span>
              <span>Share My Recap</span>
            </button>
            {onStartNew && (
              <button
                onClick={onStartNew}
                className="px-8 py-4 bg-white border-2 border-slate-300 text-slate-700 rounded-xl font-semibold hover:bg-slate-50 transition-all flex items-center justify-center gap-2"
              >
                <span className="text-lg">🔍</span>
                <span>Search Summoner</span>
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