"use client";

import Badge from "@/components/ui/Badge";
import { formatDate } from "@/lib/formatters";
import Link from "next/link";
import { deletePipelineRun } from "@/lib/api";
import { useState } from "react";

interface PipelineRun {
  runId: string;
  status: string;
  startedAt: string;
  completedAt?: string;
  sectorsTargeted: string[];
  totalStocksAnalyzed: number;
}

interface RunHistoryListProps {
  runs: PipelineRun[];
  selectedRunId?: string | null;
  onSelectRun?: (runId: string) => void;
  onRunDeleted?: () => void;
}

function statusBadgeVerdict(status: string): string {
  switch (status) {
    case "done":
      return "STRONG_BUY";
    case "running":
    case "pending":
      return "MEDIUM_BUY";
    case "failed":
      return "AVOID";
    default:
      return "WEAK_BUY";
  }
}

export default function RunHistoryList({ runs, selectedRunId, onSelectRun, onRunDeleted }: RunHistoryListProps) {
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const handleDelete = async (runId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    
    if (!confirm("Are you sure you want to delete this pipeline run? This cannot be undone.")) {
      return;
    }

    setDeletingId(runId);
    try {
      await deletePipelineRun(runId);
      onRunDeleted?.();
    } catch (error: any) {
      alert(`Failed to delete: ${error.message}`);
    } finally {
      setDeletingId(null);
    }
  };

  if (runs.length === 0) {
    return (
      <p className="py-8 text-center text-sm text-gray-500">
        No pipeline runs yet.
      </p>
    );
  }

  return (
    <div className="space-y-3">
      {runs.map((run) => (
        <div
          key={run.runId}
          className={`flex cursor-pointer items-center justify-between rounded-lg border px-4 py-3 shadow-sm transition-colors ${
            selectedRunId === run.runId
              ? "border-blue-300 bg-blue-50"
              : "border-gray-200 bg-white hover:border-gray-300"
          }`}
        >
          <div
            onClick={() => onSelectRun?.(run.runId)}
            className="flex flex-1 items-center gap-4"
          >
            <Badge verdict={statusBadgeVerdict(run.status)} />
            <div>
              <p className="text-sm font-medium text-gray-800">
                {formatDate(run.startedAt)}
              </p>
              <p className="text-xs text-gray-500">
                {run.sectorsTargeted.length > 0
                  ? run.sectorsTargeted.join(", ")
                  : "All sectors"}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="text-right">
              <p className="text-sm font-medium text-gray-700">
                {run.totalStocksAnalyzed} stocks
              </p>
              <p className="text-xs uppercase text-gray-500">{run.status}</p>
            </div>
            
            <div className="flex gap-2">
              {run.status === "done" && (
                <>
                  <Link
                    href={`/runs/${run.runId}/dashboard`}
                    className="rounded bg-blue-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-blue-700"
                    onClick={(e) => e.stopPropagation()}
                  >
                    Dashboard
                  </Link>
                  <Link
                    href={`/runs/${run.runId}/recommendations`}
                    className="rounded bg-green-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-green-700"
                    onClick={(e) => e.stopPropagation()}
                  >
                    Recommendations
                  </Link>
                </>
              )}
              
              <button
                onClick={(e) => handleDelete(run.runId, e)}
                disabled={deletingId === run.runId}
                className="rounded bg-red-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-red-700 disabled:opacity-50"
                title="Delete this pipeline run"
              >
                {deletingId === run.runId ? "..." : "Delete"}
              </button>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

