"use client";

import { useEffect, useState } from "react";
import { getRunAgentOutputs, TickerAgentOutputs } from "@/lib/api";

/** Human-friendly labels for agent stages */
const AGENT_LABELS: Record<string, { label: string; icon: string }> = {
  sector_agent: { label: "Sector Agent", icon: "🏢" },
  screener_agent: { label: "Screener Agent", icon: "🔍" },
  fundamental_agent: { label: "Fundamental Agent", icon: "📊" },
  technical_agent: { label: "Technical Agent", icon: "📈" },
  report_agent: { label: "Report Agent", icon: "📝" },
  prompt_enhancer: { label: "Prompt Enhancer", icon: "✨" },
};

function agentLabel(name: string) {
  return AGENT_LABELS[name] ?? { label: name, icon: "🤖" };
}

/** Collapsible section for showing prompt data sent to the model */
function PromptDetails({ prompt, label }: { prompt: string; label: string }) {
  const [expanded, setExpanded] = useState(false);

  // Count lines for info
  const lineCount = prompt.split("\n").length;
  const preview = prompt.slice(0, 120).replace(/\n/g, " ");

  return (
    <div className="mt-1">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center gap-1.5 text-left text-[11px] text-blue-200 hover:text-white transition-colors"
      >
        <svg
          className={`h-3 w-3 shrink-0 transition-transform ${expanded ? "rotate-90" : ""}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
        <span className="font-medium">
          {expanded ? "Hide" : "Show"} data sent to {label}
        </span>
        <span className="ml-auto text-[10px] text-blue-300">
          {lineCount} lines
        </span>
      </button>

      {!expanded && (
        <p className="mt-1 text-[10px] text-blue-300/70 truncate pl-4">
          {preview}…
        </p>
      )}

      {expanded && (
        <div className="mt-2 rounded-lg bg-blue-700/50 p-3 max-h-[400px] overflow-y-auto">
          <pre className="whitespace-pre-wrap break-words font-mono text-[11px] leading-relaxed text-blue-50">
            {prompt}
          </pre>
        </div>
      )}
    </div>
  );
}

interface AgentChatPanelProps {
  runId: string;
  onClose: () => void;
}

export default function AgentChatPanel({ runId, onClose }: AgentChatPanelProps) {
  const [data, setData] = useState<TickerAgentOutputs[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    getRunAgentOutputs(runId)
      .then((d) => {
        setData(d);
        if (d.length > 0) setSelectedTicker(d[0].ticker);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [runId]);

  const tickerData = data.find((t) => t.ticker === selectedTicker);

  return (
    <div className="rounded-xl border border-gray-200 bg-white shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-gray-200 px-5 py-3">
        <div>
          <h3 className="text-sm font-semibold text-gray-900">
            Agent Communication
          </h3>
          <p className="text-xs text-gray-500">Run: {runId.slice(0, 12)}…</p>
        </div>
        <button
          onClick={onClose}
          className="rounded-lg p-1.5 text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-600"
        >
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Ticker tabs */}
      {data.length > 1 && (
        <div className="flex gap-1 overflow-x-auto border-b border-gray-200 px-4 py-2">
          {data.map((t) => (
            <button
              key={t.ticker}
              onClick={() => setSelectedTicker(t.ticker)}
              className={`shrink-0 rounded-full px-3 py-1 text-xs font-medium transition-colors ${
                selectedTicker === t.ticker
                  ? "bg-blue-100 text-blue-700"
                  : "text-gray-500 hover:bg-gray-100 hover:text-gray-700"
              }`}
            >
              {t.ticker}
            </button>
          ))}
        </div>
      )}

      {/* Chat body */}
      <div className="max-h-[500px] overflow-y-auto p-4">
        {loading && (
          <div className="flex items-center justify-center py-12">
            <svg className="h-6 w-6 animate-spin text-blue-500" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            <span className="ml-2 text-sm text-gray-500">Loading agent outputs…</span>
          </div>
        )}

        {error && (
          <p className="py-8 text-center text-sm text-red-600">{error}</p>
        )}

        {!loading && !error && data.length === 0 && (
          <p className="py-8 text-center text-sm text-gray-500">
            No agent outputs found for this run.
          </p>
        )}

        {tickerData && (
          <div className="space-y-4">
            {tickerData.agents.map((agent, i) => {
              const { label, icon } = agentLabel(agent.agentName);
              return (
                <div key={i} className="space-y-2">
                  {/* Prompt bubble (what we sent to the agent) */}
                  <div className="flex justify-end">
                    <div className="max-w-[85%] rounded-2xl rounded-br-sm bg-blue-600 px-4 py-2.5 text-sm text-white shadow-sm">
                      <p className="mb-1 text-[10px] font-semibold uppercase tracking-wider text-blue-200">
                        Stage {agent.stage} → {label}
                      </p>
                      {agent.response?.prompt ? (
                        <PromptDetails prompt={agent.response.prompt} label={label} />
                      ) : (
                        <p className="text-xs text-blue-100 italic">
                          Analyse {tickerData.ticker}
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Agent response bubble */}
                  <div className="flex justify-start">
                    <div className="max-w-[80%] rounded-2xl rounded-bl-sm border border-gray-200 bg-gray-50 px-4 py-2.5 shadow-sm">
                      <div className="mb-1 flex items-center gap-1.5">
                        <span className="text-sm">{icon}</span>
                        <span className="text-xs font-semibold text-gray-700">
                          {label}
                        </span>
                        {agent.response?.verdict && (
                          <span
                            className={`ml-1 rounded-full px-2 py-0.5 text-[10px] font-semibold ${
                              agent.response.verdict === "STRONG_BUY"
                                ? "bg-green-100 text-green-700"
                                : agent.response.verdict === "MEDIUM_BUY"
                                  ? "bg-yellow-100 text-yellow-700"
                                  : agent.response.verdict === "WEAK_BUY"
                                    ? "bg-orange-100 text-orange-700"
                                    : agent.response.verdict === "AVOID"
                                      ? "bg-red-100 text-red-700"
                                      : "bg-gray-100 text-gray-700"
                            }`}
                          >
                            {agent.response.verdict.replace("_", " ")}
                          </span>
                        )}
                      </div>

                      {agent.response?.narrative ? (
                        <p className="text-sm leading-relaxed text-gray-700">
                          {agent.response.narrative}
                        </p>
                      ) : (
                        <p className="text-sm italic text-gray-400">
                          No narrative returned
                        </p>
                      )}

                      {/* Meta info */}
                      <div className="mt-2 flex gap-3 text-[10px] text-gray-400">
                        <span>{agent.tokensUsed} tokens</span>
                        <span>{agent.latencyMs}ms</span>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
