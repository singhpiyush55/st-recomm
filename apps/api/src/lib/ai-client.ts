import axios, { AxiosInstance } from "axios";

const AI_SERVICE_URL =
  process.env.AI_SERVICE_URL ?? "http://localhost:8000";

const client: AxiosInstance = axios.create({
  baseURL: AI_SERVICE_URL,
  timeout: 300_000, // 5 min — pipeline can be slow
  headers: { "Content-Type": "application/json" },
});

export interface PipelineRequestBody {
  tickers?: string[];
  sectors?: string[];
  days?: number;
  top_n?: number;
}

/**
 * Calls the Python AI service POST /pipeline/run endpoint.
 * Returns the raw JSON body from the Python service.
 */
export async function runPipeline(body: PipelineRequestBody): Promise<any> {
  const maxRetries = 2;
  let lastError: Error | null = null;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      const { data } = await client.post("/pipeline/run", body);
      return data;
    } catch (err: any) {
      lastError = err;
      const status = err.response?.status;

      // Don't retry on 4xx client errors
      if (status && status >= 400 && status < 500) {
        throw new Error(
          `AI service returned ${status}: ${err.response?.data?.detail ?? err.message}`
        );
      }

      // Wait before retry (exponential back-off)
      if (attempt < maxRetries) {
        const delay = 1000 * 2 ** attempt;
        console.warn(
          `[ai-client] Attempt ${attempt + 1} failed, retrying in ${delay}ms…`
        );
        await new Promise((r) => setTimeout(r, delay));
      }
    }
  }

  throw new Error(
    `AI service unreachable after ${maxRetries + 1} attempts: ${lastError?.message}`
  );
}

/**
 * Quick health check against the Python service.
 */
export async function checkAIHealth(): Promise<boolean> {
  try {
    const { data } = await client.get("/health");
    return data?.status === "ok";
  } catch {
    return false;
  }
}
