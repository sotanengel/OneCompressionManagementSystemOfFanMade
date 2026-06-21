"use client";

import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { apiFetch } from "@/lib/api";

interface ThroughputPoint {
  date: string;
  count: number;
}

interface FailureReason {
  reason: string;
  count: number;
}

interface QueueDepth {
  pending: number;
  ec2_launching: number;
  running: number;
}

interface JobStats {
  period: string;
  total_jobs: number;
  status_counts: Record<string, number>;
  queue_depth: QueueDepth;
  throughput: ThroughputPoint[];
  avg_duration_sec_by_method: Record<string, number>;
  failure_reasons: FailureReason[];
}

const STATUS_COLORS: Record<string, string> = {
  pending: "#facc15",
  ec2_launching: "#60a5fa",
  running: "#34d399",
  uploading: "#a78bfa",
  syncing: "#a78bfa",
  completed: "#22d3ee",
  failed: "#ef4444",
  cancelled: "#9ca3af",
};

function StatCard({
  label,
  value,
  accent,
}: {
  label: string;
  value: string | number;
  accent?: string;
}) {
  return (
    <div className="rounded-lg border border-gray-700 bg-gray-800 p-4">
      <div className="text-xs uppercase tracking-wide text-gray-400">{label}</div>
      <div
        className="mt-1 text-2xl font-bold"
        style={{ color: accent ?? "#f9fafb" }}
      >
        {value}
      </div>
    </div>
  );
}

function formatSeconds(seconds: number): string {
  if (seconds < 60) return `${seconds.toFixed(0)}s`;
  if (seconds < 3600) return `${(seconds / 60).toFixed(1)}m`;
  return `${(seconds / 3600).toFixed(2)}h`;
}

export function JobStatsPanel({ period }: { period: string }) {
  const [stats, setStats] = useState<JobStats | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    setError(null);
    apiFetch(`/api/stats/jobs?period=${period}`)
      .then(async (res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return (await res.json()) as JobStats;
      })
      .then(setStats)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [period]);

  if (loading) {
    return <p className="text-center text-gray-400">Loading job stats…</p>;
  }
  if (error) {
    return (
      <div className="rounded-lg border border-red-700 bg-red-900/30 p-4 text-red-400">
        {error}
      </div>
    );
  }
  if (!stats) return null;

  const completed = stats.status_counts.completed ?? 0;
  const failed = stats.status_counts.failed ?? 0;
  const finished = completed + failed;
  const failureRate = finished > 0 ? (failed / finished) * 100 : 0;
  const active =
    stats.queue_depth.pending +
    stats.queue_depth.ec2_launching +
    stats.queue_depth.running;

  const statusData = Object.entries(stats.status_counts)
    .filter(([, count]) => count > 0)
    .map(([status, count]) => ({
      name: status,
      value: count,
      fill: STATUS_COLORS[status] ?? "#9ca3af",
    }));

  const durationData = Object.entries(stats.avg_duration_sec_by_method).map(
    ([method, seconds]) => ({
      method,
      seconds: Math.round(seconds),
    }),
  );

  return (
    <div className="space-y-8">
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard label="Total jobs" value={stats.total_jobs} />
        <StatCard label="Active" value={active} accent="#34d399" />
        <StatCard label="Completed" value={completed} accent="#22d3ee" />
        <StatCard
          label="Failure rate"
          value={`${failureRate.toFixed(1)}%`}
          accent={failureRate > 20 ? "#ef4444" : "#f9fafb"}
        />
      </div>

      <div className="rounded-lg border border-gray-700 bg-gray-800 p-6">
        <h3 className="mb-4 text-lg font-semibold text-white">
          Completed jobs per day
        </h3>
        {stats.throughput.length === 0 ? (
          <p className="text-sm text-gray-400">
            No completed jobs in this period.
          </p>
        ) : (
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={stats.throughput} margin={{ left: 16 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="date" tick={{ fill: "#9ca3af", fontSize: 12 }} />
              <YAxis allowDecimals={false} tick={{ fill: "#9ca3af", fontSize: 12 }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#1f2937",
                  border: "1px solid #374151",
                }}
                labelStyle={{ color: "#f9fafb" }}
              />
              <Line type="monotone" dataKey="count" stroke="#22d3ee" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        <div className="rounded-lg border border-gray-700 bg-gray-800 p-6">
          <h3 className="mb-4 text-lg font-semibold text-white">
            Status distribution
          </h3>
          {statusData.length === 0 ? (
            <p className="text-sm text-gray-400">No jobs in this period.</p>
          ) : (
            <ResponsiveContainer width="100%" height={240}>
              <PieChart>
                <Pie
                  data={statusData}
                  dataKey="value"
                  nameKey="name"
                  innerRadius={45}
                  outerRadius={90}
                  paddingAngle={2}
                >
                  {statusData.map((d) => (
                    <Cell key={d.name} fill={d.fill} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#1f2937",
                    border: "1px solid #374151",
                  }}
                  labelStyle={{ color: "#f9fafb" }}
                />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="rounded-lg border border-gray-700 bg-gray-800 p-6">
          <h3 className="mb-4 text-lg font-semibold text-white">
            Top failure reasons
          </h3>
          {stats.failure_reasons.length === 0 ? (
            <p className="text-sm text-gray-400">No recorded failures.</p>
          ) : (
            <ResponsiveContainer width="100%" height={240}>
              <BarChart
                data={stats.failure_reasons}
                layout="vertical"
                margin={{ left: 24, right: 24 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis type="number" allowDecimals={false} tick={{ fill: "#9ca3af", fontSize: 12 }} />
                <YAxis
                  type="category"
                  dataKey="reason"
                  tick={{ fill: "#9ca3af", fontSize: 11 }}
                  width={120}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#1f2937",
                    border: "1px solid #374151",
                  }}
                  labelStyle={{ color: "#f9fafb" }}
                />
                <Bar dataKey="count" fill="#ef4444" />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {durationData.length > 0 && (
        <div className="rounded-lg border border-gray-700 bg-gray-800 p-6">
          <h3 className="mb-4 text-lg font-semibold text-white">
            Average duration by method
          </h3>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-700 text-gray-400">
                <th className="py-2 text-left">Method</th>
                <th className="py-2 text-right">Avg duration</th>
              </tr>
            </thead>
            <tbody>
              {durationData.map((d) => (
                <tr key={d.method} className="border-b border-gray-700/50">
                  <td className="py-2 text-white">{d.method}</td>
                  <td className="py-2 text-right text-gray-300">
                    {formatSeconds(d.seconds)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
