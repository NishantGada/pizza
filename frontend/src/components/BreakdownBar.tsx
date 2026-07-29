import { money } from "../lib/format";

export type Cycle = {
  income: string;
  savingsAmount: string;
  retirementAmount: string;
  hsaAmount: string;
  categoriesTotal: string;
  availableSpending: string;
};

const SEGMENTS = [
  { key: "savingsAmount", label: "Savings", color: "#f59e0b" },
  { key: "retirementAmount", label: "401(k)", color: "#10b981" },
  { key: "hsaAmount", label: "HSA", color: "#0ea5e9" },
  { key: "categoriesTotal", label: "Categories", color: "#8b5cf6" },
  { key: "availableSpending", label: "Spending", color: "#334155" },
] as const;

export default function BreakdownBar({
  cycle,
  showLegend = true,
  showPercent = false,
}: {
  cycle: Cycle;
  showLegend?: boolean;
  showPercent?: boolean;
}) {
  const income = Number(cycle.income) || 0;
  const overspent = Number(cycle.availableSpending) < 0;
  const pctOf = (v: string) => (income > 0 ? `${Math.round((Number(v) / income) * 100)}%` : "—");

  return (
    <div className="space-y-3">
      <div className="flex h-3 w-full overflow-hidden rounded-full bg-slate-100">
        {SEGMENTS.map((seg) => {
          const value = Math.max(0, Number(cycle[seg.key]) || 0);
          const width = income > 0 ? (value / income) * 100 : 0;
          if (width <= 0) return null;
          return (
            <div
              key={seg.key}
              style={{ width: `${width}%`, backgroundColor: seg.color }}
              title={`${seg.label}: ${money(cycle[seg.key])}`}
            />
          );
        })}
      </div>
      {showLegend && (
        <ul className="grid grid-cols-2 gap-x-4 gap-y-1.5 sm:grid-cols-3">
          {SEGMENTS.map((seg) => (
            <li key={seg.key} className="flex items-center justify-between text-sm">
              <span className="flex items-center gap-2 text-slate-600">
                <span className="h-2.5 w-2.5 rounded-sm" style={{ backgroundColor: seg.color }} />
                {seg.label}
              </span>
              <span className="flex items-baseline gap-2">
                {showPercent && (
                  <span className="text-xs tabular-nums text-slate-400">{pctOf(cycle[seg.key])}</span>
                )}
                <span
                  className={
                    seg.key === "availableSpending" && overspent
                      ? "font-medium text-red-600"
                      : "font-medium text-slate-900"
                  }
                >
                  {money(cycle[seg.key])}
                </span>
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
