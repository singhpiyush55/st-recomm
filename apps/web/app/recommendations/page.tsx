import { getRecommendations } from "@/lib/api";
import RecommendationTable from "@/components/recommendation/RecommendationTable";
import Link from "next/link";

export default async function RecommendationsPage() {
  let recs: any[] = [];
  let error: string | null = null;

  try {
    recs = await getRecommendations();
  } catch (e: any) {
    error = e.message;
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">All Recommendations</h2>
        <p className="text-sm text-gray-500">
          Latest pipeline run - Click any row to see full analysis
        </p>
        <Link
          href="/pipeline"
          className="mt-1 inline-block text-xs text-blue-600 hover:text-blue-700"
        >
          View all pipeline runs →
        </Link>
      </div>

      {error ? (
        <p className="py-8 text-center text-sm text-red-400">{error}</p>
      ) : (
        <RecommendationTable data={recs} />
      )}
    </div>
  );
}
