"use client";

import Card from "@/components/ui/Card";
import { formatScore } from "@/lib/formatters";

interface ScoreBreakdownPanelProps {
  techScore: number;
  fundScore: number;
  sectorScore: number;
  sentimentScore: number;
  riskPenalty: number;
  finalScore: number;
}

const components = [
  { key: "techScore", label: "Technical", weight: "40%", color: "bg-blue-500" },
  { key: "fundScore", label: "Fundamental", weight: "30%", color: "bg-emerald-500" },
  { key: "sectorScore", label: "Sector", weight: "15%", color: "bg-violet-500" },
  { key: "sentimentScore", label: "Sentiment", weight: "10%", color: "bg-yellow-500" },
  { key: "riskPenalty", label: "Risk Penalty", weight: "-5%", color: "bg-red-500" },
] as const;

export default function ScoreBreakdownPanel(props: ScoreBreakdownPanelProps) {
  return (
    <Card title="Score Breakdown">
      <div className="space-y-3">
        {components.map(({ key, label, weight, color }) => {
          const value = props[key];
          const barWidth = key === "riskPenalty" ? value * 10 : value;
          return (
            <div key={key}>
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-500">
                  {label}{" "}
                  <span className="text-gray-400">({weight})</span>
                </span>
                <span className="font-medium text-gray-700">
                  {key === "riskPenalty" ? `-${value.toFixed(1)}` : value.toFixed(1)}
                </span>
              </div>
              <div className="mt-1 h-2 overflow-hidden rounded-full bg-gray-200">
                <div
                  className={`h-full rounded-full ${color}`}
                  style={{ width: `${Math.min(barWidth, 100)}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>

      {/* Final score */}
      <div className="mt-5 border-t border-gray-200 pt-4 text-center">
        <p className="text-sm text-gray-500">Final Score</p>
        <p className="text-4xl font-bold text-gray-900">
          {formatScore(props.finalScore)}
        </p>
      </div>
    </Card>
  );
}
