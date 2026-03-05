"use client";

import { usePathname } from "next/navigation";

const pageTitles: Record<string, string> = {
  "/dashboard": "Dashboard",
  "/recommendations": "Recommendations",
  "/sectors": "Sector Rankings",
  "/backtest": "Backtest Results",
  "/pipeline": "Pipeline Runs",
};

export default function TopBar() {
  const pathname = usePathname();
  const title =
    Object.entries(pageTitles).find(([path]) =>
      pathname.startsWith(path)
    )?.[1] ?? "Stock Recommender";

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center border-b border-gray-200 bg-white/80 px-6 backdrop-blur">
      <h1 className="text-lg font-semibold text-gray-900">{title}</h1>
    </header>
  );
}
