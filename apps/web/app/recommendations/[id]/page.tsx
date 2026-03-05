import { getRecommendationById } from "@/lib/api";
import { notFound } from "next/navigation";
import Badge from "@/components/ui/Badge";
import Card from "@/components/ui/Card";
import RadarScoreChart from "@/components/charts/RadarScoreChart";
import ScoreBreakdownPanel from "@/components/recommendation/ScoreBreakdownPanel";
import { formatCurrency, formatScore, formatDate } from "@/lib/formatters";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default async function RecommendationDetailPage({ params }: PageProps) {
  const { id } = await params;
  let rec: any;

  try {
    rec = await getRecommendationById(id);
  } catch {
    notFound();
  }

  if (!rec) notFound();

  const sb = rec.scoreBreakdown;
  const tech = rec.technicalSignal;
  const fund = rec.fundamentalData;
  const sent = rec.sentimentData;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center gap-4">
        <h2 className="text-3xl font-bold text-gray-900">{rec.ticker}</h2>
        <Badge verdict={rec.verdict} />
        <span className="ml-auto text-sm text-gray-500">
          {formatDate(rec.createdAt)}
        </span>
      </div>

      {/* Summary box */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-5">
        {[
          { label: "Score", value: formatScore(rec.finalScore), color: "text-gray-900" },
          {
            label: "Entry Zone",
            value: `${formatCurrency(rec.entryZone[0])} – ${formatCurrency(rec.entryZone[1])}`,
            color: "text-gray-700",
          },
          { label: "Stop Loss", value: formatCurrency(rec.stopLoss), color: "text-red-600" },
          { label: "Target", value: formatCurrency(rec.target), color: "text-green-600" },
          { label: "R/R Ratio", value: rec.rrRatio.toFixed(1), color: "text-blue-600" },
        ].map((item) => (
          <Card key={item.label}>
            <p className="text-xs text-gray-500">{item.label}</p>
            <p className={`mt-1 text-xl font-bold ${item.color}`}>{item.value}</p>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Radar chart */}
        {sb && (
          <Card title="Score Radar">
            <RadarScoreChart
              techScore={sb.techScore}
              fundScore={sb.fundScore}
              sectorScore={sb.sectorScore}
              sentimentScore={sb.sentimentScore}
              riskPenalty={sb.riskPenalty}
              verdict={rec.verdict}
            />
          </Card>
        )}

        {/* Score breakdown */}
        {sb && <ScoreBreakdownPanel {...sb} />}
      </div>

      {/* Technical signals */}
      {tech && (
        <Card title="Technical Indicators">
          <div className="grid grid-cols-2 gap-x-8 gap-y-2 text-sm sm:grid-cols-4">
            {[
              ["EMA 20", tech.ema20?.toFixed(2)],
              ["EMA 50", tech.ema50?.toFixed(2)],
              ["EMA 200", tech.ema200?.toFixed(2)],
              ["RSI", tech.rsi?.toFixed(1)],
              ["MACD", tech.macdLine?.toFixed(3)],
              ["MACD Signal", tech.macdSignal?.toFixed(3)],
              ["BB Upper", tech.bbUpper?.toFixed(2)],
              ["BB Lower", tech.bbLower?.toFixed(2)],
              ["ATR", tech.atr?.toFixed(2)],
              ["Volume Spike", tech.volumeSpike ? "Yes" : "No"],
              ["OBV Trend", tech.obvTrend],
            ].map(([label, val]) => (
              <div key={label as string} className="flex justify-between border-b border-gray-200 py-1.5">
                <span className="text-gray-500">{label}</span>
                <span className="font-medium text-gray-700">{val ?? "—"}</span>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Fundamental ratios */}
      {fund && (
        <Card title="Fundamental Ratios">
          <div className="grid grid-cols-2 gap-x-8 gap-y-2 text-sm sm:grid-cols-3">
            {[
              ["P/E Ratio", fund.peRatio?.toFixed(2)],
              ["PEG Ratio", fund.pegRatio?.toFixed(2)],
              ["ROE", fund.roe?.toFixed(2)],
              ["ROA", fund.roa?.toFixed(2)],
              ["Debt/Equity", fund.debtToEquity?.toFixed(2)],
              ["Interest Coverage", fund.interestCoverage?.toFixed(2)],
              ["Revenue Growth", fund.revenueGrowth?.toFixed(2)],
              ["EPS Growth", fund.epsGrowth?.toFixed(2)],
              ["Free Cash Flow", fund.freeCashFlow ? `₹${(fund.freeCashFlow / 1e7).toFixed(2)} Cr` : "—"],
            ].map(([label, val]) => (
              <div key={label as string} className="flex justify-between border-b border-gray-200 py-1.5">
                <span className="text-gray-500">{label}</span>
                <span className="font-medium text-gray-700">{val ?? "—"}</span>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Sentiment / Headlines */}
      {sent && (
        <Card title="Sentiment">
          <p className="mb-3 text-sm text-gray-500">
            News Score:{" "}
            <span className="font-semibold text-gray-900">
              {sent.newsScore?.toFixed(2)}
            </span>{" "}
            &middot; Insider: {sent.insiderSignal}
          </p>
          {Array.isArray(sent.headlinesJson) && sent.headlinesJson.length > 0 && (
            <ul className="space-y-1 text-sm">
              {(sent.headlinesJson as string[]).slice(0, 8).map((h: string, i: number) => (
                <li key={i} className="text-gray-500">
                  • {h}
                </li>
              ))}
            </ul>
          )}
        </Card>
      )}

      {/* LLM Outputs */}
      {rec.llmOutputs && rec.llmOutputs.length > 0 && (
        <Card title="Agent Outputs">
          <div className="space-y-4">
            {rec.llmOutputs.map((o: any, i: number) => (
              <div key={i} className="border-b border-gray-200 pb-3 last:border-0">
                <p className="text-xs font-semibold uppercase text-gray-500">
                  Stage {o.stage} — {o.agentName}
                </p>
                {o.response?.narrative && (
                  <p className="mt-1 text-sm leading-relaxed text-gray-700">
                    {o.response.narrative}
                  </p>
                )}
                {o.response?.verdict && (
                  <p className="mt-1 text-xs text-gray-500">
                    Verdict: {o.response.verdict}
                  </p>
                )}
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}
