import { useState, type FormEvent } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery } from "urql";

import BreakdownBar, { type Cycle } from "../components/BreakdownBar";
import { Button, Card, ErrorNote, Field, Input, KindToggle, Spinner } from "../components/ui";
import {
  ADD_CATEGORY,
  DELETE_CATEGORY,
  DELETE_PAY_CYCLE,
  PAY_CYCLE,
  UPDATE_CATEGORY,
  UPDATE_PAY_CYCLE,
} from "../gql/operations";
import { dateRange, describeKind, kindToInput, kindToStored, money, type Kind } from "../lib/format";

type Category = { id: string; name: string; kind: Kind; value: string; amount: string };
type CycleFull = Cycle & {
  id: string;
  startDate: string;
  endDate: string;
  categories: Category[];
};

export default function CycleDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [{ data, fetching, error }, refetch] = useQuery<{ payCycle: CycleFull }>({
    query: PAY_CYCLE,
    variables: { id },
    requestPolicy: "cache-and-network",
  });
  const [, updateCycle] = useMutation(UPDATE_PAY_CYCLE);
  const [, deleteCycle] = useMutation(DELETE_PAY_CYCLE);

  const [editingIncome, setEditingIncome] = useState(false);
  const [incomeDraft, setIncomeDraft] = useState("");

  if (fetching && !data) return <Spinner />;
  if (error) return <ErrorNote>{error.message}</ErrorNote>;
  const cycle = data?.payCycle;
  if (!cycle) return <ErrorNote>Pay cycle not found.</ErrorNote>;

  const reload = () => refetch({ requestPolicy: "network-only" });

  async function saveIncome() {
    await updateCycle({ id, income: incomeDraft });
    setEditingIncome(false);
    reload();
  }

  async function onDelete() {
    if (!confirm("Delete this pay cycle and all its categories?")) return;
    await deleteCycle({ id });
    navigate("/", { replace: true });
  }

  const overspent = Number(cycle.availableSpending) < 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <button onClick={() => navigate("/")} className="text-sm text-slate-500 hover:underline">
          ← Back
        </button>
        <Button variant="danger" size="sm" onClick={onDelete}>
          Delete cycle
        </Button>
      </div>

      <Card className="p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="text-xl font-semibold tracking-tight">
              {dateRange(cycle.startDate, cycle.endDate)}
            </h1>
            <div className="mt-1 flex items-center gap-2 text-slate-500">
              {editingIncome ? (
                <>
                  <Input
                    type="number"
                    min="0"
                    step="0.01"
                    className="w-32"
                    value={incomeDraft}
                    onChange={(e) => setIncomeDraft(e.target.value)}
                  />
                  <Button size="sm" onClick={saveIncome}>
                    Save
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => setEditingIncome(false)}>
                    Cancel
                  </Button>
                </>
              ) : (
                <>
                  <span className="text-sm">{money(cycle.income)} post-tax income</span>
                  <button
                    onClick={() => {
                      setIncomeDraft(cycle.income);
                      setEditingIncome(true);
                    }}
                    className="text-xs font-medium text-amber-700 hover:underline"
                  >
                    edit
                  </button>
                </>
              )}
            </div>
          </div>
          <div className="text-right">
            <div className="text-xs uppercase tracking-wide text-slate-400">Available spending</div>
            <div
              className={`text-3xl font-semibold ${overspent ? "text-red-600" : "text-slate-900"}`}
            >
              {money(cycle.availableSpending)}
            </div>
          </div>
        </div>
        <div className="mt-6">
          <BreakdownBar cycle={cycle} showPercent />
        </div>
        {overspent && (
          <p className="mt-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
            Your allocations exceed this paycheck. Trim a category or lower your savings rate.
          </p>
        )}
      </Card>

      <CategorySection cycleId={id!} categories={cycle.categories} onChange={reload} />
    </div>
  );
}

function CategorySection({
  cycleId,
  categories,
  onChange,
}: {
  cycleId: string;
  categories: Category[];
  onChange: () => void;
}) {
  const [, addCategory] = useMutation(ADD_CATEGORY);
  const [, updateCategory] = useMutation(UPDATE_CATEGORY);
  const [, deleteCategory] = useMutation(DELETE_CATEGORY);
  const [name, setName] = useState("");
  const [kind, setKind] = useState<Kind>("PERCENT");
  const [amount, setAmount] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function onAdd(e: FormEvent) {
    e.preventDefault();
    setError(null);
    const res = await addCategory({ payCycleId: cycleId, name, kind, value: kindToStored(kind, amount) });
    if (res.error) {
      setError(res.error.graphQLErrors[0]?.message ?? res.error.message);
      return;
    }
    setName("");
    setAmount("");
    onChange();
  }

  return (
    <Card className="p-6">
      <h2 className="mb-1 text-sm font-semibold uppercase tracking-wide text-slate-400">
        Categories
      </h2>
      <p className="mb-4 text-xs text-slate-400">
        Snapshotted from your contribution settings. Tweak or remove them just for this paycheck.
      </p>

      <ul className="divide-y divide-slate-100">
        {categories.length === 0 && (
          <li className="py-2 text-sm text-slate-400">No categories yet.</li>
        )}
        {categories.map((cat) => (
          <CategoryRow
            key={cat.id}
            category={cat}
            onSave={async (n, k, v) => {
              await updateCategory({ id: cat.id, name: n, kind: k, value: v });
              onChange();
            }}
            onDelete={async () => {
              await deleteCategory({ id: cat.id });
              onChange();
            }}
          />
        ))}
      </ul>

      <form onSubmit={onAdd} className="mt-4 flex flex-wrap items-end gap-3">
        <div className="min-w-40 flex-1">
          <Field label="Name">
            <Input
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Fitness"
            />
          </Field>
        </div>
        <Field label="Type">
          <KindToggle value={kind} onChange={setKind} />
        </Field>
        <div className="w-28">
          <Field label={kind === "PERCENT" ? "Percent" : "Amount"}>
            <div className="flex items-center gap-1.5">
              {kind === "FIXED" && <span className="text-slate-500">$</span>}
              <Input
                type="number"
                min="0"
                step={kind === "PERCENT" ? "0.1" : "0.01"}
                required
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder={kind === "PERCENT" ? "5" : "50.00"}
              />
              {kind === "PERCENT" && <span className="text-slate-500">%</span>}
            </div>
          </Field>
        </div>
        <Button type="submit">Add</Button>
      </form>
      <ErrorNote>{error}</ErrorNote>
    </Card>
  );
}

function CategoryRow({
  category,
  onSave,
  onDelete,
}: {
  category: Category;
  onSave: (name: string, kind: Kind, value: string) => Promise<void>;
  onDelete: () => Promise<void>;
}) {
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState(category.name);
  const [kind, setKind] = useState<Kind>(category.kind);
  const [amount, setAmount] = useState(kindToInput(category.kind, category.value));

  if (editing) {
    return (
      <li className="flex flex-wrap items-center gap-2 py-2">
        <Input className="min-w-32 flex-1" value={name} onChange={(e) => setName(e.target.value)} />
        <KindToggle value={kind} onChange={setKind} />
        <div className="flex w-24 items-center gap-1">
          {kind === "FIXED" && <span className="text-slate-500">$</span>}
          <Input
            type="number"
            min="0"
            step={kind === "PERCENT" ? "0.1" : "0.01"}
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
          />
          {kind === "PERCENT" && <span className="text-slate-500">%</span>}
        </div>
        <Button
          size="sm"
          onClick={async () => {
            await onSave(name, kind, kindToStored(kind, amount));
            setEditing(false);
          }}
        >
          Save
        </Button>
        <Button size="sm" variant="ghost" onClick={() => setEditing(false)}>
          Cancel
        </Button>
      </li>
    );
  }

  return (
    <li className="flex items-center justify-between py-2.5">
      <span className="text-slate-700">{category.name}</span>
      <div className="flex items-center gap-3">
        {category.kind === "PERCENT" && (
          <span className="text-xs tabular-nums text-slate-400">
            {describeKind(category.kind, category.value)}
          </span>
        )}
        <span className="font-medium text-slate-900">{money(category.amount)}</span>
        <button
          onClick={() => {
            setName(category.name);
            setKind(category.kind);
            setAmount(kindToInput(category.kind, category.value));
            setEditing(true);
          }}
          className="text-xs font-medium text-amber-700 hover:underline"
        >
          edit
        </button>
        <button onClick={onDelete} className="text-xs font-medium text-red-600 hover:underline">
          remove
        </button>
      </div>
    </li>
  );
}
