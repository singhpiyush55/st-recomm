"use client";

import { useEffect, useState, useCallback } from "react";
import RunPipelineButton from "@/components/pipeline/RunPipelineButton";
import RunHistoryList from "@/components/pipeline/RunHistoryList";
import AgentChatPanel from "@/components/pipeline/AgentChatPanel";
import { getPipelineRuns } from "@/lib/api";

export default function PipelinePage() {
  const [runs, setRuns] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);

  const fetchRuns = useCallback(async () => {
    try {
      const data = await getPipelineRuns();
      setRuns(data);
      setError(null);
    } catch (err: any) {
      setError(err.message ?? "Failed to load pipeline runs");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchRuns();
    // Refresh every 5 seconds to catch running pipelines
    const interval = setInterval(fetchRuns, 5000);
    return () => clearInterval(interval);
  }, [fetchRuns]);

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Pipeline</h2>
          <p className="text-sm text-gray-500">
            Trigger new analysis runs and view history
          </p>
        </div>
        <RunPipelineButton onComplete={fetchRuns} />
      </div>

      {loading && runs.length === 0 && (
        <div className="py-12 text-center text-gray-500">Loading runs…</div>
      )}

      {error && (
        <div className="rounded-lg border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-600">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Left: Run history */}
        <div>
          <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-gray-500">
            Run History
          </h3>
          <RunHistoryList
            runs={runs}
            selectedRunId={selectedRunId}
            onSelectRun={setSelectedRunId}
            onRunDeleted={fetchRuns}
          />
        </div>

        {/* Right: Agent chat panel */}
        <div>
          <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-gray-500">
            Agent Chat
          </h3>
          {selectedRunId ? (
            <AgentChatPanel
              key={selectedRunId}
              runId={selectedRunId}
              onClose={() => setSelectedRunId(null)}
            />
          ) : (
            <div className="rounded-xl border border-gray-200 bg-white px-6 py-16 text-center shadow-sm">
              <p className="text-3xl">💬</p>
              <p className="mt-3 text-sm font-medium text-gray-500">
                Select a run to view agent communication
              </p>
              <p className="mt-1 text-xs text-gray-400">
                Click on any run from the history to see what each AI agent sent
                and received during analysis
              </p>
            </div>
          )}
        </div>
      </div>

      {!loading && runs.length === 0 && !error && (
        <div className="rounded-xl border border-gray-200 bg-white px-6 py-12 text-center shadow-sm">
          <p className="text-lg font-medium text-gray-500">
            No runs yet
          </p>
          <p className="mt-1 text-sm text-gray-400">
            Click &quot;Run Pipeline&quot; to start your first analysis.
            Results will appear on the Dashboard and Recommendations pages.
          </p>
        </div>
      )}
    </div>
  );
}
