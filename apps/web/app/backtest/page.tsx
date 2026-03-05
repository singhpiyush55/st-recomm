"use client";

import { useEffect, useState } from "react";
import { getBacktestResults } from "@/lib/api";
import Card from "@/components/ui/Card";
import EquityCurveChart from "@/components/charts/EquityCurveChart";
import { formatPercent } from "@/lib/formatters";

export default function BacktestPage() {
  const [stats, setStats] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getBacktestResults()
      .then(setStats)
      .catch((e) => setError(e.message));
  }, []);

  // Simple simulated equity curve from stats
  const equityData =
    stats && stats.totalTrades > 0
      ? Array.from({ length: stats.totalTrades }, (_, i) => ({
          date: `Trade ${i + 1}`,
          value: Math.round(
            10000 * (1 + (stats.avgReturn / 100) * (i + 1)) +
              (Math.random() - 0.5) * 200
          ),
        }))
      : [];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Backtest Results</h2>
        <p className="text-sm text-gray-500">
          How recommendations would have performed historically
        </p>
      </div>

      {error ? (
        <p className="py-8 text-center text-sm text-red-400">{error}</p>
      ) : stats ? (
        <>
          {/* Stats grid */}
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <Card>
              <p className="text-xs text-gray-500">Total Trades</p>
              <p className="mt-1 text-2xl font-bold text-gray-900">
                {stats.totalTrades}
              </p>
            </Card>
            <Card>
              <p className="text-xs text-gray-500">Win Rate</p>
              <p className="mt-1 text-2xl font-bold text-green-600">
                {formatPercent(stats.winRate)}
              </p>
            </Card>
            <Card>
              <p className="text-xs text-gray-500">Avg Return</p>
              <p
                className={`mt-1 text-2xl font-bold ${
                  stats.avgReturn >= 0 ? "text-green-600" : "text-red-600"
                }`}
              >
                {formatPercent(stats.avgReturn)}
              </p>
            </Card>
            <Card>
              <p className="text-xs text-gray-500">Expectancy</p>
              <p
                className={`mt-1 text-2xl font-bold ${
                  stats.expectancy >= 0 ? "text-blue-600" : "text-red-600"
                }`}
              >
                {formatPercent(stats.expectancy)}
              </p>
            </Card>
          </div>

          {/* Trade breakdown */}
          <div className="grid grid-cols-3 gap-4">
            <Card>
              <p className="text-xs text-gray-500">Hit Target</p>
              <p className="mt-1 text-xl font-bold text-green-600">
                {stats.hitTargetCount}
              </p>
            </Card>
            <Card>
              <p className="text-xs text-gray-500">Hit Stop</p>
              <p className="mt-1 text-xl font-bold text-red-600">
                {stats.hitStopCount}
              </p>
            </Card>
            <Card>
              <p className="text-xs text-gray-500">Open</p>
              <p className="mt-1 text-xl font-bold text-yellow-600">
                {stats.openCount}
              </p>
            </Card>
          </div>

          {/* Equity curve */}
          {equityData.length > 0 && (
            <Card title="Simulated Equity Curve">
              <EquityCurveChart data={equityData} />
            </Card>
          )}
        </>
      ) : (
        <Card className="text-center">
          <p className="py-8 text-gray-500">Loading backtest data…</p>
        </Card>
      )}
    </div>
  );
}
