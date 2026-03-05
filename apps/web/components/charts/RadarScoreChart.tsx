"use client";

import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
} from "recharts";

interface RadarScoreChartProps {
  techScore: number;
  fundScore: number;
  sectorScore: number;
  sentimentScore: number;
  riskPenalty: number;
  verdict?: string;
}

export default function RadarScoreChart({
  techScore,
  fundScore,
  sectorScore,
  sentimentScore,
  riskPenalty,
  verdict,
}: RadarScoreChartProps) {
  const data = [
    { axis: "Technical", value: techScore },
    { axis: "Fundamental", value: fundScore },
    { axis: "Sector", value: sectorScore },
    { axis: "Sentiment", value: sentimentScore },
    { axis: "Risk", value: Math.max(0, 100 - riskPenalty * 10) },
  ];

  const fillColor =
    verdict === "STRONG_BUY"
      ? "#22c55e"
      : verdict === "MEDIUM_BUY"
        ? "#eab308"
        : verdict === "WEAK_BUY"
          ? "#f97316"
          : "#6b7280";

  return (
    <ResponsiveContainer width="100%" height={280}>
      <RadarChart data={data} cx="50%" cy="50%" outerRadius="70%">
        <PolarGrid stroke="#e5e7eb" />
        <PolarAngleAxis dataKey="axis" tick={{ fill: "#6b7280", fontSize: 12 }} />
        <PolarRadiusAxis
          angle={90}
          domain={[0, 100]}
          tick={{ fill: "#9ca3af", fontSize: 10 }}
        />
        <Radar
          dataKey="value"
          stroke={fillColor}
          fill={fillColor}
          fillOpacity={0.25}
          strokeWidth={2}
        />
      </RadarChart>
    </ResponsiveContainer>
  );
}
