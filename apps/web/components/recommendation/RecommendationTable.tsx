"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import Badge from "@/components/ui/Badge";
import { formatScore, formatCurrency } from "@/lib/formatters";

interface Recommendation {
  id: string;
  ticker: string;
  finalScore: number;
  verdict: string;
  entryZone: [number, number];
  stopLoss: number;
  target: number;
  rrRatio: number;
  createdAt: string;
}

interface RecommendationTableProps {
  data: Recommendation[];
}

type SortKey = "finalScore" | "ticker" | "rrRatio";

export default function RecommendationTable({ data }: RecommendationTableProps) {
  const router = useRouter();
  const [sortKey, setSortKey] = useState<SortKey>("finalScore");
  const [sortAsc, setSortAsc] = useState(false);

  const sorted = [...data].sort((a, b) => {
    const av = a[sortKey];
    const bv = b[sortKey];
    if (typeof av === "string") return sortAsc ? av.localeCompare(bv as string) : (bv as string).localeCompare(av);
    return sortAsc ? (av as number) - (bv as number) : (bv as number) - (av as number);
  });

  function toggleSort(key: SortKey) {
    if (sortKey === key) setSortAsc(!sortAsc);
    else {
      setSortKey(key);
      setSortAsc(false);
    }
  }

  const thClass =
    "px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 cursor-pointer hover:text-gray-900 select-none";

  return (
    <div className="overflow-x-auto rounded-xl border border-gray-200">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className={thClass} onClick={() => toggleSort("ticker")}>
              Ticker
            </th>
            <th className={thClass} onClick={() => toggleSort("finalScore")}>
              Score
            </th>
            <th className={thClass}>Verdict</th>
            <th className={thClass}>Entry Zone</th>
            <th className={thClass}>Stop Loss</th>
            <th className={thClass}>Target</th>
            <th className={thClass} onClick={() => toggleSort("rrRatio")}>
              R/R
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200 bg-white">
          {sorted.map((rec) => (
            <tr
              key={rec.id}
              className="cursor-pointer transition-colors hover:bg-gray-50"
              onClick={() => router.push(`/recommendations/${rec.id}`)}
            >
              <td className="whitespace-nowrap px-4 py-3 text-sm font-semibold text-gray-900">
                {rec.ticker}
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-700">
                {formatScore(rec.finalScore)}
              </td>
              <td className="whitespace-nowrap px-4 py-3">
                <Badge verdict={rec.verdict} />
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-700">
                {formatCurrency(rec.entryZone[0])} – {formatCurrency(rec.entryZone[1])}
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-sm text-red-600">
                {formatCurrency(rec.stopLoss)}
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-sm text-green-600">
                {formatCurrency(rec.target)}
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-700">
                {rec.rrRatio.toFixed(1)}
              </td>
            </tr>
          ))}
          {sorted.length === 0 && (
            <tr>
              <td
                colSpan={7}
                className="px-4 py-8 text-center text-sm text-gray-500"
              >
                No recommendations yet. Run the pipeline first.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
