import { getRecommendationsByRunId, getPipelineStatus } from "@/lib/api";
import RecommendationTable from "@/components/recommendation/RecommendationTable";
import Link from "next/link";

interface PageProps {
  params: Promise<{ runId: string }>;
}

export default async function RunRecommendationsPage({ params }: PageProps) {
  const { runId } = await params;
  
  let recs: any[] = [];
  let runInfo: any = null;
  let error: string | null = null;

  try {
    [recs, runInfo] = await Promise.all([
      getRecommendationsByRunId(runId),
      getPipelineStatus(runId),
    ]);
  } catch (e: any) {
    error = e.message;
  }

  return (
    <div className="space-y-6">
      {/* Back link */}
      <Link
        href="/pipeline"
        className="inline-flex items-center text-sm text-blue-600 hover:text-blue-700"
      >
        ← Back to Pipeline Runs
      </Link>

      <div>
        <h2 className="text-2xl font-bold text-gray-900">All Recommendations</h2>
        <p className="text-sm text-gray-500">
          {runInfo
            ? `Run from ${new Date(runInfo.completedAt).toLocaleString()}`
            : "Click any row to see full analysis"}
        </p>
        {runInfo?.sectorsTargeted?.length > 0 && (
          <p className="mt-1 text-xs text-gray-400">
            Sectors: {runInfo.sectorsTargeted.join(", ")}
          </p>
        )}
      </div>

      {error ? (
        <p className="py-8 text-center text-sm text-red-400">{error}</p>
      ) : (
        <RecommendationTable data={recs} />
      )}
    </div>
  );
}
