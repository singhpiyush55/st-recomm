import { prisma } from "@repo/db";

/**
 * Returns all recommendations from the latest completed pipeline run,
 * joined with score breakdowns.
 */
export async function getLatestRecommendations() {
  // Find the most recent completed run
  const latestRun = await prisma.pipelineRun.findFirst({
    where: { status: "done" },
    orderBy: { createdAt: "desc" },
    select: { id: true },
  });

  if (!latestRun) return [];

  const recs = await prisma.recommendation.findMany({
    where: { runId: latestRun.id },
    orderBy: { finalScore: "desc" },
    include: {
      scoreBreakdown: true,
    },
  });

  return recs.map((r) => ({
    id: r.id,
    ticker: r.ticker,
    finalScore: r.finalScore,
    verdict: r.verdict,
    entryZone: [r.entryLow, r.entryHigh] as [number, number],
    stopLoss: r.stopLoss,
    target: r.target,
    rrRatio: r.rrRatio,
    createdAt: r.createdAt.toISOString(),
    scoreBreakdown: r.scoreBreakdown
      ? {
          techScore: r.scoreBreakdown.techScore,
          fundScore: r.scoreBreakdown.fundScore,
          sectorScore: r.scoreBreakdown.sectorScore,
          sentimentScore: r.scoreBreakdown.sentimentScore,
          riskPenalty: r.scoreBreakdown.riskPenalty,
          finalScore: r.scoreBreakdown.finalScore,
        }
      : null,
  }));
}

/**
 * Returns one recommendation with full detail:
 * score breakdown, technical signals, fundamental data,
 * sentiment data, and all LLM outputs.
 */
export async function getRecommendationById(id: string) {
  const rec = await prisma.recommendation.findUnique({
    where: { id },
    include: {
      scoreBreakdown: true,
      technicalSignal: true,
      fundamentalData: true,
      sentimentData: true,
      llmOutputs: {
        orderBy: { stage: "asc" },
      },
      run: {
        select: {
          id: true,
          runDate: true,
          status: true,
          sectorsTargeted: true,
        },
      },
    },
  });

  if (!rec) return null;

  return {
    id: rec.id,
    ticker: rec.ticker,
    finalScore: rec.finalScore,
    verdict: rec.verdict,
    entryZone: [rec.entryLow, rec.entryHigh] as [number, number],
    stopLoss: rec.stopLoss,
    target: rec.target,
    rrRatio: rec.rrRatio,
    createdAt: rec.createdAt.toISOString(),
    run: rec.run,
    scoreBreakdown: rec.scoreBreakdown,
    technicalSignal: rec.technicalSignal,
    fundamentalData: rec.fundamentalData,
    sentimentData: rec.sentimentData,
    llmOutputs: rec.llmOutputs.map((o) => ({
      stage: o.stage,
      agentName: o.promptHash,
      response: o.responseJson,
      tokensUsed: o.tokensUsed,
      latencyMs: o.latencyMs,
    })),
  };
}
