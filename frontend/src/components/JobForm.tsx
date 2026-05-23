"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

const MODELS = [
  { value: "meta-llama/Llama-3.1-8B-Instruct", label: "Llama 3.1 8B", family: "llama" },
  { value: "meta-llama/Llama-3.2-1B-Instruct", label: "Llama 3.2 1B", family: "llama" },
  { value: "meta-llama/Llama-3.2-3B-Instruct", label: "Llama 3.2 3B", family: "llama" },
  { value: "meta-llama/Llama-3.3-70B-Instruct", label: "Llama 3.3 70B", family: "llama" },
  { value: "Qwen/Qwen3-0.6B", label: "Qwen3 0.6B", family: "qwen3" },
  { value: "Qwen/Qwen3-1.7B", label: "Qwen3 1.7B", family: "qwen3" },
  { value: "Qwen/Qwen3-4B", label: "Qwen3 4B", family: "qwen3" },
  { value: "Qwen/Qwen3-8B", label: "Qwen3 8B", family: "qwen3" },
  { value: "Qwen/Qwen3-32B", label: "Qwen3 32B", family: "qwen3" },
  { value: "google/gemma-2-2b-it", label: "Gemma 2 2B", family: "gemma" },
  { value: "google/gemma-2-9b-it", label: "Gemma 2 9B", family: "gemma" },
  { value: "google/gemma-3-1b-it", label: "Gemma 3 1B", family: "gemma" },
  { value: "google/gemma-3-4b-it", label: "Gemma 3 4B", family: "gemma" },
  { value: "google/gemma-3-12b-it", label: "Gemma 3 12B", family: "gemma" },
  { value: "__custom__", label: "カスタム (HF model ID 直接入力)", family: "custom" },
] as const;

const QUANT_METHODS = ["GPTQ", "AWQ", "SmoothQuant", "FP8"] as const;
type QuantMethod = (typeof QUANT_METHODS)[number];

const BITS_OPTIONS: Record<QuantMethod, number[]> = {
  GPTQ: [4, 8],
  AWQ: [4, 8],
  SmoothQuant: [8],
  FP8: [8],
};

const INSTANCE_TYPES = [
  "g5.xlarge",
  "g5.2xlarge",
  "g6.xlarge",
  "g6.2xlarge",
] as const;

type FormState = {
  modelPreset: string;
  customModelId: string;
  quantMethod: QuantMethod;
  bits: number;
  featurePreflight: boolean;
  featureCheckpoint: boolean;
  instanceType: string;
  region: string;
  spot: boolean;
  maxRuntimeHours: number;
};

export function JobForm() {
  const router = useRouter();
  const [form, setForm] = useState<FormState>({
    modelPreset: MODELS[0].value,
    customModelId: "",
    quantMethod: "GPTQ",
    bits: 4,
    featurePreflight: false,
    featureCheckpoint: false,
    instanceType: "g5.xlarge",
    region: "us-east-1",
    spot: false,
    maxRuntimeHours: 4,
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showGemmaTou, setShowGemmaTou] = useState(false);
  const [gemmaTouAccepted, setGemmaTouAccepted] = useState(false);

  const selectedModel = MODELS.find((m) => m.value === form.modelPreset);
  const isGemma = selectedModel?.family === "gemma";
  const isCustom = form.modelPreset === "__custom__";
  const modelId = isCustom ? form.customModelId : form.modelPreset;

  const availableBits = BITS_OPTIONS[form.quantMethod];

  function handleQuantMethodChange(method: QuantMethod) {
    const bits = BITS_OPTIONS[method].includes(form.bits)
      ? form.bits
      : BITS_OPTIONS[method][0];
    setForm((f) => ({ ...f, quantMethod: method, bits }));
  }

  function handleModelChange(value: string) {
    const model = MODELS.find((m) => m.value === value);
    const isNewGemma = model?.family === "gemma";
    setForm((f) => ({ ...f, modelPreset: value }));
    if (isNewGemma && !gemmaTouAccepted) {
      setShowGemmaTou(true);
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (isGemma && !gemmaTouAccepted) {
      setShowGemmaTou(true);
      return;
    }
    if (!modelId) {
      setError("モデルIDを入力してください");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const res = await fetch("/api/jobs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model_id: modelId,
          quant_method: form.quantMethod,
          bits: form.bits,
          feature_flags: {
            check_env_preflight: form.featurePreflight,
            checkpoint: form.featureCheckpoint,
          },
          instance_type: form.instanceType,
          region: form.region,
          spot: form.spot,
          max_runtime_hours: form.maxRuntimeHours,
        }),
      });
      if (!res.ok) {
        const data = (await res.json()) as { detail?: string };
        throw new Error(data.detail ?? `HTTP ${res.status}`);
      }
      const job = (await res.json()) as { job_id: string };
      router.push(`/jobs/${job.job_id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "送信に失敗しました");
      setSubmitting(false);
    }
  }

  return (
    <>
      {showGemmaTou && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h2 className="text-lg font-bold mb-3">Gemma Terms of Use</h2>
            <p className="text-sm text-gray-700 mb-4">
              Gemmaモデルは Google の利用規約（Gemma Terms of Use）の対象です。
              再配布制限があります。利用前に必ず規約を確認してください。
            </p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => {
                  setShowGemmaTou(false);
                  setForm((f) => ({ ...f, modelPreset: MODELS[0].value }));
                }}
                className="px-4 py-2 text-sm border rounded hover:bg-gray-50"
              >
                キャンセル
              </button>
              <button
                onClick={() => {
                  setGemmaTouAccepted(true);
                  setShowGemmaTou(false);
                }}
                className="px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                同意して続ける
              </button>
            </div>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6 max-w-2xl">
        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
            {error}
          </div>
        )}

        <section className="space-y-3">
          <h2 className="font-semibold text-gray-900">モデル</h2>
          <div>
            <label className="block text-sm text-gray-700 mb-1">プリセット</label>
            <select
              value={form.modelPreset}
              onChange={(e) => handleModelChange(e.target.value)}
              className="w-full border rounded px-3 py-2 text-sm"
            >
              {MODELS.map((m) => (
                <option key={m.value} value={m.value}>
                  {m.label}
                </option>
              ))}
            </select>
          </div>
          {isCustom && (
            <div>
              <label className="block text-sm text-gray-700 mb-1">
                HuggingFace Model ID
              </label>
              <input
                type="text"
                value={form.customModelId}
                onChange={(e) =>
                  setForm((f) => ({ ...f, customModelId: e.target.value }))
                }
                placeholder="meta-llama/Llama-3.2-3B-Instruct"
                className="w-full border rounded px-3 py-2 text-sm font-mono"
                required
              />
            </div>
          )}
          {isGemma && gemmaTouAccepted && (
            <p className="text-xs text-amber-600 bg-amber-50 px-3 py-2 rounded">
              Gemma TOU に同意済みです。再配布には制限があります。
            </p>
          )}
        </section>

        <section className="space-y-3">
          <h2 className="font-semibold text-gray-900">量子化設定</h2>
          <div>
            <label className="block text-sm text-gray-700 mb-1">量子化方式</label>
            <div className="flex gap-2 flex-wrap">
              {QUANT_METHODS.map((m) => (
                <button
                  key={m}
                  type="button"
                  onClick={() => handleQuantMethodChange(m)}
                  className={`px-3 py-1.5 rounded border text-sm ${
                    form.quantMethod === m
                      ? "bg-blue-600 text-white border-blue-600"
                      : "border-gray-300 hover:bg-gray-50"
                  }`}
                >
                  {m.toUpperCase()}
                </button>
              ))}
            </div>
          </div>
          <div>
            <label className="block text-sm text-gray-700 mb-1">ビット数</label>
            <div className="flex gap-2">
              {[4, 8].map((b) => {
                const disabled = !availableBits.includes(b);
                return (
                  <button
                    key={b}
                    type="button"
                    disabled={disabled}
                    onClick={() => setForm((f) => ({ ...f, bits: b }))}
                    className={`px-3 py-1.5 rounded border text-sm ${
                      form.bits === b
                        ? "bg-blue-600 text-white border-blue-600"
                        : disabled
                          ? "border-gray-200 text-gray-300 cursor-not-allowed"
                          : "border-gray-300 hover:bg-gray-50"
                    }`}
                  >
                    {b === 4 ? "INT4" : form.quantMethod === "FP8" ? "FP8" : "INT8"}
                  </button>
                );
              })}
            </div>
            {form.quantMethod === "FP8" && (
              <p className="text-xs text-gray-500 mt-1">FP8 は bits=8 のみです</p>
            )}
          </div>
        </section>

        <section className="space-y-3">
          <h2 className="font-semibold text-gray-900">未公開機能</h2>
          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={form.featurePreflight}
              onChange={(e) =>
                setForm((f) => ({ ...f, featurePreflight: e.target.checked }))
              }
              className="w-4 h-4"
            />
            <span className="text-sm">
              check-env-preflight を有効化
              <span className="ml-2 text-xs text-gray-500">
                (sotanengel:feature/check-env-preflight)
              </span>
            </span>
          </label>
          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={form.featureCheckpoint}
              onChange={(e) =>
                setForm((f) => ({ ...f, featureCheckpoint: e.target.checked }))
              }
              className="w-4 h-4"
            />
            <span className="text-sm">
              checkpoint を有効化
              <span className="ml-2 text-xs text-gray-500">
                (sotanengel:feature/checkpoint)
              </span>
            </span>
          </label>
        </section>

        <section className="space-y-3">
          <h2 className="font-semibold text-gray-900">EC2 設定</h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-700 mb-1">インスタンスタイプ</label>
              <select
                value={form.instanceType}
                onChange={(e) => setForm((f) => ({ ...f, instanceType: e.target.value }))}
                className="w-full border rounded px-3 py-2 text-sm"
              >
                {INSTANCE_TYPES.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm text-gray-700 mb-1">リージョン</label>
              <select
                value={form.region}
                onChange={(e) => setForm((f) => ({ ...f, region: e.target.value }))}
                className="w-full border rounded px-3 py-2 text-sm"
              >
                <option value="us-east-1">us-east-1</option>
                <option value="us-west-2">us-west-2</option>
              </select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-700 mb-1">最大実行時間 (時間)</label>
              <input
                type="number"
                min={1}
                max={24}
                value={form.maxRuntimeHours}
                onChange={(e) =>
                  setForm((f) => ({ ...f, maxRuntimeHours: Number(e.target.value) }))
                }
                className="w-full border rounded px-3 py-2 text-sm"
              />
            </div>
            <div className="flex items-end pb-1">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={form.spot}
                  onChange={(e) => setForm((f) => ({ ...f, spot: e.target.checked }))}
                  className="w-4 h-4"
                />
                <span className="text-sm">Spot インスタンス使用</span>
              </label>
            </div>
          </div>
        </section>

        <button
          type="submit"
          disabled={submitting || (isGemma && !gemmaTouAccepted)}
          className="px-6 py-2.5 bg-blue-600 text-white rounded font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {submitting ? "送信中..." : "ジョブを投入する"}
        </button>
      </form>
    </>
  );
}
