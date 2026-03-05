import { verdictBgColor } from "@/lib/formatters";

interface BadgeProps {
  verdict: string;
  className?: string;
}

export default function Badge({ verdict, className = "" }: BadgeProps) {
  const label = verdict.replace("_", " ");
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold ${verdictBgColor(verdict)} ${className}`}
    >
      {label}
    </span>
  );
}
