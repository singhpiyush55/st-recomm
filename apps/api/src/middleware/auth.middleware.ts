import { Request, Response, NextFunction } from "express";

const API_SECRET = process.env.API_SECRET ?? "";

/**
 * Validates x-api-key header against API_SECRET env var.
 * Skip this middleware for /health endpoint.
 */
export function authMiddleware(
  req: Request,
  res: Response,
  next: NextFunction
): void {
  // Skip auth for health check
  if (req.path === "/health") {
    return next();
  }

  const apiKey = req.headers["x-api-key"] as string | undefined;

  if (!apiKey || apiKey !== API_SECRET) {
    res.status(401).json({ error: "Unauthorized — invalid or missing API key" });
    return;
  }

  next();
}
