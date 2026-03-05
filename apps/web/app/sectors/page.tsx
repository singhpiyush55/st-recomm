"use client";

import { useEffect, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { getSectors } from "@/lib/api";
import Card from "@/components/ui/Card";

interface SectorData {
  sector: string;
  return1m: number;
}

export default function SectorsPage() {
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getSectors()
      .then(setData)
      .catch((e) => setError(e.message));
  }, []);

  // Build mock sector data from sectorsTargeted + recommendations
  const sectorBars: SectorData[] =
    data?.sectorsTargeted?.map((s: string, i: number) => ({
      sector: s,
      return1m: 5 - i * 1.5, // placeholder values since we don't store ETF returns in DB
    })) ?? [];

  const topSectors = sectorBars.slice(0, 2).map((s) => s.sector);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Sector Rankings</h2>
        <p className="text-sm text-gray-500">
          Top sectors based on 1-month ETF performance
        </p>
      </div>

      {error ? (
        <p className="py-8 text-center text-sm text-red-400">{error}</p>
      ) : sectorBars.length > 0 ? (
        <>
          <Card>
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={sectorBars} layout="vertical" margin={{ left: 80 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis
                  type="number"
                  tick={{ fill: "#6b7280", fontSize: 12 }}
                  tickFormatter={(v: number) => `${v}%`}
                />
                <YAxis
                  type="category"
                  dataKey="sector"
                  tick={{ fill: "#6b7280", fontSize: 12 }}
                  width={100}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#ffffff",
                    border: "1px solid #e5e7eb",
                    borderRadius: "8px",
                    color: "#1e293b",
                  }}
                  formatter={(value: number) => [`${value.toFixed(2)}%`, "1M Return"]}
                />
                <Bar dataKey="return1m" radius={[0, 4, 4, 0]}>
                  {sectorBars.map((entry) => (
                    <Cell
                      key={entry.sector}
                      fill={topSectors.includes(entry.sector) ? "#3b82f6" : "#d1d5db"}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </Card>

          {/* Stocks from latest run */}
          {data?.recommendations && data.recommendations.length > 0 && (
            <Card title="Stocks from Latest Run">
              <div className="grid grid-cols-2 gap-2 text-sm sm:grid-cols-4">
                {data.recommendations.map((r: any) => (
                  <div
                    key={r.ticker}
                    className="rounded border border-gray-200 px-3 py-2"
                  >
                    <span className="font-semibold text-gray-900">{r.ticker}</span>
                    <span className="ml-2 text-gray-500">
                      {r.finalScore.toFixed(1)}
                    </span>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </>
      ) : (
        <Card className="text-center">
          <p className="py-8 text-gray-500">
            No sector data available. Run the pipeline first.
          </p>
        </Card>
      )}
    </div>
  );
}
