const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:4000";
const API_KEY = process.env.NEXT_PUBLIC_API_KEY ?? "";

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      "x-api-key": API_KEY,
      ...(init?.headers ?? {}),
    },
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.error ?? `API error ${res.status}`);
  }

  return res.json();
}

/* ─── Recommendations ─────────────────────────────────────────── */

export function getRecommendations() {
  return apiFetch<any[]>("/api/recommendations");
}

export function getRecommendationsByRunId(runId: string) {
  return apiFetch<any[]>(`/api/recommendations/runs/${runId}`);
}

export function getRecommendationById(id: string) {
  return apiFetch<any>(`/api/recommendations/${id}`);
}

/* ─── Pipeline ────────────────────────────────────────────────── */

export interface TriggerPipelineBody {
  tickers?: string[];
  sectors?: string[];
  days?: number;
  top_n?: number;
}

export function triggerPipeline(body: TriggerPipelineBody = {}) {
  return apiFetch<{ runId: string; status: string }>("/api/pipeline/run", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function getPipelineRuns() {
  return apiFetch<{
    runId: string;
    status: string;
    startedAt: string;
    completedAt?: string;
    sectorsTargeted: string[];
    totalStocksAnalyzed: number;
  }[]>("/api/pipeline/runs");
}

export function getPipelineStatus(runId: string) {
  return apiFetch<{
    runId: string;
    status: string;
    startedAt: string;
    completedAt?: string;
    sectorsTargeted: string[];
    totalStocksAnalyzed: number;
  }>(`/api/pipeline/status/${runId}`);
}

export interface AgentOutput {
  stage: number;
  agentName: string;
  response: { verdict?: string; narrative?: string; prompt?: string };
  tokensUsed: number;
  latencyMs: number;
  createdAt: string;
}

export interface TickerAgentOutputs {
  ticker: string;
  agents: AgentOutput[];
}

export function getRunAgentOutputs(runId: string) {
  return apiFetch<TickerAgentOutputs[]>(`/api/pipeline/runs/${runId}/agents`);
}

export function deletePipelineRun(runId: string) {
  return apiFetch<{ success: boolean }>(`/api/pipeline/runs/${runId}`, {
    method: "DELETE",
  });
}

/* ─── Backtest ────────────────────────────────────────────────── */

export function getBacktestResults() {
  return apiFetch<{
    totalTrades: number;
    winRate: number;
    avgReturn: number;
    expectancy: number;
    hitTargetCount: number;
    hitStopCount: number;
    openCount: number;
  }>("/api/backtest/results");
}

export function runBacktest(startDate?: string, endDate?: string) {
  return apiFetch<{ created: number }>("/api/backtest/run", {
    method: "POST",
    body: JSON.stringify({ startDate, endDate }),
  });
}

/* ─── Sectors ─────────────────────────────────────────────────── */

export function getSectors() {
  return apiFetch<any>("/api/sectors");
}
