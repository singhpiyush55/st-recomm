/**
 * Format a score to 1 decimal place.
 */
export function formatScore(score: number): string {
  return score.toFixed(1);
}

/**
 * Format a number as a percentage string (e.g. "12.5%").
 */
export function formatPercent(value: number): string {
  return `${value.toFixed(2)}%`;
}

/**
 * Format a number as an INR currency string.
 */
export function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

/**
 * Format an ISO date string to a readable format.
 */
export function formatDate(date: string): string {
  return new Date(date).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

/**
 * Return a Tailwind text-color class based on verdict.
 */
export function verdictColor(verdict: string): string {
  switch (verdict) {
    case "STRONG_BUY":
      return "text-green-600";
    case "MEDIUM_BUY":
      return "text-yellow-600";
    case "WEAK_BUY":
      return "text-orange-600";
    case "AVOID":
      return "text-red-600";
    default:
      return "text-gray-500";
  }
}

/**
 * Return a Tailwind bg-color class based on verdict (for badges).
 */
export function verdictBgColor(verdict: string): string {
  switch (verdict) {
    case "STRONG_BUY":
      return "bg-green-100 text-green-700 border-green-300";
    case "MEDIUM_BUY":
      return "bg-yellow-100 text-yellow-700 border-yellow-300";
    case "WEAK_BUY":
      return "bg-orange-100 text-orange-700 border-orange-300";
    case "AVOID":
      return "bg-red-100 text-red-700 border-red-300";
    default:
      return "bg-gray-100 text-gray-700 border-gray-300";
  }
}
