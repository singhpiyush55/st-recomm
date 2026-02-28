import { prisma } from "@repo/db";
import { runPipeline, PipelineRequestBody } from "../lib/ai-client";

/**
 * Triggers a full pipeline run:
 * 1. Creates a PipelineRun record (status "pending")
 * 2. Calls the Python AI service
 * 3. Writes all sub-records to the DB
 * 4. Updates PipelineRun status to "done" (or "failed")
 * 5. Returns the run ID
 */
export async function triggerPipeline(
  body: PipelineRequestBody
): Promise<string> {
  // 1. Create PipelineRun
  const run = await prisma.pipelineRun.create({
    data: {
      status: "pending",
      sectorsTargeted: body.sectors ?? [],
    },
  });

  try {
    // Update to running
    await prisma.pipelineRun.update({
      where: { id: run.id },
      data: { status: "running" },
    });

    // 2. Call Python service
    const result = await runPipeline(body);

    // 3. Write each stock result to DB
    const stockResults: any[] = result.results ?? [];

    for (const stock of stockResults) {
      const rec = await prisma.recommendation.create({
        data: {
          runId: run.id,
          ticker: stock.ticker,
          finalScore: stock.score?.final_score ?? 0,
          verdict: stock.score?.verdict ?? "AVOID",
          entryLow: stock.entry_low ?? 0,
          entryHigh: stock.entry_high ?? 0,
          stopLoss: stock.stop_loss ?? 0,
          target: stock.target ?? 0,
          rrRatio: stock.rr_ratio ?? 0,
        },
      });

      // Score breakdown
      if (stock.score) {
        await prisma.scoreBreakdown.create({
          data: {
            recommendationId: rec.id,
            techScore: stock.score.tech_score ?? 0,
            fundScore: stock.score.fund_score ?? 0,
            sectorScore: stock.score.sector_score ?? 0,
            sentimentScore: stock.score.sentiment_score ?? 0,
            riskPenalty: stock.score.risk_penalty ?? 0,
            finalScore: stock.score.final_score ?? 0,
          },
        });
      }

      // Technical signals
      const tech = stock.quant?.technical;
      if (tech) {
        await prisma.technicalSignal.create({
          data: {
            recommendationId: rec.id,
            ticker: stock.ticker,
            date: new Date(),
            ema20: tech.ema_20 ?? 0,
            ema50: tech.ema_50 ?? 0,
            ema200: tech.ema_200 ?? 0,
            macdLine: tech.macd_line ?? 0,
            macdSignal: tech.macd_signal ?? 0,
            macdHistogram: tech.macd_histogram ?? 0,
            rsi: tech.rsi ?? 0,
            bbUpper: tech.bb_upper ?? 0,
            bbLower: tech.bb_lower ?? 0,
            atr: tech.atr ?? 0,
            volumeSpike: tech.volume_spike ?? false,
            obvTrend: tech.obv_trend ?? "flat",
          },
        });
      }

      // Fundamental data
      const fund = stock.quant?.fundamental;
      if (fund) {
        await prisma.fundamentalData.create({
          data: {
            recommendationId: rec.id,
            ticker: stock.ticker,
            peRatio: fund.pe_ratio,
            pegRatio: fund.peg_ratio,
            roe: fund.roe,
            roa: fund.roa,
            debtToEquity: fund.debt_to_equity,
            interestCoverage: fund.interest_coverage,
            revenueGrowth: fund.revenue_growth,
            epsGrowth: fund.eps_growth,
            freeCashFlow: fund.free_cash_flow,
          },
        });
      }

      // Sentiment data
      const sent = stock.quant?.sentiment;
      if (sent) {
        await prisma.sentimentData.create({
          data: {
            recommendationId: rec.id,
            ticker: stock.ticker,
            newsScore: sent.news_score ?? 0,
            insiderSignal: sent.insider_signal ?? "neutral",
            earningsSurprise: sent.earnings_surprise,
            headlinesJson: sent.headlines ?? [],
          },
        });
      }

      // LLM outputs
      const agents: any[] = stock.agent_outputs ?? [];
      for (const agent of agents) {
        await prisma.llmOutput.create({
          data: {
            recommendationId: rec.id,
            stage: agent.stage ?? 0,
            promptHash: agent.agent_name ?? "",
            responseJson: {
              verdict: agent.verdict,
              narrative: agent.narrative,
            },
            tokensUsed: agent.tokens_used ?? 0,
            latencyMs: agent.latency_ms ?? 0,
          },
        });
      }
    }

    // 4. Mark as done
    await prisma.pipelineRun.update({
      where: { id: run.id },
      data: {
        status: "done",
        totalStocksAnalyzed: result.total_stocks_analyzed ?? stockResults.length,
        sectorsTargeted: result.sectors_targeted ?? body.sectors ?? [],
      },
    });

    return run.id;
  } catch (err: any) {
    // Mark as failed
    await prisma.pipelineRun.update({
      where: { id: run.id },
      data: { status: "failed" },
    });
    throw err;
  }
}

/**
 * Get the status of a pipeline run.
 */
export async function getPipelineStatus(runId: string) {
  const run = await prisma.pipelineRun.findUnique({
    where: { id: runId },
    select: {
      id: true,
      status: true,
      runDate: true,
      sectorsTargeted: true,
      totalStocksAnalyzed: true,
      createdAt: true,
    },
  });

  if (!run) return null;

  return {
    runId: run.id,
    status: run.status,
    startedAt: run.createdAt.toISOString(),
    completedAt: run.runDate.toISOString(),
    sectorsTargeted: run.sectorsTargeted,
    totalStocksAnalyzed: run.totalStocksAnalyzed,
  };
}
