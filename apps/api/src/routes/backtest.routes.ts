import { Router, Request, Response, NextFunction } from "express";
import { getBacktestResults, runBacktest } from "../services/backtest.service";

const router = Router();

/**
 * GET /api/backtest/results
 * Returns backtest summary statistics.
 */
router.get(
  "/results",
  async (_req: Request, res: Response, next: NextFunction) => {
    try {
      const stats = await getBacktestResults();
      res.json(stats);
    } catch (err) {
      next(err);
    }
  }
);

/**
 * POST /api/backtest/run
 * Triggers a backtest simulation from the latest pipeline run.
 */
router.post(
  "/run",
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      const { startDate, endDate } = req.body;
      const result = await runBacktest(startDate, endDate);
      res.status(201).json(result);
    } catch (err) {
      next(err);
    }
  }
);

export default router;
