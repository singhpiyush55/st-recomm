import dotenv from "dotenv";
dotenv.config();

import express from "express";
import cors from "cors";

import { authMiddleware } from "./middleware/auth.middleware";
import { errorHandler } from "./middleware/error.middleware";

import pipelineRoutes from "./routes/pipeline.routes";
import recommendationsRoutes from "./routes/recommendations.routes";
import backtestRoutes from "./routes/backtest.routes";
import sectorsRoutes from "./routes/sectors.routes";

const app = express();
const PORT = parseInt(process.env.PORT ?? "4000", 10);

// ── Global middleware ────────────────────────────────────────────
app.use(cors({ origin: ["http://localhost:3000"], credentials: true }));
app.use(express.json());

// ── Health check (no auth) ───────────────────────────────────────
app.get("/health", (_req, res) => {
  res.json({ status: "ok" });
});

// ── Auth middleware for all /api routes ───────────────────────────
app.use("/api", authMiddleware);

// ── Routes ───────────────────────────────────────────────────────
app.use("/api/pipeline", pipelineRoutes);
app.use("/api/recommendations", recommendationsRoutes);
app.use("/api/backtest", backtestRoutes);
app.use("/api/sectors", sectorsRoutes);

// ── Error handler (must be last) ─────────────────────────────────
app.use(errorHandler);

// ── Start server ─────────────────────────────────────────────────
app.listen(PORT, () => {
  console.log(`[api] Server running on http://localhost:${PORT}`);
});
