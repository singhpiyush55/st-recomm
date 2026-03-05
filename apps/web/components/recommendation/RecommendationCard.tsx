"use client";

import Link from "next/link";
import Badge from "@/components/ui/Badge";
import Card from "@/components/ui/Card";
import { formatScore, formatCurrency } from "@/lib/formatters";

interface RecommendationCardProps {
  id: string;
  ticker: string;
  finalScore: number;
  verdict: string;
  entryZone: [number, number];
  stopLoss: number;
  target: number;
  rrRatio: number;
}

export default function RecommendationCard({
  id,
  ticker,
  finalScore,
  verdict,
  entryZone,
  stopLoss,
  target,
  rrRatio,
}: RecommendationCardProps) {
  return (
    <Link href={`/recommendations/${id}`}>
      <Card className="transition-colors hover:border-gray-300">
        <div className="flex items-center justify-between">
          <span className="text-lg font-bold text-gray-900">{ticker}</span>
          <Badge verdict={verdict} />
        </div>

        <div className="mt-3 text-3xl font-bold text-gray-900">
          {formatScore(finalScore)}
          <span className="ml-1 text-sm font-normal text-gray-500">/ 100</span>
        </div>

        <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
          <div>
            <p className="text-gray-500">Entry Zone</p>
            <p className="font-medium text-gray-700">
              {formatCurrency(entryZone[0])} – {formatCurrency(entryZone[1])}
            </p>
          </div>
          <div>
            <p className="text-gray-500">R/R Ratio</p>
            <p className="font-medium text-gray-700">{rrRatio.toFixed(1)}</p>
          </div>
          <div>
            <p className="text-gray-500">Stop Loss</p>
            <p className="font-medium text-red-600">{formatCurrency(stopLoss)}</p>
          </div>
          <div>
            <p className="text-gray-500">Target</p>
            <p className="font-medium text-green-600">{formatCurrency(target)}</p>
          </div>
        </div>
      </Card>
    </Link>
  );
}
