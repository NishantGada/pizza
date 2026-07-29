import { useEffect, useState, type FormEvent } from "react";
import { useMutation, useQuery } from "urql";

import { Button, Card, ErrorNote, Field, Input, KindToggle, Spinner } from "../components/ui";
import {
  ADD_CONTRIBUTION_CATEGORY,
  APPLY_CONTRIBUTIONS_TO_CYCLES,
  BUDGET_SETTINGS,
  CONTRIBUTION_CATEGORIES,
  DELETE_CONTRIBUTION_CATEGORY,
  UPDATE_BUDGET_SETTINGS,
  UPDATE_CONTRIBUTION_CATEGORY,
} from "../gql/operations";
import { describeKind, kindToInput, kindToStored, type Kind } from "../lib/format";

type SettingsData = {
  id: string;
  savingsPct: string;
  retirement401kPct: string;
  hsaPerCycle: string;
};

type ContribCategory = { id: string; name: string; kind: Kind; value: string };

export default function Settings() {
  return (
    <div className="mx-auto max-w-lg space-y-8">
      <BudgetSettingsSection />
      <ContributionCategoriesSection />
    </div>
  );
}

function BudgetSettingsSection() {
  const [{ data, fetching, error }] = useQuery<{ budgetSettings: SettingsData }>({
    query: BUDGET_SETTINGS,
    requestPolicy: "cache-and-network",
  });
  const [, update] = useMutation(UPDATE_BUDGET_SETTINGS);

  const [savings, setSavings] = useState("");
  const [retirement, setRetirement] = useState("");
  const [hsa, setHsa] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (data?.budgetSettings) {
      const s = data.budgetSettings;
      setSavings((Number(s.savingsPct) * 100).toString());
      setRetirement((Number(s.retirement401kPct) * 100).toString());
      setHsa(Number(s.hsaPerCycle).toString());
    }
  }, [data]);

  if (fetching && !data) return <Spinner />;
  if (error) return <ErrorNote>{error.message}</ErrorNote>;

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setFormError(null);
    setSaved(false);
    const res = await update({
      savingsPct: (Number(savings) / 100).toString(),
      retirement401kPct: (Number(retirement) / 100).toString(),
      hsaPerCycle: hsa,
    });
    if (res.error) {
      setFormError(res.error.graphQLErrors[0]?.message ?? res.error.message);
      return;
    }
    setSaved(true);
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">Budget settings</h1>
        <p className="mt-1 text-sm text-slate-500">
          Defaults applied to new pay cycles. Editing these never changes past cycles.
        </p>
      </div>

      <Card className="p-6">
        <form onSubmit={onSubmit} className="space-y-5">
          <Field label="Savings rate" hint="Percent of each post-tax paycheck moved to savings.">
            <div className="flex items-center gap-2">
              <Input
                type="number"
                min="0"
                max="100"
                step="0.1"
                value={savings}
                onChange={(e) => setSavings(e.target.value)}
              />
              <span className="text-slate-500">%</span>
            </div>
          </Field>
          <Field label="401(k) contribution" hint="Percent of each post-tax paycheck.">
            <div className="flex items-center gap-2">
              <Input
                type="number"
                min="0"
                max="100"
                step="0.1"
                value={retirement}
                onChange={(e) => setRetirement(e.target.value)}
              />
              <span className="text-slate-500">%</span>
            </div>
          </Field>
          <Field label="HSA per pay cycle" hint="Fixed dollar amount (e.g. $50 = $100/month).">
            <div className="flex items-center gap-2">
              <span className="text-slate-500">$</span>
              <Input
                type="number"
                min="0"
                step="0.01"
                value={hsa}
                onChange={(e) => setHsa(e.target.value)}
              />
            </div>
          </Field>
          <ErrorNote>{formError}</ErrorNote>
          <div className="flex items-center gap-3">
            <Button type="submit">Save settings</Button>
            {saved && <span className="text-sm text-emerald-600">Saved ✓</span>}
          </div>
        </form>
      </Card>
    </div>
  );
}

function ContributionCategoriesSection() {
  const [{ data, fetching, error }, refetch] = useQuery<{
    contributionCategories: ContribCategory[];
  }>({ query: CONTRIBUTION_CATEGORIES, requestPolicy: "cache-and-network" });
  const [, addCategory] = useMutation(ADD_CONTRIBUTION_CATEGORY);
  const [, deleteCategory] = useMutation(DELETE_CONTRIBUTION_CATEGORY);
  const [{ fetching: applying }, applyToCycles] = useMutation(APPLY_CONTRIBUTIONS_TO_CYCLES);

  const [name, setName] = useState("");
  const [kind, setKind] = useState<Kind>("PERCENT");
  const [amount, setAmount] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const [applyMsg, setApplyMsg] = useState<string | null>(null);

  const reload = () => refetch({ requestPolicy: "network-only" });
  const categories = data?.contributionCategories ?? [];

  async function onApply() {
    setApplyMsg(null);
    const res = await applyToCycles({});
    if (res.error) {
      setApplyMsg(res.error.graphQLErrors[0]?.message ?? res.error.message);
      return;
    }
    const n: number = res.data?.applyContributionsToCycles ?? 0;
    setApplyMsg(
      n === 0
        ? "Existing cycles already include all categories."
        : `Applied — added ${n} ${n === 1 ? "category" : "categories"} across your cycles.`,
    );
  }

  async function onAdd(e: FormEvent) {
    e.preventDefault();
    setFormError(null);
    const res = await addCategory({ name, kind, value: kindToStored(kind, amount) });
    if (res.error) {
      setFormError(res.error.graphQLErrors[0]?.message ?? res.error.message);
      return;
    }
    setName("");
    setAmount("");
    reload();
  }

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold tracking-tight">Contribution categories</h2>
        <p className="mt-1 text-sm text-slate-500">
          Buckets that come out of every paycheck — a percent of income (e.g. Vacation 5%) or a
          fixed amount (e.g. Gym $50). Applied to new pay cycles; you can still tweak them per
          cycle.
        </p>
      </div>

      <Card className="p-6">
        {fetching && !data ? (
          <Spinner />
        ) : error ? (
          <ErrorNote>{error.message}</ErrorNote>
        ) : (
          <>
            <ul className="divide-y divide-slate-100">
              {categories.length === 0 && (
                <li className="py-2 text-sm text-slate-400">
                  No contribution categories yet. Add one below.
                </li>
              )}
              {categories.map((cat) => (
                <ContribRow
                  key={cat.id}
                  category={cat}
                  onSaved={reload}
                  onDelete={async () => {
                    await deleteCategory({ id: cat.id });
                    reload();
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
                    placeholder="Vacation"
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
            <ErrorNote>{formError}</ErrorNote>

            {categories.length > 0 && (
              <div className="mt-5 flex flex-wrap items-center gap-3 border-t border-slate-100 pt-4">
                <Button variant="ghost" size="sm" onClick={onApply} disabled={applying}>
                  {applying ? "Applying…" : "Apply to existing cycles"}
                </Button>
                <span className="text-xs text-slate-400">
                  New cycles get these automatically. Use this to add them to paychecks you
                  already created.
                </span>
                {applyMsg && <span className="text-sm text-emerald-600">{applyMsg}</span>}
              </div>
            )}
          </>
        )}
      </Card>
    </div>
  );
}

function ContribRow({
  category,
  onSaved,
  onDelete,
}: {
  category: ContribCategory;
  onSaved: () => void;
  onDelete: () => Promise<void>;
}) {
  const [, updateCategory] = useMutation(UPDATE_CONTRIBUTION_CATEGORY);
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState(category.name);
  const [kind, setKind] = useState<Kind>(category.kind);
  const [amount, setAmount] = useState(kindToInput(category.kind, category.value));

  function startEdit() {
    setName(category.name);
    setKind(category.kind);
    setAmount(kindToInput(category.kind, category.value));
    setEditing(true);
  }

  async function save() {
    await updateCategory({ id: category.id, name, kind, value: kindToStored(kind, amount) });
    setEditing(false);
    onSaved();
  }

  if (editing) {
    return (
      <li className="flex flex-wrap items-center gap-2 py-2.5">
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
        <Button size="sm" onClick={save}>
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
        <span className="font-medium text-slate-900">{describeKind(category.kind, category.value)}</span>
        <button onClick={startEdit} className="text-xs font-medium text-amber-700 hover:underline">
          edit
        </button>
        <button onClick={onDelete} className="text-xs font-medium text-red-600 hover:underline">
          remove
        </button>
      </div>
    </li>
  );
}
