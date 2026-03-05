import { Router, Request, Response, NextFunction } from "express";
import { prisma } from "@repo/db";

const router = Router();

/**
 * GET /api/sectors
 * Returns the sector rankings from the most recent pipeline run.
 */
router.get("/", async (_req: Request, res: Response, next: NextFunction) => {
  try {
    // Find the latest completed run
    const latestRun = await prisma.pipelineRun.findFirst({
      where: { status: "done" },
      orderBy: { createdAt: "desc" },
      select: {
        id: true,
        sectorsTargeted: true,
        runDate: true,
        totalStocksAnalyzed: true,
        recommendations: {
          select: {
            ticker: true,
            finalScore: true,
            verdict: true,
          },
          orderBy: { finalScore: "desc" },
        },
      },
    });

    if (!latestRun) {
      res.json({ sectors: [], message: "No completed pipeline runs found" });
      return;
    }

    // Group recommendations by sector (using sectorsTargeted)
    res.json({
      runId: latestRun.id,
      runDate: latestRun.runDate.toISOString(),
      sectorsTargeted: latestRun.sectorsTargeted,
      totalStocksAnalyzed: latestRun.totalStocksAnalyzed,
      recommendations: latestRun.recommendations,
    });
  } catch (err) {
    next(err);
  }
});

export default router;
