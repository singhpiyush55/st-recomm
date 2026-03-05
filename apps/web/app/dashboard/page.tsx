import { getRecommendations } from "@/lib/api";
import RecommendationCard from "@/components/recommendation/RecommendationCard";
import RunPipelineButton from "@/components/pipeline/RunPipelineButton";
import Card from "@/components/ui/Card";
import Link from "next/link";

export default async function DashboardPage() {
  let recs: any[] = [];
  let error: string | null = null;

  try {
    recs = await getRecommendations();
  } catch (e: any) {
    error = e.message;
  }

  const top3 = recs.slice(0, 3);

  return (
    <div className="space-y-8">
      {/* Header row */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Overview</h2>
          <p className="text-sm text-gray-500">
            Latest AI-powered stock recommendations
          </p>
          <Link
            href="/pipeline"
            className="mt-1 inline-block text-xs text-blue-600 hover:text-blue-700"
          >
            View all pipeline runs →
          </Link>
        </div>
        <RunPipelineButton />
      </div>

      {/* Stats cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Card>
          <p className="text-sm text-gray-500">Total Analysed</p>
          <p className="mt-1 text-3xl font-bold text-gray-900">{recs.length}</p>
        </Card>
        <Card>
          <p className="text-sm text-gray-500">Strong Buys</p>
          <p className="mt-1 text-3xl font-bold text-green-600">
            {recs.filter((r) => r.verdict === "STRONG_BUY").length}
          </p>
        </Card>
        <Card>
          <p className="text-sm text-gray-500">Avg Score</p>
          <p className="mt-1 text-3xl font-bold text-blue-600">
            {recs.length > 0
              ? (recs.reduce((s, r) => s + r.finalScore, 0) / recs.length).toFixed(1)
              : "—"}
          </p>
        </Card>
      </div>

      {/* Top 3 recommendations */}
      {top3.length > 0 ? (
        <div>
          <h3 className="mb-4 text-lg font-semibold text-gray-900">
            Top Picks
          </h3>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            {top3.map((rec) => (
              <RecommendationCard key={rec.id} {...rec} />
            ))}
          </div>
        </div>
      ) : (
        <Card className="text-center">
          <p className="py-8 text-gray-500">
            {error
              ? `Could not load recommendations: ${error}`
              : "No recommendations yet. Click \"Run Pipeline\" to get started."}
          </p>
        </Card>
      )}
    </div>
  );
}
