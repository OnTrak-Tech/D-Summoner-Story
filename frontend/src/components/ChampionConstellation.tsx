import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';

interface ChampionNode {
  id: string;
  name: string;
  games: number;
  winRate: number;
  kda: number;
  role: string;
  playstyle: string;
  x?: number;
  y?: number;
  fx?: number | null;
  fy?: number | null;
}

interface ChampionConstellationProps {
  championStats: Array<{
    champion_name: string;
    games_played: number;
    win_rate: number;
    avg_kda: number;
  }>;
}

const CHAMPION_ROLES: Record<string, { role: string; playstyle: string; color: string }> = {
  'Jinx': { role: 'ADC', playstyle: 'Marksman', color: '#ff6b6b' },
  'Caitlyn': { role: 'ADC', playstyle: 'Marksman', color: '#ff6b6b' },
  'Vayne': { role: 'ADC', playstyle: 'Marksman', color: '#ff6b6b' },
  'Ezreal': { role: 'ADC', playstyle: 'Marksman', color: '#ff6b6b' },
  'Yasuo': { role: 'Mid', playstyle: 'Assassin', color: '#4ecdc4' },
  'Zed': { role: 'Mid', playstyle: 'Assassin', color: '#4ecdc4' },
  'Ahri': { role: 'Mid', playstyle: 'Mage', color: '#45b7d1' },
  'Lux': { role: 'Mid', playstyle: 'Mage', color: '#45b7d1' },
  'Syndra': { role: 'Mid', playstyle: 'Mage', color: '#45b7d1' },
  'Graves': { role: 'Jungle', playstyle: 'Fighter', color: '#f9ca24' },
  'Lee Sin': { role: 'Jungle', playstyle: 'Fighter', color: '#f9ca24' },
  'Thresh': { role: 'Support', playstyle: 'Support', color: '#6c5ce7' },
  'Leona': { role: 'Support', playstyle: 'Tank', color: '#a29bfe' },
  'Garen': { role: 'Top', playstyle: 'Tank', color: '#a29bfe' },
  'Darius': { role: 'Top', playstyle: 'Fighter', color: '#f9ca24' },
};

export const ChampionConstellation: React.FC<ChampionConstellationProps> = ({ championStats }) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!svgRef.current || !championStats.length) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const width = 800;
    const height = 600;
    const margin = { top: 20, right: 20, bottom: 20, left: 20 };

    // Prepare nodes
    const nodes: ChampionNode[] = championStats.map(stat => ({
      id: stat.champion_name,
      name: stat.champion_name,
      games: stat.games_played,
      winRate: stat.win_rate,
      kda: stat.avg_kda,
      role: CHAMPION_ROLES[stat.champion_name]?.role || 'Unknown',
      playstyle: CHAMPION_ROLES[stat.champion_name]?.playstyle || 'Unknown'
    }));

    // Create links between similar champions
    const links: Array<{ source: string; target: string; strength: number }> = [];
    nodes.forEach((node1, i) => {
      nodes.slice(i + 1).forEach(node2 => {
        if (node1.role === node2.role || node1.playstyle === node2.playstyle) {
          links.push({
            source: node1.id,
            target: node2.id,
            strength: node1.role === node2.role ? 0.8 : 0.4
          });
        }
      });
    });

    // Create force simulation
    const simulation = d3.forceSimulation(nodes)
      .force("link", d3.forceLink(links).id((d: any) => d.id).strength(d => d.strength * 0.3))
      .force("charge", d3.forceManyBody().strength(-300))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide().radius(d => Math.sqrt(d.games) * 3 + 10))
      .force("x", d3.forceX(width / 2).strength(0.1))
      .force("y", d3.forceY(height / 2).strength(0.1));

    // Create gradient definitions
    const defs = svg.append("defs");
    nodes.forEach(node => {
      const gradient = defs.append("radialGradient")
        .attr("id", `gradient-${node.id}`)
        .attr("cx", "30%")
        .attr("cy", "30%");
      
      const color = CHAMPION_ROLES[node.name]?.color || '#64748b';
      gradient.append("stop")
        .attr("offset", "0%")
        .attr("stop-color", color)
        .attr("stop-opacity", 0.9);
      gradient.append("stop")
        .attr("offset", "100%")
        .attr("stop-color", color)
        .attr("stop-opacity", 0.3);
    });

    // Create container group
    const container = svg.append("g");

    // Add constellation lines (links)
    const link = container.append("g")
      .selectAll("line")
      .data(links)
      .enter().append("line")
      .attr("stroke", "#e2e8f0")
      .attr("stroke-opacity", 0.6)
      .attr("stroke-width", d => d.strength * 2);

    // Add champion nodes (stars)
    const node = container.append("g")
      .selectAll("g")
      .data(nodes)
      .enter().append("g")
      .call(d3.drag<SVGGElement, ChampionNode>()
        .on("start", dragstarted)
        .on("drag", dragged)
        .on("end", dragended));

    // Add star shape for each champion
    node.each(function(d) {
      const group = d3.select(this);
      const radius = Math.sqrt(d.games) * 2 + 8;
      const points = 5;
      const outerRadius = radius;
      const innerRadius = radius * 0.4;

      // Create star path
      const starPath = d3.range(points * 2).map(i => {
        const angle = (i * Math.PI) / points - Math.PI / 2;
        const r = i % 2 === 0 ? outerRadius : innerRadius;
        return [Math.cos(angle) * r, Math.sin(angle) * r];
      }).join("L");

      group.append("path")
        .attr("d", `M${starPath}Z`)
        .attr("fill", `url(#gradient-${d.id})`)
        .attr("stroke", CHAMPION_ROLES[d.name]?.color || '#64748b')
        .attr("stroke-width", 2)
        .attr("opacity", Math.min(d.winRate / 100 + 0.3, 1));

      // Add champion name
      group.append("text")
        .attr("text-anchor", "middle")
        .attr("dy", "0.35em")
        .attr("font-size", "10px")
        .attr("font-weight", "bold")
        .attr("fill", "#1e293b")
        .text(d.name.length > 8 ? d.name.substring(0, 6) + "..." : d.name);
    });

    // Add hover effects
    node
      .on("mouseover", function(event, d) {
        d3.select(this).select("path").attr("stroke-width", 4);
        
        if (tooltipRef.current) {
          const tooltip = d3.select(tooltipRef.current);
          tooltip.style("opacity", 1)
            .style("left", (event.pageX + 10) + "px")
            .style("top", (event.pageY - 10) + "px")
            .html(`
              <div class="font-bold text-slate-900">${d.name}</div>
              <div class="text-sm text-slate-600 mt-1">
                <div><span class="font-medium">Role:</span> ${d.role}</div>
                <div><span class="font-medium">Games:</span> ${d.games}</div>
                <div><span class="font-medium">Win Rate:</span> ${d.winRate.toFixed(1)}%</div>
                <div><span class="font-medium">KDA:</span> ${d.kda.toFixed(2)}</div>
                <div><span class="font-medium">Style:</span> ${d.playstyle}</div>
              </div>
            `);
        }
      })
      .on("mouseout", function() {
        d3.select(this).select("path").attr("stroke-width", 2);
        if (tooltipRef.current) {
          d3.select(tooltipRef.current).style("opacity", 0);
        }
      });

    // Update positions on simulation tick
    simulation.on("tick", () => {
      link
        .attr("x1", (d: any) => d.source.x)
        .attr("y1", (d: any) => d.source.y)
        .attr("x2", (d: any) => d.target.x)
        .attr("y2", (d: any) => d.target.y);

      node.attr("transform", d => `translate(${d.x},${d.y})`);
    });

    function dragstarted(event: any, d: ChampionNode) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }

    function dragged(event: any, d: ChampionNode) {
      d.fx = event.x;
      d.fy = event.y;
    }

    function dragended(event: any, d: ChampionNode) {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }

    return () => {
      simulation.stop();
    };
  }, [championStats]);

  return (
    <div className="relative">
      <div className="text-center mb-4">
        <h3 className="text-xl font-bold text-slate-900 mb-2">🌟 Champion Mastery Constellation</h3>
        <p className="text-sm text-slate-600">
          Star size = games played • Brightness = win rate • Lines connect similar champions
        </p>
      </div>
      
      <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-xl p-4 overflow-hidden">
        <svg
          ref={svgRef}
          width="100%"
          height="600"
          viewBox="0 0 800 600"
          className="w-full h-auto"
        />
      </div>

      {/* Tooltip */}
      <div
        ref={tooltipRef}
        className="absolute pointer-events-none bg-white border border-slate-200 rounded-lg p-3 shadow-lg opacity-0 transition-opacity z-10"
        style={{ maxWidth: '200px' }}
      />

      {/* Legend */}
      <div className="mt-4 grid grid-cols-2 md:grid-cols-3 gap-2 text-xs">
        {Object.entries(
          Object.values(CHAMPION_ROLES).reduce((acc, { role, color }) => {
            acc[role] = color;
            return acc;
          }, {} as Record<string, string>)
        ).map(([role, color]) => (
          <div key={role} className="flex items-center gap-2">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: color }}
            />
            <span className="text-slate-600">{role}</span>
          </div>
        ))}
      </div>
    </div>
  );
};