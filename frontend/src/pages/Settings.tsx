import { useEffect, useState, type FormEvent } from "react";
import { useMutation, useQuery } from "urql";

import { Button, Card, ErrorNote, Field, Input, Spinner } from "../components/ui";
import { BUDGET_SETTINGS, UPDATE_BUDGET_SETTINGS } from "../gql/operations";

type SettingsData = {
  id: string;
  savingsPct: string;
  retirement401kPct: string;
  hsaPerCycle: string;
};

export default function Settings() {
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
    <div className="mx-auto max-w-lg space-y-6">
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
