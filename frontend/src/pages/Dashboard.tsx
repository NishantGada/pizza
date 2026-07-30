import { Fragment, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery } from "urql";

import BreakdownBar, { type Cycle } from "../components/BreakdownBar";
import { Button, Card, ErrorNote, Field, Input, Spinner } from "../components/ui";
import { CREATE_PAY_CYCLE, DASHBOARD } from "../gql/operations";
import { dateRange, money } from "../lib/format";

type CycleRow = Cycle & { id: string; startDate: string; endDate: string };
type Projection = { actual: string; annual: string; relative: string };
type CategoryTotal = { name: string; cycleCount: number; projection: Projection };
type Summary = {
  cycleCount: number;
  totalIncome: string;
  totalSaved: string;
  totalRetirement: string;
  totalHsa: string;
  totalAllocated: string;
  totalContributed: string;
  totalAvailable: string;
  projectionLabel: string;
  savedProjection: Projection;
  retirementProjection: Projection;
  hsaProjection: Projection;
  allocatedProjection: Projection;
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

const COLS = "grid grid-cols-[1fr_auto_auto_auto] items-center gap-x-6 gap-y-2.5 text-sm";

function ColumnHeader({ label }: { label: string }) {
  return (
    <>
      <span />
      <span className="text-right text-[10px] font-semibold uppercase tracking-wide text-slate-400">
        Actual
      </span>
      <span className="text-right text-[10px] font-semibold uppercase tracking-wide text-slate-400">
        Annual
      </span>
      <span className="text-right text-[10px] font-semibold uppercase tracking-wide text-slate-400">
        {label}
      </span>
    </>
  );
}

function ProjectionCells({ proj }: { proj: Projection }) {
  return (
    <>
      <span className="text-right font-medium tabular-nums text-slate-900">
        {money(proj.actual)}
      </span>
      <span className="text-right tabular-nums text-slate-500">{money(proj.annual)}</span>
      <span className="text-right tabular-nums text-slate-500">{money(proj.relative)}</span>
    </>
  );
}

function Contributions({ summary }: { summary: Summary }) {
  const label = summary.projectionLabel || "To date";
  const fixed = [
    { name: "Savings", proj: summary.savedProjection, color: "#f59e0b" },
    { name: "401(k)", proj: summary.retirementProjection, color: "#10b981" },
    { name: "HSA", proj: summary.hsaProjection, color: "#0ea5e9" },
  ];

  return (
    <Card className="p-6">
      <div className="mb-5 flex items-baseline justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">
          Contributions
        </h2>
        <div className="text-right">
          <span className="text-lg font-semibold">{money(summary.totalContributed)}</span>
          <span className="ml-2 text-sm text-slate-400">contributed so far</span>
        </div>
      </div>

      <div className={COLS}>
        <ColumnHeader label={label} />
        {fixed.map((f) => (
          <Fragment key={f.name}>
            <span className="flex items-center gap-2 text-slate-600">
              <span className="h-2.5 w-2.5 rounded-sm" style={{ backgroundColor: f.color }} />
              {f.name}
            </span>
            <ProjectionCells proj={f.proj} />
          </Fragment>
        ))}
      </div>

      {summary.byCategory.length > 0 && (
        <>
          <div className="my-4 flex items-center gap-2 border-t border-slate-100 pt-4">
            <span className="h-2.5 w-2.5 rounded-sm" style={{ backgroundColor: "#8b5cf6" }} />
            <span className="text-xs font-semibold uppercase tracking-wide text-slate-400">
              Categories
            </span>
            <span className="text-xs text-slate-400">· {money(summary.totalAllocated)} tracked</span>
          </div>
          <div className={COLS}>
            {summary.byCategory.map((c) => (
              <Fragment key={c.name}>
                <span className="text-slate-600">
                  {c.name}
                  <span className="ml-2 text-xs text-slate-400">
                    {c.cycleCount} {c.cycleCount === 1 ? "cycle" : "cycles"}
                  </span>
                </span>
                <ProjectionCells proj={c.projection} />
              </Fragment>
            ))}
          </div>
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
