"use client";

import useSWR from "swr";
import { getPipelineStatus } from "@/lib/api";

/**
 * SWR hook that polls pipeline status every 3 seconds while
 * status is "pending" or "running". Stops polling when "done" or "failed".
 */
export function usePipelineStatus(runId: string | null) {
  const { data, error, isLoading } = useSWR(
    runId ? `pipeline-status-${runId}` : null,
    () => getPipelineStatus(runId!),
    {
      refreshInterval: (latestData) => {
        const status = latestData?.status;
        if (status === "pending" || status === "running") return 3000;
        return 0; // stop polling
      },
    }
  );

  return {
    data,
    isLoading,
    error,
    isDone: data?.status === "done",
    isFailed: data?.status === "failed",
    isRunning: data?.status === "running" || data?.status === "pending",
  };
}
