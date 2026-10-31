import { useState } from "react";
import { Link } from "react-router";
import { trpc } from "@/providers/trpc";
import FractalTree from "@/components/FractalTree";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  Sparkles,
  Zap,
  Trash2,
  Activity,
  GitBranch,
  Layers,
  Brain,
  Network,
  ChevronRight,
  RotateCcw,
  Terminal,
  Clock,
} from "lucide-react";

export default function Home() {
  const [task, setTask] = useState("");
  const [maxDepth, setMaxDepth] = useState(2);
  const [branchingFactor, setBranchingFactor] = useState(3);
  const [enableMeta, setEnableMeta] = useState(true);
  const [isSeeding, setIsSeeding] = useState(false);

  const utils = trpc.useUtils();
  const { data: stats } = trpc.genesis.stats.useQuery();
  const { data: agents } = trpc.agent.tree.useQuery();
  const { data: recentLogs } = trpc.log.list.useQuery({ limit: 5 });

  const seedMutation = trpc.genesis.seed.useMutation({
    onSuccess: () => {
      utils.genesis.stats.invalidate();
      utils.agent.tree.invalidate();
      utils.log.list.invalidate();
      setIsSeeding(false);
    },
    onError: () => setIsSeeding(false),
  });

  const resetMutation = trpc.genesis.reset.useMutation({
    onSuccess: () => {
      utils.genesis.stats.invalidate();
      utils.agent.tree.invalidate();
      utils.log.list.invalidate();
    },
  });

  const handleSeed = () => {
    if (!task.trim()) return;
    setIsSeeding(true);
    seedMutation.mutate({
      task: task.trim(),
      maxDepth,
      branchingFactor,
      enableMeta,
    });
  };

  const handleReset = () => {
    if (confirm("Are you sure? This will destroy all agents and their capabilities.")) {
      resetMutation.mutate();
    }
  };

  // Build tree structure from flat agents list
  const buildAgentTree = () => {
    if (!agents) return [];
    interface AgentWithChildren {
      id: number;
      name: string;
      purpose: string;
      status: string;
      agentType: string;
      parentId: number | null;
      depth: number;
      insight?: string | null;
      code?: string | null;
      avatar?: string | null;
      spawnedCount: number;
      children: AgentWithChildren[];
    }

    const agentMap = new Map<number, AgentWithChildren>();
    agents.forEach((a) => {
      agentMap.set(a.id, { ...a, children: [] });
    });

    const roots: AgentWithChildren[] = [];

    agents.forEach((a) => {
      const node = agentMap.get(a.id);
      if (!node) return;
      if (a.parentId === null || a.parentId === undefined) {
        roots.push(node);
      } else {
        const parent = agentMap.get(a.parentId);
        if (parent) {
          parent.children.push(node);
        } else {
          roots.push(node);
        }
      }
    });

    return roots;
  };

  const agentTree = buildAgentTree();

  const logActionColors: Record<string, string> = {
    spawn: "text-violet-400 bg-violet-400/10",
    build_capability: "text-orange-400 bg-orange-400/10",
    modify_architecture: "text-cyan-400 bg-cyan-400/10",
    self_refactor: "text-fuchsia-400 bg-fuchsia-400/10",
    discover_need: "text-amber-400 bg-amber-400/10",
    merge: "text-emerald-400 bg-emerald-400/10",
    deprecate: "text-red-400 bg-red-400/10",
  };

  return (
    <div className="min-h-screen bg-[#0a0c10]">
      {/* Header */}
      <header className="border-b border-slate-800/60 bg-[#0d0f14]/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-cyan-500/10 flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-cyan-400" />
            </div>
            <div>
              <h1 className="text-sm font-bold text-slate-100 tracking-tight">
                GENESIS ENGINE
              </h1>
              <p className="text-[10px] text-slate-500 tracking-wider">
                SELF-MODIFYING WORKFLOW ORCHESTRATOR
              </p>
            </div>
          </div>
          <nav className="flex items-center gap-2">
            <Link
              to="/logs"
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 rounded-md transition-colors"
            >
              <Terminal className="w-3.5 h-3.5" />
              Logs
            </Link>
          </nav>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6">
        {/* Hero / Seed Section */}
        <section className="mb-8">
          <div className="rounded-xl border border-slate-800/60 bg-[#0f1219] p-6 genesis-glow">
            <div className="flex items-center gap-2 mb-4">
              <Zap className="w-4 h-4 text-cyan-400" />
              <h2 className="text-sm font-semibold text-slate-200">
                Seed a Root Task
              </h2>
            </div>

            <div className="flex gap-3 mb-4">
              <Input
                placeholder="Describe a task... (e.g., 'track my expenses', 'monitor competitor prices')"
                value={task}
                onChange={(e) => setTask(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSeed()}
                className="flex-1 bg-slate-900/60 border-slate-700/50 text-slate-200 placeholder:text-slate-600 text-sm"
              />
              <Button
                onClick={handleSeed}
                disabled={isSeeding || !task.trim()}
                className="bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 hover:border-cyan-500/50"
              >
                {isSeeding ? (
                  <RotateCcw className="w-4 h-4 animate-spin" />
                ) : (
                  <Sparkles className="w-4 h-4" />
                )}
                <span className="ml-2">{isSeeding ? "Spawning..." : "Genesis"}</span>
              </Button>
            </div>

            {/* Quick seeds */}
            <div className="flex flex-wrap gap-2 mb-5">
              {[
                "Track my expenses",
                "Monitor competitor prices",
                "Automate customer outreach",
                "Generate SEO content",
                "Build a code review bot",
              ].map((preset) => (
                <button
                  key={preset}
                  onClick={() => setTask(preset)}
                  className="px-2.5 py-1 text-[11px] text-slate-500 bg-slate-900/40 border border-slate-800 rounded-md hover:text-slate-300 hover:border-slate-600 transition-colors"
                >
                  {preset}
                </button>
              ))}
            </div>

            <Separator className="bg-slate-800/60 mb-4" />

            {/* Parameters */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
              <div>
                <div className="flex justify-between mb-2">
                  <Label className="text-xs text-slate-500">Max Depth</Label>
                  <span className="text-xs text-cyan-400 font-mono">{maxDepth}</span>
                </div>
                <Slider
                  value={[maxDepth]}
                  onValueChange={(v) => setMaxDepth(v[0])}
                  min={1}
                  max={5}
                  step={1}
                  className="w-full"
                />
                <p className="text-[10px] text-slate-600 mt-1">
                  How many levels of recursive agent spawning
                </p>
              </div>
              <div>
                <div className="flex justify-between mb-2">
                  <Label className="text-xs text-slate-500">Branching Factor</Label>
                  <span className="text-xs text-cyan-400 font-mono">{branchingFactor}</span>
                </div>
                <Slider
                  value={[branchingFactor]}
                  onValueChange={(v) => setBranchingFactor(v[0])}
                  min={1}
                  max={6}
                  step={1}
                  className="w-full"
                />
                <p className="text-[10px] text-slate-600 mt-1">
                  Agents spawned per parent
                </p>
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <Label className="text-xs text-slate-500">Meta-Layer</Label>
                  <p className="text-[10px] text-slate-600 mt-1">
                    Spawn self-observing meta-agents
                  </p>
                </div>
                <Switch
                  checked={enableMeta}
                  onCheckedChange={setEnableMeta}
                  className="data-[state=checked]:bg-fuchsia-500"
                />
              </div>
            </div>
          </div>
        </section>

        {/* Stats */}
        {stats && stats.totalAgents > 0 && (
          <section className="mb-6">
            <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3">
              <div className="rounded-lg border border-slate-800/60 bg-[#0f1219] p-3">
                <div className="flex items-center gap-1.5 mb-1.5">
                  <Brain className="w-3 h-3 text-cyan-400" />
                  <span className="text-[10px] text-slate-500 uppercase tracking-wider">Agents</span>
                </div>
                <p className="text-xl font-bold text-slate-100">{stats.totalAgents}</p>
              </div>
              <div className="rounded-lg border border-slate-800/60 bg-[#0f1219] p-3">
                <div className="flex items-center gap-1.5 mb-1.5">
                  <Activity className="w-3 h-3 text-emerald-400" />
                  <span className="text-[10px] text-slate-500 uppercase tracking-wider">Active</span>
                </div>
                <p className="text-xl font-bold text-slate-100">{stats.activeAgents}</p>
              </div>
              <div className="rounded-lg border border-slate-800/60 bg-[#0f1219] p-3">
                <div className="flex items-center gap-1.5 mb-1.5">
                  <GitBranch className="w-3 h-3 text-violet-400" />
                  <span className="text-[10px] text-slate-500 uppercase tracking-wider">Depth</span>
                </div>
                <p className="text-xl font-bold text-slate-100">{stats.maxDepth}</p>
              </div>
              <div className="rounded-lg border border-slate-800/60 bg-[#0f1219] p-3">
                <div className="flex items-center gap-1.5 mb-1.5">
                  <Layers className="w-3 h-3 text-orange-400" />
                  <span className="text-[10px] text-slate-500 uppercase tracking-wider">Capabilities</span>
                </div>
                <p className="text-xl font-bold text-slate-100">{stats.totalCapabilities}</p>
              </div>
              <div className="rounded-lg border border-slate-800/60 bg-[#0f1219] p-3">
                <div className="flex items-center gap-1.5 mb-1.5">
                  <Network className="w-3 h-3 text-fuchsia-400" />
                  <span className="text-[10px] text-slate-500 uppercase tracking-wider">Meta</span>
                </div>
                <p className="text-xl font-bold text-slate-100">{stats.typeBreakdown.meta}</p>
              </div>
              <div className="rounded-lg border border-slate-800/60 bg-[#0f1219] p-3 flex items-center justify-center">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleReset}
                  className="text-red-400/60 hover:text-red-400 hover:bg-red-400/10 text-xs"
                >
                  <Trash2 className="w-3 h-3 mr-1" />
                  Reset
                </Button>
              </div>
            </div>
          </section>
        )}

        {/* Main Content: Tree + Sidebar */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Tree Visualization */}
          <div className="lg:col-span-3">
            <div className="rounded-xl border border-slate-800/60 bg-[#0f1219] p-4 min-h-[400px]">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <Network className="w-4 h-4 text-slate-400" />
                  <h3 className="text-sm font-semibold text-slate-300">
                    Agent Topology
                  </h3>
                </div>
                {stats && stats.totalAgents > 0 && (
                  <Badge variant="outline" className="text-[10px] border-slate-700 text-slate-500">
                    {stats.totalAgents} nodes
                  </Badge>
                )}
              </div>
              <FractalTree agents={agentTree} />
            </div>
          </div>

          {/* Sidebar: Recent Activity */}
          <div className="lg:col-span-1">
            <div className="rounded-xl border border-slate-800/60 bg-[#0f1219] p-4">
              <div className="flex items-center gap-2 mb-4">
                <Clock className="w-4 h-4 text-slate-400" />
                <h3 className="text-sm font-semibold text-slate-300">
                  Recent Activity
                </h3>
              </div>

              {recentLogs && recentLogs.length > 0 ? (
                <div className="space-y-3">
                  {recentLogs.map((log) => (
                    <div
                      key={log.id}
                      className="rounded-lg bg-slate-900/40 border border-slate-800/40 p-3"
                    >
                      <div className="flex items-center gap-2 mb-1.5">
                        <Badge
                          variant="outline"
                          className={`text-[9px] px-1.5 py-0 h-4 border-0 ${
                            logActionColors[log.action] || "text-slate-400 bg-slate-400/10"
                          }`}
                        >
                          {log.action}
                        </Badge>
                        <span className="text-[10px] text-slate-600">
                          {log.agent?.name || "Unknown"}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-400 leading-relaxed">
                        {log.details.slice(0, 80)}
                        {log.details.length > 80 ? "..." : ""}
                      </p>
                    </div>
                  ))}
                  <Link
                    to="/logs"
                    className="flex items-center justify-center gap-1 text-[11px] text-cyan-400 hover:text-cyan-300 pt-2"
                  >
                    View all logs
                    <ChevronRight className="w-3 h-3" />
                  </Link>
                </div>
              ) : (
                <div className="text-center py-8">
                  <Clock className="w-8 h-8 mx-auto text-slate-700 mb-2" />
                  <p className="text-xs text-slate-600">No activity yet</p>
                  <p className="text-[10px] text-slate-700 mt-1">
                    Activity will appear as agents spawn
                  </p>
                </div>
              )}
            </div>

            {/* How it Works */}
            <div className="rounded-xl border border-slate-800/60 bg-[#0f1219] p-4 mt-4">
              <h3 className="text-sm font-semibold text-slate-300 mb-3">
                How It Works
              </h3>
              <div className="space-y-3">
                {[
                  {
                    step: "1",
                    title: "Seed",
                    desc: "You provide a root task like 'track expenses'",
                  },
                  {
                    step: "2",
                    title: "Discover",
                    desc: "Root agent analyzes and discovers needed capabilities",
                  },
                  {
                    step: "3",
                    title: "Spawn",
                    desc: "Worker agents spawn to build each capability",
                  },
                  {
                    step: "4",
                    title: "Recurse",
                    desc: "Workers discover their own needs and spawn deeper",
                  },
                  {
                    step: "5",
                    title: "Observe",
                    desc: "Meta-agents optimize the entire topology",
                  },
                ].map((item) => (
                  <div key={item.step} className="flex gap-3">
                    <div className="flex-shrink-0 w-5 h-5 rounded-full bg-cyan-500/10 flex items-center justify-center">
                      <span className="text-[10px] font-bold text-cyan-400">
                        {item.step}
                      </span>
                    </div>
                    <div>
                      <p className="text-[11px] font-medium text-slate-300">
                        {item.title}
                      </p>
                      <p className="text-[10px] text-slate-500 leading-relaxed">
                        {item.desc}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
