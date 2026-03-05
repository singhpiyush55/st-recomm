import { Router, Request, Response, NextFunction } from "express";
import {
  getLatestRecommendations,
  getRecommendationsByRunId,
  getRecommendationById,
} from "../services/recommendation.service";

const router = Router();

/**
 * GET /api/recommendations
 * Returns all recommendations from the latest completed pipeline run.
 */
router.get("/", async (_req: Request, res: Response, next: NextFunction) => {
  try {
    const recs = await getLatestRecommendations();
    res.json(recs);
  } catch (err) {
    next(err);
  }
});

/**
 * GET /api/runs/:runId/recommendations
 * Returns all recommendations for a specific pipeline run.
 */
router.get("/runs/:runId", async (req: Request, res: Response, next: NextFunction) => {
  try {
    const recs = await getRecommendationsByRunId(req.params.runId);
    res.json(recs);
  } catch (err) {
    next(err);
  }
});

/**
 * GET /api/recommendations/:id
 * Returns one recommendation with full detail.
 */
router.get("/:id", async (req: Request, res: Response, next: NextFunction) => {
  try {
    const rec = await getRecommendationById(req.params.id);
    if (!rec) {
      res.status(404).json({ error: "Recommendation not found" });
      return;
    }
    res.json(rec);
  } catch (err) {
    next(err);
  }
});

export default router;
