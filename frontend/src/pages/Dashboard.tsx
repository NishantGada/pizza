import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery } from "urql";

import BreakdownBar, { type Cycle } from "../components/BreakdownBar";
import { Button, Card, ErrorNote, Field, Input, Spinner } from "../components/ui";
import { CREATE_PAY_CYCLE, DASHBOARD } from "../gql/operations";
import { dateRange, money } from "../lib/format";

type CycleRow = Cycle & { id: string; startDate: string; endDate: string };
type CategoryTotal = { name: string; total: string; cycleCount: number };
type Summary = {
  cycleCount: number;
  totalIncome: string;
  totalSaved: string;
  totalRetirement: string;
  totalHsa: string;
  totalAllocated: string;
  totalContributed: string;
  totalAvailable: string;
  byCategory: CategoryTotal[];
};

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <Card className="p-4">
      <div className="text-xs font-medium uppercase tracking-wide text-slate-400">{label}</div>
      <div className="mt-1 text-2xl font-semibold tracking-tight">{value}</div>
    </Card>
  );
}

export default function Dashboard() {
  const [{ data, fetching, error }, refetch] = useQuery<{
    dashboard: Summary;
    payCycles: CycleRow[];
  }>({ query: DASHBOARD, requestPolicy: "cache-and-network" });

  if (fetching && !data) return <Spinner />;
  if (error) return <ErrorNote>{error.message}</ErrorNote>;

  const summary = data?.dashboard;
  const cycles = data?.payCycles ?? [];

  return (
    <div className="space-y-8">
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Stat label="Pay cycles" value={String(summary?.cycleCount ?? 0)} />
        <Stat label="Total income" value={money(summary?.totalIncome ?? 0)} />
        <Stat label="Total saved" value={money(summary?.totalSaved ?? 0)} />
        <Stat label="Total spending" value={money(summary?.totalAvailable ?? 0)} />
      </div>

      {summary && summary.cycleCount > 0 && <Contributions summary={summary} />}

      <NewCycleForm onCreated={() => refetch({ requestPolicy: "network-only" })} />

      <section className="space-y-3">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">
          Pay cycles
        </h2>
        {cycles.length === 0 ? (
          <Card className="p-8 text-center text-sm text-slate-500">
            No pay cycles yet. Add your first paycheck above to see the breakdown.
          </Card>
        ) : (
          <div className="space-y-3">
            {cycles.map((c) => (
              <Link key={c.id} to={`/cycles/${c.id}`} className="block">
                <Card className="p-5 transition-shadow hover:shadow-md">
                  <div className="mb-4 flex items-baseline justify-between">
                    <div>
                      <div className="font-medium">{dateRange(c.startDate, c.endDate)}</div>
                      <div className="text-sm text-slate-500">{money(c.income)} income</div>
                    </div>
                    <div className="text-right">
                      <div className="text-xs uppercase tracking-wide text-slate-400">
                        Spending
                      </div>
                      <div className="text-lg font-semibold text-slate-900">
                        {money(c.availableSpending)}
                      </div>
                    </div>
                  </div>
                  <BreakdownBar cycle={c} showLegend={false} />
                </Card>
              </Link>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

function Contributions({ summary }: { summary: Summary }) {
  const income = Number(summary.totalIncome) || 0;
  const pct = (v: string) => (income > 0 ? `${Math.round((Number(v) / income) * 100)}%` : "—");
  const fixed = [
    { label: "Savings", value: summary.totalSaved, color: "#f59e0b" },
    { label: "401(k)", value: summary.totalRetirement, color: "#10b981" },
    { label: "HSA", value: summary.totalHsa, color: "#0ea5e9" },
  ];

  return (
    <Card className="p-6">
      <div className="mb-5 flex items-baseline justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">
          Contributions
        </h2>
        <div className="text-right">
          <span className="text-lg font-semibold">{money(summary.totalContributed)}</span>
          <span className="ml-2 text-sm text-slate-400">
            {pct(summary.totalContributed)} of income
          </span>
        </div>
      </div>

      <ul className="space-y-2.5">
        {fixed.map((f) => (
          <li key={f.label} className="flex items-center justify-between text-sm">
            <span className="flex items-center gap-2 text-slate-600">
              <span className="h-2.5 w-2.5 rounded-sm" style={{ backgroundColor: f.color }} />
              {f.label}
            </span>
            <span className="flex items-baseline gap-2">
              <span className="text-xs tabular-nums text-slate-400">{pct(f.value)}</span>
              <span className="font-medium text-slate-900">{money(f.value)}</span>
            </span>
          </li>
        ))}
      </ul>

      {summary.byCategory.length > 0 && (
        <>
          <div className="my-4 flex items-center gap-2 border-t border-slate-100 pt-4">
            <span className="h-2.5 w-2.5 rounded-sm" style={{ backgroundColor: "#8b5cf6" }} />
            <span className="text-xs font-semibold uppercase tracking-wide text-slate-400">
              Categories
            </span>
            <span className="text-xs text-slate-400">· {money(summary.totalAllocated)} total</span>
          </div>
          <ul className="space-y-2.5">
            {summary.byCategory.map((c) => (
              <li key={c.name} className="flex items-center justify-between text-sm">
                <span className="text-slate-600">
                  {c.name}
                  <span className="ml-2 text-xs text-slate-400">
                    {c.cycleCount} {c.cycleCount === 1 ? "cycle" : "cycles"}
                  </span>
                </span>
                <span className="flex items-baseline gap-2">
                  <span className="text-xs tabular-nums text-slate-400">{pct(c.total)}</span>
                  <span className="font-medium text-slate-900">{money(c.total)}</span>
                </span>
              </li>
            ))}
          </ul>
        </>
      )}
    </Card>
  );
}

function NewCycleForm({ onCreated }: { onCreated: () => void }) {
  const [open, setOpen] = useState(false);
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [income, setIncome] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [{ fetching }, create] = useMutation(CREATE_PAY_CYCLE);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    const res = await create({ startDate, endDate, income });
    if (res.error) {
      setError(res.error.graphQLErrors[0]?.message ?? res.error.message);
      return;
    }
    setStartDate("");
    setEndDate("");
    setIncome("");
    setOpen(false);
    onCreated();
  }

  if (!open) {
    return (
      <Button onClick={() => setOpen(true)}>+ New pay cycle</Button>
    );
  }

  return (
    <Card className="p-5">
      <form onSubmit={onSubmit} className="space-y-4">
        <div className="grid gap-4 sm:grid-cols-3">
          <Field label="Start date">
            <Input type="date" required value={startDate} onChange={(e) => setStartDate(e.target.value)} />
          </Field>
          <Field label="End date">
            <Input type="date" required value={endDate} onChange={(e) => setEndDate(e.target.value)} />
          </Field>
          <Field label="Income (post-tax)">
            <Input
              type="number"
              min="0"
              step="0.01"
              required
              value={income}
              onChange={(e) => setIncome(e.target.value)}
              placeholder="2000.00"
            />
          </Field>
        </div>
        <ErrorNote>{error}</ErrorNote>
        <div className="flex gap-2">
          <Button type="submit" disabled={fetching}>
            {fetching ? "Saving…" : "Add pay cycle"}
          </Button>
          <Button type="button" variant="ghost" onClick={() => setOpen(false)}>
            Cancel
          </Button>
        </div>
      </form>
    </Card>
  );
}
