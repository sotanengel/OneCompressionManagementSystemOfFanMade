"use client";

import { useEffect, useState } from "react";

import { CostChart } from "@/components/CostChart";
import { JobStatsPanel } from "@/components/JobStatsPanel";
import { apiFetch } from "@/lib/api";

interface CostSummary {
  total_usd: number;
  by_model: Record<string, number>;
  budget_warning: boolean;
}

type Period = "week" | "month" | "all";
type Tab = "cost" | "jobs";

async function fetchSummary(period: Period): Promise<CostSummary> {
  const res = await apiFetch(`/api/cost/summary?period=${period}&group_by=model`);
  if (!res.ok) throw new Error(`Failed to fetch cost summary: ${res.status}`);
  return res.json();
}

export default function DashboardPage() {
  const [period, setPeriod] = useState<Period>("week");
  const [tab, setTab] = useState<Tab>("cost");
  const [summary, setSummary] = useState<CostSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (tab !== "cost") return;
    setLoading(true);
    setError(null);
    fetchSummary(period)
      .then(setSummary)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [period, tab]);

  return (
    <div className="mx-auto max-w-4xl px-4 py-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white">Dashboard</h1>
        <div className="flex gap-2">
          {(["week", "month", "all"] as Period[]).map((p) => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              className={`rounded px-4 py-1.5 text-sm font-medium transition-colors ${
                period === p
                  ? "bg-indigo-600 text-white"
                  : "bg-gray-700 text-gray-300 hover:bg-gray-600"
              }`}
            >
              {p === "week" ? "7 days" : p === "month" ? "30 days" : "All time"}
            </button>
          ))}
        </div>
      </div>

      <div className="mb-6 flex border-b border-gray-700">
        {(["cost", "jobs"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm font-medium transition-colors ${
              tab === t
                ? "border-b-2 border-indigo-500 text-white"
                : "text-gray-400 hover:text-gray-200"
            }`}
          >
            {t === "cost" ? "コスト" : "ジョブ"}
          </button>
        ))}
      </div>

      {tab === "cost" && (
        <>
          {loading && (
            <p className="text-center text-gray-400">Loading cost data…</p>
          )}
          {error && (
            <div className="rounded-lg border border-red-700 bg-red-900/30 p-4 text-red-400">
              {error}
            </div>
          )}
          {summary && !loading && <CostChart summary={summary} />}
        </>
      )}

      {tab === "jobs" && <JobStatsPanel period={period} />}
    </div>
  );
}
