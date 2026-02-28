// All shared types for the Stock Recommender system
// Copilot will fill these in — stubs for now
 
export type Verdict = 'STRONG_BUY' | 'MEDIUM_BUY' | 'WEAK_BUY' | 'AVOID';
 
export interface StockRecommendation {
  id: string;
  ticker: string;
  finalScore: number;
  verdict: Verdict;
  entryZone: [number, number];
  stopLoss: number;
  target: number;
  rrRatio: number;
  createdAt: string;
}
 
export interface ScoreBreakdown {
  techScore: number;
  fundScore: number;
  sectorScore: number;
  sentimentScore: number;
  riskPenalty: number;
  finalScore: number;
}
 
export interface PipelineRunStatus {
  runId: string;
  status: 'pending' | 'running' | 'done' | 'failed';
  startedAt: string;
  completedAt?: string;
}
