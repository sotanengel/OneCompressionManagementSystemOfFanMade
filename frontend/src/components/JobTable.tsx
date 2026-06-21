"use client";

import { useEffect, useState } from "react";

import { apiFetch } from "@/lib/api";

type Job = {
  job_id: string;
  model_id: string;
  quant_method: string;
  bits: number;
  status: string;
  created_at: string;
  estimated_cost_usd: number | null;
};

const STATUS_COLORS: Record<string, string> = {
  pending: "bg-yellow-100 text-yellow-800",
  ec2_launching: "bg-blue-100 text-blue-800",
  running: "bg-green-100 text-green-800",
  succeeded: "bg-emerald-100 text-emerald-800",
  failed: "bg-red-100 text-red-800",
  cancelled: "bg-gray-100 text-gray-800",
};

export function JobTable() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiFetch("/api/jobs")
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data) => {
        setJobs(data.items ?? []);
        setLoading(false);
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Unknown error");
        setLoading(false);
      });
  }, []);

  if (loading) return <div className="text-gray-500">読み込み中...</div>;
  if (error) return <div className="text-red-500">エラー: {error}</div>;
  if (jobs.length === 0) return <div className="text-gray-500">ジョブがありません</div>;

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse">
        <thead>
          <tr className="border-b bg-gray-50">
            <th className="text-left p-3 text-sm font-medium text-gray-700">Job ID</th>
            <th className="text-left p-3 text-sm font-medium text-gray-700">モデル</th>
            <th className="text-left p-3 text-sm font-medium text-gray-700">量子化</th>
            <th className="text-left p-3 text-sm font-medium text-gray-700">Bits</th>
            <th className="text-left p-3 text-sm font-medium text-gray-700">ステータス</th>
            <th className="text-left p-3 text-sm font-medium text-gray-700">作成日時</th>
            <th className="text-left p-3 text-sm font-medium text-gray-700">推定コスト</th>
            <th className="text-left p-3 text-sm font-medium text-gray-700">操作</th>
          </tr>
        </thead>
        <tbody>
          {jobs.map((job) => (
            <tr key={job.job_id} className="border-b hover:bg-gray-50">
              <td className="p-3 font-mono text-xs text-gray-500">
                {job.job_id.slice(0, 8)}...
              </td>
              <td className="p-3 text-sm">{job.model_id}</td>
              <td className="p-3 text-sm">{job.quant_method}</td>
              <td className="p-3 text-sm">{job.bits}</td>
              <td className="p-3">
                <span
                  className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                    STATUS_COLORS[job.status] ?? "bg-gray-100 text-gray-800"
                  }`}
                >
                  {job.status}
                </span>
              </td>
              <td className="p-3 text-sm text-gray-500">
                {new Date(job.created_at).toLocaleString("ja-JP")}
              </td>
              <td className="p-3 text-sm">
                {job.estimated_cost_usd != null
                  ? `$${job.estimated_cost_usd.toFixed(2)}`
                  : "—"}
              </td>
              <td className="p-3">
                <a
                  href={`/jobs/${job.job_id}`}
                  className="text-blue-600 hover:underline text-sm"
                >
                  詳細
                </a>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
