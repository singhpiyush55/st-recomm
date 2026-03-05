import { Router, Request, Response, NextFunction } from "express";
import { triggerPipeline, getPipelineStatus, listPipelineRuns, getRunAgentOutputs, deletePipelineRun } from "../services/pipeline.service";

const router = Router();

/**
 * POST /api/pipeline/run
 * Triggers a full pipeline run. Accepts optional tickers, sectors, days, top_n.
 */
router.post(
  "/run",
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      const { tickers, sectors, days, top_n } = req.body;
      const runId = await triggerPipeline({ tickers, sectors, days, top_n });
      res.status(201).json({ runId, status: "done" });
    } catch (err) {
      next(err);
    }
  }
);

/**
 * GET /api/pipeline/runs
 * Returns all pipeline runs, newest first.
 */
router.get(
  "/runs",
  async (_req: Request, res: Response, next: NextFunction) => {
    try {
      const runs = await listPipelineRuns();
      res.json(runs);
    } catch (err) {
      next(err);
    }
  }
);

/**
 * GET /api/pipeline/status/:runId
 * Returns the current status of a pipeline run.
 */
router.get(
  "/status/:runId",
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      const result = await getPipelineStatus(req.params.runId);
      if (!result) {
        res.status(404).json({ error: "Pipeline run not found" });
        return;
      }
      res.json(result);
    } catch (err) {
      next(err);
    }
  }
);

/**
 * GET /api/pipeline/runs/:runId/agents
 * Returns all agent LLM outputs for a specific pipeline run, grouped by ticker.
 */
router.get(
  "/runs/:runId/agents",
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      const outputs = await getRunAgentOutputs(req.params.runId);
      res.json(outputs);
    } catch (err) {
      next(err);
    }
  }
);

/**
 * DELETE /api/pipeline/runs/:runId
 * Deletes a pipeline run and all its related data.
 */
router.delete(
  "/runs/:runId",
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      const deleted = await deletePipelineRun(req.params.runId);
      if (!deleted) {
        res.status(404).json({ error: "Pipeline run not found" });
        return;
      }
      res.json({ success: true });
    } catch (err) {
      next(err);
    }
  }
);

export default router;
