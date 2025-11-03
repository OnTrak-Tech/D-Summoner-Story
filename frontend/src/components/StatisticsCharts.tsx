/**
 * StatisticsCharts component using Chart.js for interactive data visualizations.
 * Displays win rate, champion performance, monthly trends, and KDA analysis.
 */

import React, { useRef, useEffect } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  RadialLinearScale,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import {
  Line,
  Bar,
  Doughnut,
  Radar,
} from 'react-chartjs-2';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  RadialLinearScale,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface ChartData {
  chart_type: string;
  data: any;
  options: any;
}

interface StatisticsChartsProps {
  visualizations: ChartData[];
  statistics: {
    total_games: number;
    win_rate: number;
    avg_kda: number;
    total_wins: number;
    total_losses: number;
    champion_stats?: Array<{
      champion_name: string;
      games_played: number;
      win_rate: number;
      avg_kda?: number;
    }>;
    monthly_trends?: Array<{
      month: string;
      year: number;
      win_rate: number;
      avg_kda: number;
      games?: number;
    }>;
  };
}

const defaultChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'bottom' as const,
    },
  },
};

export const StatisticsCharts: React.FC<StatisticsChartsProps> = ({
  visualizations,
  statistics,
}) => {
  // Create charts from statistics if visualizations are not provided
  const createDefaultCharts = (): ChartData[] => {
    const charts: ChartData[] = [];

    // 1. Win Rate Doughnut Chart
    charts.push({
      chart_type: 'doughnut',
      data: {
        labels: ['Wins', 'Losses'],
        datasets: [{
          data: [statistics.total_wins, statistics.total_losses],
          backgroundColor: ['#10B981', '#EF4444'],
          borderWidth: 0,
          hoverBackgroundColor: ['#059669', '#DC2626'],
        }],
      },
      options: {
        ...defaultChartOptions,
        plugins: {
          ...defaultChartOptions.plugins,
          title: {
            display: true,
            text: `Win Rate: ${statistics.win_rate.toFixed(1)}%`,
            font: { size: 16, weight: 'bold' },
          },
        },
      },
    });

    // 2. Monthly Performance Line Chart
    if (statistics.monthly_trends && statistics.monthly_trends.length > 0) {
      const months = statistics.monthly_trends.map(trend => 
        `${trend.month.slice(0, 3)} ${trend.year}`
      );
      const winRates = statistics.monthly_trends.map(trend => trend.win_rate);
      const kdas = statistics.monthly_trends.map(trend => trend.avg_kda);

      charts.push({
        chart_type: 'line',
        data: {
          labels: months,
          datasets: [
            {
              label: 'Win Rate (%)',
              data: winRates,
              borderColor: '#3B82F6',
              backgroundColor: 'rgba(59, 130, 246, 0.1)',
              tension: 0.4,
              fill: true,
              yAxisID: 'y',
            },
            {
              label: 'Average KDA',
              data: kdas,
              borderColor: '#F59E0B',
              backgroundColor: 'rgba(245, 158, 11, 0.1)',
              tension: 0.4,
              fill: false,
              yAxisID: 'y1',
            },
          ],
        },
        options: {
          ...defaultChartOptions,
          interaction: {
            mode: 'index' as const,
            intersect: false,
          },
          scales: {
            y: {
              type: 'linear' as const,
              display: true,
              position: 'left' as const,
              title: {
                display: true,
                text: 'Win Rate (%)',
              },
              min: 0,
              max: 100,
            },
            y1: {
              type: 'linear' as const,
              display: true,
              position: 'right' as const,
              title: {
                display: true,
                text: 'Average KDA',
              },
              grid: {
                drawOnChartArea: false,
              },
              min: 0,
            },
          },
          plugins: {
            ...defaultChartOptions.plugins,
            title: {
              display: true,
              text: 'Performance Trends Over Time',
              font: { size: 16, weight: 'bold' },
            },
          },
        },
      });
    }

    // 3. Champion Performance Bar Chart
    if (statistics.champion_stats && statistics.champion_stats.length > 0) {
      const topChampions = statistics.champion_stats.slice(0, 5);
      const championNames = topChampions.map(champ => champ.champion_name);
      const gamesPlayed = topChampions.map(champ => champ.games_played);
      const winRates = topChampions.map(champ => champ.win_rate);

      charts.push({
        chart_type: 'bar',
        data: {
          labels: championNames,
          datasets: [
            {
              label: 'Games Played',
              data: gamesPlayed,
              backgroundColor: 'rgba(99, 102, 241, 0.8)',
              borderColor: 'rgba(99, 102, 241, 1)',
              borderWidth: 1,
              yAxisID: 'y',
            },
            {
              label: 'Win Rate (%)',
              data: winRates,
              backgroundColor: 'rgba(16, 185, 129, 0.8)',
              borderColor: 'rgba(16, 185, 129, 1)',
              borderWidth: 1,
              yAxisID: 'y1',
            },
          ],
        },
        options: {
          ...defaultChartOptions,
          scales: {
            y: {
              type: 'linear' as const,
              display: true,
              position: 'left' as const,
              title: {
                display: true,
                text: 'Games Played',
              },
              beginAtZero: true,
            },
            y1: {
              type: 'linear' as const,
              display: true,
              position: 'right' as const,
              title: {
                display: true,
                text: 'Win Rate (%)',
              },
              grid: {
                drawOnChartArea: false,
              },
              beginAtZero: true,
              max: 100,
            },
          },
          plugins: {
            ...defaultChartOptions.plugins,
            title: {
              display: true,
              text: 'Top Champions Performance',
              font: { size: 16, weight: 'bold' },
            },
          },
        },
      });
    }

    // 4. Performance Radar Chart
    const performanceMetrics = [
      Math.min((statistics.total_games / 200) * 100, 100), // Games activity
      statistics.win_rate, // Win rate
      Math.min(statistics.avg_kda * 25, 100), // KDA (scaled)
      Math.min((statistics.champion_stats?.length || 0) * 10, 100), // Champion diversity
      75, // Consistency (placeholder)
    ];

    charts.push({
      chart_type: 'radar',
      data: {
        labels: ['Activity', 'Win Rate', 'KDA', 'Diversity', 'Consistency'],
        datasets: [{
          label: 'Performance Profile',
          data: performanceMetrics,
          backgroundColor: 'rgba(139, 92, 246, 0.2)',
          borderColor: 'rgba(139, 92, 246, 1)',
          pointBackgroundColor: 'rgba(139, 92, 246, 1)',
          pointBorderColor: '#fff',
          pointHoverBackgroundColor: '#fff',
          pointHoverBorderColor: 'rgba(139, 92, 246, 1)',
        }],
      },
      options: {
        ...defaultChartOptions,
        scales: {
          r: {
            beginAtZero: true,
            max: 100,
            ticks: {
              stepSize: 20,
            },
          },
        },
        plugins: {
          ...defaultChartOptions.plugins,
          title: {
            display: true,
            text: 'Overall Performance Profile',
            font: { size: 16, weight: 'bold' },
          },
        },
      },
    });

    return charts;
  };

  const charts = visualizations.length > 0 ? visualizations : createDefaultCharts();

  const renderChart = (chart: ChartData, index: number) => {
    const commonProps = {
      data: chart.data,
      options: chart.options,
    };

    switch (chart.chart_type.toLowerCase()) {
      case 'line':
        return <Line key={index} {...commonProps} />;
      case 'bar':
        return <Bar key={index} {...commonProps} />;
      case 'doughnut':
      case 'pie':
        return <Doughnut key={index} {...commonProps} />;
      case 'radar':
        return <Radar key={index} {...commonProps} />;
      default:
        return (
          <div key={index} className="flex items-center justify-center h-64 bg-gray-100 rounded-lg">
            <p className="text-gray-500">Unsupported chart type: {chart.chart_type}</p>
          </div>
        );
    }
  };

  return (
    <div className="space-y-8">
      <div className="text-center">
        <h2 className="text-3xl font-bold text-slate-900 mb-2">
          📊 Performance Analytics
        </h2>
        <p className="text-slate-600 text-lg">
          Interactive visualizations of your League of Legends performance
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {charts.map((chart, index) => (
          <div
            key={index}
            className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 hover:shadow-md transition-shadow"
          >
            <div className="h-80">
              {renderChart(chart, index)}
            </div>
          </div>
        ))}
      </div>

      {/* Chart Legend and Info */}
      <div className="bg-gradient-to-br from-slate-50 to-slate-100 border border-slate-200 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-slate-900 mb-3">
          📈 Chart Information
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-slate-700">
          <div>
            <strong>Win Rate Chart:</strong> Shows your wins vs losses distribution
          </div>
          <div>
            <strong>Performance Trends:</strong> Monthly progression of win rate and KDA
          </div>
          <div>
            <strong>Champion Performance:</strong> Your top champions by games played and win rate
          </div>
          <div>
            <strong>Performance Profile:</strong> Overall skill assessment across different metrics
          </div>
        </div>
      </div>
    </div>
  );
};