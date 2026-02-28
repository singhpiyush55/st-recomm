import { prisma } from "@repo/db";

export interface BacktestStats {
  totalTrades: number;
  winRate: number;
  avgReturn: number;
  expectancy: number;
  hitTargetCount: number;
  hitStopCount: number;
  openCount: number;
}

/**
 * Queries BacktestResult table and computes summary statistics:
 * win rate, average return, expectancy.
 */
export async function getBacktestResults(): Promise<BacktestStats> {
  const results = await prisma.backtestResult.findMany({
    orderBy: { signalDate: "desc" },
  });

  const total = results.length;
  if (total === 0) {
    return {
      totalTrades: 0,
      winRate: 0,
      avgReturn: 0,
      expectancy: 0,
      hitTargetCount: 0,
      hitStopCount: 0,
      openCount: 0,
    };
  }

  const closed = results.filter((r) => r.exitPrice !== null);
  const hitTarget = results.filter((r) => r.hitTarget).length;
  const hitStop = results.filter((r) => r.hitStop).length;
  const openCount = results.filter(
    (r) => !r.hitTarget && !r.hitStop && r.exitPrice === null
  ).length;

  const returns = closed
    .map((r) => r.returnPct ?? 0)
    .filter((v) => v !== 0);

  const avgReturn =
    returns.length > 0
      ? returns.reduce((a, b) => a + b, 0) / returns.length
      : 0;

  const winRate = closed.length > 0 ? hitTarget / closed.length : 0;

  // Expectancy = (winRate * avgWin) - ((1 - winRate) * avgLoss)
  const wins = returns.filter((r) => r > 0);
  const losses = returns.filter((r) => r < 0);
  const avgWin =
    wins.length > 0 ? wins.reduce((a, b) => a + b, 0) / wins.length : 0;
  const avgLoss =
    losses.length > 0
      ? Math.abs(losses.reduce((a, b) => a + b, 0) / losses.length)
      : 0;
  const expectancy = winRate * avgWin - (1 - winRate) * avgLoss;

  return {
    totalTrades: total,
    winRate: Math.round(winRate * 10000) / 100, // e.g. 65.43
    avgReturn: Math.round(avgReturn * 100) / 100,
    expectancy: Math.round(expectancy * 100) / 100,
    hitTargetCount: hitTarget,
    hitStopCount: hitStop,
    openCount,
  };
}

/**
 * Creates backtest records from the latest pipeline run recommendations.
 * This is a simplified simulation — records entry prices and marks them open.
 */
export async function runBacktest(
  startDate?: string,
  endDate?: string
): Promise<{ created: number }> {
  const latestRun = await prisma.pipelineRun.findFirst({
    where: { status: "done" },
    orderBy: { createdAt: "desc" },
    include: {
      recommendations: true,
    },
  });

  if (!latestRun || latestRun.recommendations.length === 0) {
    return { created: 0 };
  }

  let created = 0;
  for (const rec of latestRun.recommendations) {
    // Avoid duplicate entries
    const existing = await prisma.backtestResult.findFirst({
      where: {
        ticker: rec.ticker,
        signalDate: latestRun.runDate,
      },
    });

    if (existing) continue;

    await prisma.backtestResult.create({
      data: {
        ticker: rec.ticker,
        signalDate: latestRun.runDate,
        entryPrice: (rec.entryLow + rec.entryHigh) / 2,
      },
    });
    created++;
  }

  return { created };
}
