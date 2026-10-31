import { useParams, Link } from "react-router";
import { trpc } from "@/providers/trpc";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  ArrowLeft,
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
  Clock,
  FileCode,
  Lightbulb,
  ChevronRight,
} from "lucide-react";

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

const statusColors: Record<string, string> = {
  spawning: "text-violet-400 bg-violet-400/10 border-violet-400/30",
  observing: "text-sky-400 bg-sky-400/10 border-sky-400/30",
  analyzing: "text-amber-400 bg-amber-400/10 border-amber-400/30",
  building: "text-orange-400 bg-orange-400/10 border-orange-400/30",
  running: "text-emerald-400 bg-emerald-400/10 border-emerald-400/30",
  completed: "text-teal-400 bg-teal-400/10 border-teal-400/30",
  error: "text-red-400 bg-red-400/10 border-red-400/30",
  idle: "text-slate-400 bg-slate-400/10 border-slate-400/30",
};

const typeLabels: Record<string, string> = {
  root: "ROOT AGENT",
  worker: "WORKER AGENT",
  manager: "MANAGER AGENT",
  meta: "META AGENT",
};

const typeColors: Record<string, string> = {
  root: "text-cyan-400",
  worker: "text-slate-300",
  manager: "text-amber-400",
  meta: "text-fuchsia-400",
};

const logActionColors: Record<string, string> = {
  spawn: "text-violet-400 bg-violet-400/10",
  build_capability: "text-orange-400 bg-orange-400/10",
  modify_architecture: "text-cyan-400 bg-cyan-400/10",
  self_refactor: "text-fuchsia-400 bg-fuchsia-400/10",
  discover_need: "text-amber-400 bg-amber-400/10",
  merge: "text-emerald-400 bg-emerald-400/10",
  deprecate: "text-red-400 bg-red-400/10",
};

function AgentIcon({ name, className }: { name: string; className?: string }) {
  const Icon = iconMap[name] || Sparkles;
  return <Icon className={className} />;
}

export default function AgentDetail() {
  const { id } = useParams<{ id: string }>();
  const agentId = parseInt(id || "0");

  const { data: agent, isLoading } = trpc.agent.byId.useQuery(
    { id: agentId },
    { enabled: agentId > 0 }
  );

  const { data: capabilities } = trpc.capability.byAgent.useQuery(
    { agentId },
    { enabled: agentId > 0 }
  );

  const { data: agentTasks } = trpc.task.byAgent.useQuery(
    { agentId },
    { enabled: agentId > 0 }
  );

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#0a0c10] flex items-center justify-center">
        <div className="animate-pulse text-slate-500 text-sm">Loading agent...</div>
      </div>
    );
  }

  if (!agent) {
    return (
      <div className="min-h-screen bg-[#0a0c10] flex items-center justify-center">
        <div className="text-center">
          <Bot className="w-12 h-12 mx-auto text-slate-700 mb-3" />
          <p className="text-slate-400">Agent not found</p>
          <Link
            to="/"
            className="text-cyan-400 text-sm hover:text-cyan-300 mt-2 inline-block"
          >
            Back to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0a0c10]">
      {/* Header */}
      <header className="border-b border-slate-800/60 bg-[#0d0f14]/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-3 flex items-center gap-3">
          <Link
            to="/"
            className="flex items-center gap-1 text-slate-500 hover:text-slate-300 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div className="w-6 h-6 rounded bg-cyan-500/10 flex items-center justify-center">
            <Sparkles className="w-3 h-3 text-cyan-400" />
          </div>
          <span className="text-xs text-slate-500">Genesis Engine</span>
          <ChevronRight className="w-3 h-3 text-slate-700" />
          <span className="text-xs text-slate-300">Agent {agent.name}</span>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 sm:px-6 py-6">
        {/* Agent Header Card */}
        <div className="rounded-xl border border-slate-800/60 bg-[#0f1219] p-6 mb-6 genesis-glow">
          <div className="flex items-start gap-4">
            <div
              className="flex-shrink-0 w-14 h-14 rounded-xl flex items-center justify-center"
              style={{
                backgroundColor:
                  statusColors[agent.status]?.split(" ")[1]?.replace("bg-", "") || "#1e293b",
              }}
            >
              <AgentIcon
                name={agent.avatar || "bot"}
                className="w-7 h-7 text-slate-200"
              />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-3 mb-1">
                <h1 className="text-lg font-bold text-slate-100">{agent.name}</h1>
                <Badge
                  variant="outline"
                  className={`text-[10px] ${statusColors[agent.status]}`}
                >
                  {agent.status}
                </Badge>
              </div>
              <p className={`text-[11px] font-bold tracking-wider ${typeColors[agent.agentType]}`}>
                {typeLabels[agent.agentType]}
              </p>
              <p className="text-sm text-slate-400 mt-2 leading-relaxed">
                {agent.purpose}
              </p>
              {agent.insight && (
                <div className="mt-3 flex items-start gap-2 p-3 rounded-lg bg-amber-500/5 border border-amber-500/20">
                  <Lightbulb className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
                  <p className="text-xs text-amber-300/80 italic">{agent.insight}</p>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Code */}
            {agent.code && (
              <div className="rounded-xl border border-slate-800/60 bg-[#0f1219] p-4">
                <div className="flex items-center gap-2 mb-3">
                  <FileCode className="w-4 h-4 text-slate-400" />
                  <h3 className="text-sm font-semibold text-slate-300">
                    Generated Code
                  </h3>
                </div>
                <pre className="rounded-lg bg-slate-950 p-4 overflow-x-auto text-xs text-slate-400 leading-relaxed border border-slate-800/60">
                  <code>{agent.code}</code>
                </pre>
              </div>
            )}

            {/* Tasks */}
            <div className="rounded-xl border border-slate-800/60 bg-[#0f1219] p-4">
              <div className="flex items-center gap-2 mb-4">
                <Terminal className="w-4 h-4 text-slate-400" />
                <h3 className="text-sm font-semibold text-slate-300">
                  Tasks ({agentTasks?.length || 0})
                </h3>
              </div>
              {agentTasks && agentTasks.length > 0 ? (
                <div className="space-y-2">
                  {agentTasks.map((task) => (
                    <div
                      key={task.id}
                      className="flex items-center gap-3 p-3 rounded-lg bg-slate-900/40 border border-slate-800/40"
                    >
                      <div
                        className={`w-2 h-2 rounded-full flex-shrink-0 ${
                          task.status === "completed"
                            ? "bg-emerald-400"
                            : task.status === "in_progress"
                            ? "bg-orange-400"
                            : task.status === "failed"
                            ? "bg-red-400"
                            : "bg-slate-600"
                        }`}
                      />
                      <div className="flex-1 min-w-0">
                        <p className="text-xs text-slate-300">{task.description}</p>
                        {task.result && (
                          <p className="text-[10px] text-slate-500 mt-1">{task.result}</p>
                        )}
                      </div>
                      <Badge
                        variant="outline"
                        className="text-[9px] flex-shrink-0 border-slate-700 text-slate-500"
                      >
                        {task.status}
                      </Badge>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-600 text-center py-4">No tasks assigned</p>
              )}
            </div>

            {/* Children */}
            {agent.children && agent.children.length > 0 && (
              <div className="rounded-xl border border-slate-800/60 bg-[#0f1219] p-4">
                <div className="flex items-center gap-2 mb-4">
                  <GitBranch className="w-4 h-4 text-slate-400" />
                  <h3 className="text-sm font-semibold text-slate-300">
                    Spawned Agents ({agent.children.length})
                  </h3>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {agent.children.map((child) => (
                    <Link
                      key={child.id}
                      to={`/agent/${child.id}`}
                      className="flex items-center gap-3 p-3 rounded-lg bg-slate-900/40 border border-slate-800/40 hover:border-slate-600 transition-colors"
                    >
                      <AgentIcon
                        name={child.avatar || "bot"}
                        className="w-4 h-4 text-slate-400"
                      />
                      <div className="flex-1 min-w-0">
                        <p className="text-xs text-slate-300 truncate">{child.name}</p>
                        <p className="text-[10px] text-slate-500 truncate">
                          {child.purpose.slice(0, 40)}...
                        </p>
                      </div>
                      <ChevronRight className="w-3 h-3 text-slate-600" />
                    </Link>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Capabilities */}
            <div className="rounded-xl border border-slate-800/60 bg-[#0f1219] p-4">
              <div className="flex items-center gap-2 mb-4">
                <Zap className="w-4 h-4 text-slate-400" />
                <h3 className="text-sm font-semibold text-slate-300">
                  Capabilities ({capabilities?.length || 0})
                </h3>
              </div>
              {capabilities && capabilities.length > 0 ? (
                <div className="space-y-2">
                  {capabilities.map((cap) => (
                    <div
                      key={cap.id}
                      className="p-3 rounded-lg bg-slate-900/40 border border-slate-800/40"
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <p className="text-xs font-medium text-slate-300">{cap.name}</p>
                        <Badge
                          variant="outline"
                          className="text-[8px] px-1 h-4 border-slate-700 text-slate-500"
                        >
                          {cap.status}
                        </Badge>
                      </div>
                      <p className="text-[10px] text-slate-500">{cap.description}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-600 text-center py-4">
                  No capabilities built yet
                </p>
              )}
            </div>

            {/* Info */}
            <div className="rounded-xl border border-slate-800/60 bg-[#0f1219] p-4">
              <h3 className="text-sm font-semibold text-slate-300 mb-3">
                Agent Info
              </h3>
              <div className="space-y-2">
                <div className="flex justify-between text-xs">
                  <span className="text-slate-500">ID</span>
                  <span className="text-slate-300 font-mono">{agent.id}</span>
                </div>
                <Separator className="bg-slate-800/40" />
                <div className="flex justify-between text-xs">
                  <span className="text-slate-500">Depth</span>
                  <span className="text-slate-300">{agent.depth}</span>
                </div>
                <Separator className="bg-slate-800/40" />
                <div className="flex justify-between text-xs">
                  <span className="text-slate-500">Children</span>
                  <span className="text-slate-300">{agent.spawnedCount}</span>
                </div>
                <Separator className="bg-slate-800/40" />
                <div className="flex justify-between text-xs">
                  <span className="text-slate-500">Created</span>
                  <span className="text-slate-300">
                    {agent.createdAt ? new Date(agent.createdAt).toLocaleString() : "N/A"}
                  </span>
                </div>
                {agent.parentId && (
                  <>
                    <Separator className="bg-slate-800/40" />
                    <div className="flex justify-between text-xs items-center">
                      <span className="text-slate-500">Parent</span>
                      <Link
                        to={`/agent/${agent.parentId}`}
                        className="text-cyan-400 hover:text-cyan-300"
                      >
                        View Parent
                      </Link>
                    </div>
                  </>
                )}
              </div>
            </div>

            {/* Recent Logs */}
            {agent.logs && agent.logs.length > 0 && (
              <div className="rounded-xl border border-slate-800/60 bg-[#0f1219] p-4">
                <div className="flex items-center gap-2 mb-3">
                  <Clock className="w-4 h-4 text-slate-400" />
                  <h3 className="text-sm font-semibold text-slate-300">
                    Recent Logs
                  </h3>
                </div>
                <div className="space-y-2">
                  {agent.logs.slice(0, 5).map((log) => (
                    <div
                      key={log.id}
                      className="p-2 rounded bg-slate-900/40 border border-slate-800/40"
                    >
                      <Badge
                        variant="outline"
                        className={`text-[8px] px-1 h-4 border-0 mb-1 ${
                          logActionColors[log.action] || "text-slate-400 bg-slate-400/10"
                        }`}
                      >
                        {log.action}
                      </Badge>
                      <p className="text-[10px] text-slate-400">
                        {log.details.slice(0, 60)}
                        {log.details.length > 60 ? "..." : ""}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
