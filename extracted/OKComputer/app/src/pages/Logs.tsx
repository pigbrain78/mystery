import { Link } from "react-router";
import { trpc } from "@/providers/trpc";
import { Badge } from "@/components/ui/badge";
import {
  ArrowLeft,
  Terminal,
  Sparkles,
  ChevronRight,
  Clock,
  Filter,
} from "lucide-react";
import { useState } from "react";

const logActionColors: Record<string, string> = {
  spawn: "text-violet-400 bg-violet-400/10",
  build_capability: "text-orange-400 bg-orange-400/10",
  modify_architecture: "text-cyan-400 bg-cyan-400/10",
  self_refactor: "text-fuchsia-400 bg-fuchsia-400/10",
  discover_need: "text-amber-400 bg-amber-400/10",
  merge: "text-emerald-400 bg-emerald-400/10",
  deprecate: "text-red-400 bg-red-400/10",
};

const logActionIcons: Record<string, string> = {
  spawn: "SPAWN",
  build_capability: "BUILD",
  modify_architecture: "MODIFY",
  self_refactor: "REFACTOR",
  discover_need: "DISCOVER",
  merge: "MERGE",
  deprecate: "DEPRECATE",
};

export default function Logs() {
  const [filter, setFilter] = useState<string | null>(null);
  const { data: logs, isLoading } = trpc.log.list.useQuery({ limit: 100 });

  const filteredLogs = logs
    ? filter
      ? logs.filter((l) => l.action === filter)
      : logs
    : [];

  const actions = [
    "spawn",
    "discover_need",
    "build_capability",
    "modify_architecture",
    "self_refactor",
    "merge",
    "deprecate",
  ];

  return (
    <div className="min-h-screen bg-[#0a0c10]">
      {/* Header */}
      <header className="border-b border-slate-800/60 bg-[#0d0f14]/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 py-3 flex items-center gap-3">
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
          <span className="text-xs text-slate-300">Modification Logs</span>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 sm:px-6 py-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-lg font-bold text-slate-100">
              System Logs
            </h1>
            <p className="text-xs text-slate-500 mt-1">
              Complete audit trail of all self-modifications
            </p>
          </div>
          <div className="text-xs text-slate-500">
            {filteredLogs.length} entries
          </div>
        </div>

        {/* Filter Bar */}
        <div className="flex flex-wrap gap-2 mb-6">
          <button
            onClick={() => setFilter(null)}
            className={`px-3 py-1.5 text-[11px] rounded-md border transition-colors ${
              filter === null
                ? "bg-cyan-500/10 border-cyan-500/30 text-cyan-400"
                : "bg-slate-900/40 border-slate-800 text-slate-500 hover:text-slate-300"
            }`}
          >
            <Filter className="w-3 h-3 inline mr-1" />
            All
          </button>
          {actions.map((action) => (
            <button
              key={action}
              onClick={() => setFilter(filter === action ? null : action)}
              className={`px-3 py-1.5 text-[11px] rounded-md border transition-colors ${
                filter === action
                  ? `${logActionColors[action]} border-current`
                  : "bg-slate-900/40 border-slate-800 text-slate-500 hover:text-slate-300"
              }`}
            >
              {logActionIcons[action]}
            </button>
          ))}
        </div>

        {/* Logs List */}
        {isLoading ? (
          <div className="text-center py-12">
            <div className="animate-pulse text-slate-500 text-sm">
              Loading logs...
            </div>
          </div>
        ) : filteredLogs.length > 0 ? (
          <div className="space-y-2">
            {filteredLogs.map((log) => (
              <div
                key={log.id}
                className="rounded-lg border border-slate-800/60 bg-[#0f1219] p-4 hover:border-slate-700 transition-colors"
              >
                <div className="flex items-start gap-3">
                  {/* Action Badge */}
                  <div className="flex-shrink-0">
                    <Badge
                      variant="outline"
                      className={`text-[10px] px-2 py-0.5 h-6 border-0 ${
                        logActionColors[log.action] || "text-slate-400 bg-slate-400/10"
                      }`}
                    >
                      {logActionIcons[log.action] || log.action}
                    </Badge>
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-slate-300 leading-relaxed">
                      {log.details}
                    </p>

                    <div className="flex items-center gap-4 mt-2">
                      {log.agent && (
                        <Link
                          to={`/agent/${log.agent.id}`}
                          className="flex items-center gap-1 text-[11px] text-cyan-400 hover:text-cyan-300 transition-colors"
                        >
                          <Terminal className="w-3 h-3" />
                          {log.agent.name}
                        </Link>
                      )}
                      <span className="flex items-center gap-1 text-[11px] text-slate-600">
                        <Clock className="w-3 h-3" />
                        {log.createdAt
                          ? new Date(log.createdAt).toLocaleString()
                          : "N/A"}
                      </span>
                    </div>

                    {/* Metadata */}
                    {(() => {
                      const meta = log.metadata as Record<string, unknown> | null;
                      if (meta && typeof meta === "object" && Object.keys(meta).length > 0) {
                        return (
                          <div className="mt-2 p-2 rounded bg-slate-950/50 border border-slate-800/40">
                            <pre className="text-[10px] text-slate-500 overflow-x-auto">
                              {JSON.stringify(meta, null, 2)}
                            </pre>
                          </div>
                        );
                      }
                      return null;
                    })()}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-16">
            <Terminal className="w-12 h-12 mx-auto text-slate-800 mb-3" />
            <p className="text-slate-500 text-sm">No logs found</p>
            <p className="text-slate-600 text-xs mt-1">
              {filter
                ? "Try a different filter"
                : "Seed a task to generate activity"}
            </p>
          </div>
        )}
      </main>
    </div>
  );
}
