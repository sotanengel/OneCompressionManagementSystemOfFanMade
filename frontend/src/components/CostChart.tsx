"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

interface CostSummary {
  total_usd: number;
  by_model: Record<string, number>;
  budget_warning: boolean;
}

interface CostChartProps {
  summary: CostSummary;
}

const BUDGET_LIMIT = 100;
const BUDGET_WARNING = 50;

const MODEL_COLORS = [
  "#6366f1",
  "#22d3ee",
  "#a78bfa",
  "#34d399",
  "#f59e0b",
  "#fb7185",
];

export function CostChart({ summary }: CostChartProps) {
  const byModelData = Object.entries(summary.by_model).map(
    ([model, cost], i) => ({
      model: model.split("/").pop() ?? model,
      cost: Number(cost.toFixed(2)),
      fill: MODEL_COLORS[i % MODEL_COLORS.length],
    })
  );

  const usedPct = Math.min((summary.total_usd / BUDGET_LIMIT) * 100, 100);
  const gaugeColor =
    summary.total_usd >= BUDGET_WARNING
      ? summary.total_usd >= BUDGET_LIMIT
        ? "#ef4444"
        : "#f59e0b"
      : "#22d3ee";

  return (
    <div className="space-y-8">
      {/* Budget gauge */}
      <div className="rounded-lg border border-gray-700 bg-gray-800 p-6">
        <h2 className="mb-4 text-lg font-semibold text-white">
          Budget Usage (${summary.total_usd.toFixed(2)} / ${BUDGET_LIMIT})
        </h2>
        <div className="h-4 w-full overflow-hidden rounded-full bg-gray-700">
          <div
            className="h-full rounded-full transition-all"
            style={{ width: `${usedPct}%`, backgroundColor: gaugeColor }}
          />
        </div>
        {summary.budget_warning && (
          <p className="mt-2 text-sm font-medium text-yellow-400">
            ⚠ Budget warning: cumulative cost exceeds ${BUDGET_WARNING}
          </p>
        )}
      </div>

      {/* Per-model breakdown */}
      {byModelData.length > 0 && (
        <div className="rounded-lg border border-gray-700 bg-gray-800 p-6">
          <h2 className="mb-4 text-lg font-semibold text-white">
            Cost by Model (USD)
          </h2>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={byModelData} margin={{ left: 16 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="model" tick={{ fill: "#9ca3af", fontSize: 12 }} />
              <YAxis
                tick={{ fill: "#9ca3af", fontSize: 12 }}
                tickFormatter={(v) => `$${v}`}
              />
              <Tooltip
                formatter={(value: number) => [`$${value}`, "Cost"]}
                contentStyle={{
                  backgroundColor: "#1f2937",
                  border: "1px solid #374151",
                }}
                labelStyle={{ color: "#f9fafb" }}
              />
              <Legend />
              <Bar dataKey="cost" name="Cost (USD)">
                {byModelData.map((entry, i) => (
                  <Cell key={i} fill={entry.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
