import { useMemo, useRef, useEffect, useState } from "react";
import { useNavigate } from "react-router";
import {
  Brain,
  Cpu,
  Network,
  Database,
  Shield,
  Eye,
  Code,
  Box,
  GitBranch,
  Terminal,
  Activity,
  Zap,
  Layers,
  Hexagon,
  Server,
  Cloud,
  Lock,
  Scan,
  Bot,
  Cog,
  Sparkles,
} from "lucide-react";

// ─── Types ───

interface AgentNode {
  id: number;
  name: string;
  purpose: string;
  status: string;
  agentType: string;
  parentId: number | null;
  depth: number;
  children: AgentNode[];
  insight?: string | null;
  code?: string | null;
  avatar?: string | null;
  spawnedCount: number;
}

interface TreeProps {
  agents: AgentNode[];
  onNodeClick?: (agentId: number) => void;
}

// ─── Icon Mapping ───

const iconMap: Record<string, React.ElementType> = {
  brain: Brain,
  cpu: Cpu,
  network: Network,
  database: Database,
  shield: Shield,
  eye: Eye,
  code: Code,
  box: Box,
  "git-branch": GitBranch,
  terminal: Terminal,
  activity: Activity,
  zap: Zap,
  layers: Layers,
  hexagon: Hexagon,
  server: Server,
  cloud: Cloud,
  lock: Lock,
  scan: Scan,
  bot: Bot,
  cog: Cog,
};

function AgentIcon({ name, className }: { name: string; className?: string }) {
  const Icon = iconMap[name] || Sparkles;
  return <Icon className={className} />;
}

// ─── Status Colors ───

const statusColors: Record<string, string> = {
  spawning: "#a78bfa",
  observing: "#38bdf8",
  analyzing: "#fbbf24",
  building: "#fb923c",
  running: "#4ade80",
  completed: "#6ee7b7",
  error: "#f87171",
  idle: "#94a3b8",
};

const statusBg: Record<string, string> = {
  spawning: "bg-violet-500/10",
  observing: "bg-sky-500/10",
  analyzing: "bg-amber-500/10",
  building: "bg-orange-500/10",
  running: "bg-emerald-500/10",
  completed: "bg-teal-500/10",
  error: "bg-red-500/10",
  idle: "bg-slate-500/10",
};

const statusBorder: Record<string, string> = {
  spawning: "border-violet-500/40",
  observing: "border-sky-500/40",
  analyzing: "border-amber-500/40",
  building: "border-orange-500/40",
  running: "border-emerald-500/40",
  completed: "border-teal-500/40",
  error: "border-red-500/40",
  idle: "border-slate-500/40",
};

const typeLabels: Record<string, string> = {
  root: "ROOT",
  worker: "WORKER",
  manager: "MANAGER",
  meta: "META",
};

const typeColors: Record<string, string> = {
  root: "text-cyan-400",
  worker: "text-slate-300",
  manager: "text-amber-400",
  meta: "text-fuchsia-400",
};

// ─── Layout Engine ───

interface LayoutNode {
  agent: AgentNode;
  x: number;
  y: number;
  width: number;
  height: number;
}

function buildLayoutTree(
  agents: AgentNode[],
  canvasWidth: number,
  nodeWidth: number = 220,
  nodeHeight: number = 90,
  levelGap: number = 140
): LayoutNode[] {
  // Build adjacency map
  const childrenMap = new Map<number | null, AgentNode[]>();
  agents.forEach((a) => {
    const key = a.parentId;
    if (!childrenMap.has(key)) childrenMap.set(key, []);
    childrenMap.get(key)!.push(a);
  });

  // Sort children by id
  childrenMap.forEach((list) => list.sort((a, b) => a.id - b.id));

  const layout: LayoutNode[] = [];

  function placeNode(agent: AgentNode, x: number, y: number) {
    layout.push({ agent, x, y, width: nodeWidth, height: nodeHeight });
    const children = childrenMap.get(agent.id) || [];
    if (children.length === 0) return;

    const totalWidth = children.length * nodeWidth + (children.length - 1) * 40;
    let childX = x - totalWidth / 2 + nodeWidth / 2;
    const childY = y + levelGap;

    children.forEach((child) => {
      placeNode(child, childX, childY);
      childX += nodeWidth + 40;
    });
  }

  // Start with root nodes
  const roots = childrenMap.get(null) || [];
  if (roots.length === 0 && agents.length > 0) {
    // Fallback: treat all as roots
    roots.push(...agents.filter((a) => a.depth === 0));
  }

  const totalWidth = roots.length * nodeWidth + (roots.length - 1) * 60;
  let rootX = canvasWidth / 2 - totalWidth / 2 + nodeWidth / 2;
  const rootY = 40;

  roots.forEach((root) => {
    placeNode(root, rootX, rootY);
    rootX += nodeWidth + 60;
  });

  return layout;
}

// ─── Tree Component ───

export default function FractalTree({ agents }: TreeProps) {
  const navigate = useNavigate();
  const containerRef = useRef<HTMLDivElement>(null);
  const [canvasWidth, setCanvasWidth] = useState(1200);

  useEffect(() => {
    function updateWidth() {
      if (containerRef.current) {
        setCanvasWidth(containerRef.current.offsetWidth);
      }
    }
    updateWidth();
    window.addEventListener("resize", updateWidth);
    return () => window.removeEventListener("resize", updateWidth);
  }, []);

  const layout = useMemo(
    () => buildLayoutTree(agents, canvasWidth),
    [agents, canvasWidth]
  );

  // Calculate connections
  const connections = useMemo(() => {
    const agentMap = new Map(layout.map((l) => [l.agent.id, l]));
    const lines: { x1: number; y1: number; x2: number; y2: number }[] = [];

    layout.forEach((node) => {
      if (node.agent.parentId !== null && node.agent.parentId !== undefined) {
        const parent = agentMap.get(node.agent.parentId);
        if (parent) {
          lines.push({
            x1: parent.x + parent.width / 2,
            y1: parent.y + parent.height,
            x2: node.x + node.width / 2,
            y2: node.y,
          });
        }
      }
    });

    return lines;
  }, [layout]);

  // Calculate canvas height
  const canvasHeight = useMemo(() => {
    if (layout.length === 0) return 300;
    const maxY = Math.max(...layout.map((n) => n.y + n.height));
    return maxY + 60;
  }, [layout]);

  const handleNodeClick = (agentId: number) => {
    navigate(`/agent/${agentId}`);
  };

  if (agents.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-500">
        <div className="text-center">
          <Sparkles className="w-12 h-12 mx-auto mb-4 opacity-30" />
          <p className="text-sm">No agents in the topology yet.</p>
          <p className="text-xs mt-1 opacity-60">Seed a task to begin genesis.</p>
        </div>
      </div>
    );
  }

  return (
    <div ref={containerRef} className="w-full overflow-auto">
      <svg
        width={Math.max(canvasWidth, 400)}
        height={canvasHeight}
        className="block mx-auto"
      >
        {/* Connection lines */}
        {connections.map((conn, i) => (
          <line
            key={i}
            x1={conn.x1}
            y1={conn.y1}
            x2={conn.x2}
            y2={conn.y2}
            stroke="hsl(220 15% 22%)"
            strokeWidth={2}
            className="tree-line"
          />
        ))}

        {/* Nodes rendered as foreignObject for HTML content */}
        {layout.map((node) => {
          const color = statusColors[node.agent.status] || "#94a3b8";
          const isAnimating =
            node.agent.status === "running" ||
            node.agent.status === "building" ||
            node.agent.status === "observing";

          return (
            <foreignObject
              key={node.agent.id}
              x={node.x}
              y={node.y}
              width={node.width}
              height={node.height}
            >
              <div
                className={`
                  relative w-full h-full rounded-lg border cursor-pointer
                  transition-all duration-300 hover:scale-105 hover:shadow-lg
                  ${statusBg[node.agent.status]} ${statusBorder[node.agent.status]}
                  ${isAnimating ? `status-${node.agent.status}` : ""}
                `}
                style={{ borderColor: color + "40" }}
                onClick={() => handleNodeClick(node.agent.id)}
              >
                {/* Status dot */}
                <div
                  className="absolute top-2 right-2 w-2 h-2 rounded-full"
                  style={{ backgroundColor: color, boxShadow: `0 0 8px ${color}` }}
                />

                <div className="flex items-start gap-2 p-3 h-full">
                  {/* Icon */}
                  <div
                    className="flex-shrink-0 w-8 h-8 rounded-md flex items-center justify-center"
                    style={{ backgroundColor: color + "15" }}
                  >
                    <div style={{ color }}>
                      <AgentIcon
                        name={node.agent.avatar || "bot"}
                        className="w-4 h-4"
                      />
                    </div>
                  </div>

                  {/* Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5">
                      <span className={`text-[10px] font-bold tracking-wider ${typeColors[node.agent.agentType]}`}>
                        {typeLabels[node.agent.agentType]}
                      </span>
                    </div>
                    <p className="text-xs font-medium text-slate-200 truncate mt-0.5">
                      {node.agent.name}
                    </p>
                    <p className="text-[10px] text-slate-500 truncate mt-0.5">
                      {node.agent.purpose.slice(0, 50)}...
                    </p>
                    {node.agent.spawnedCount > 0 && (
                      <p className="text-[10px] text-slate-600 mt-1">
                        {node.agent.spawnedCount} children
                      </p>
                    )}
                  </div>
                </div>
              </div>
            </foreignObject>
          );
        })}
      </svg>
    </div>
  );
}
