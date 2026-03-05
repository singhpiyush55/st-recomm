"use client";

import useSWR from "swr";
import { getRecommendations } from "@/lib/api";

/**
 * SWR hook for fetching the latest recommendations.
 * Refreshes every 5 minutes.
 */
export function useRecommendations() {
  const { data, error, isLoading, mutate } = useSWR(
    "recommendations",
    () => getRecommendations(),
    { refreshInterval: 5 * 60 * 1000 }
  );

  return { data: data ?? [], isLoading, error, mutate };
}
