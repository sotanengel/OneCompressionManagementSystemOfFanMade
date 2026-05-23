"use client";

import { confirmSignUp, resendSignUpCode } from "aws-amplify/auth";
import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";

export default function VerifyPage() {
  const router = useRouter();
  const params = useSearchParams();
  const email = params.get("email") ?? "";

  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [resent, setResent] = useState(false);
  const [loading, setLoading] = useState(false);

  async function handleVerify(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await confirmSignUp({ username: email, confirmationCode: code });
      router.push("/jobs");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Verification failed");
    } finally {
      setLoading(false);
    }
  }

  async function handleResend() {
    setResent(false);
    try {
      await resendSignUpCode({ username: email });
      setResent(true);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to resend code");
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-950">
      <div className="w-full max-w-sm rounded-lg border border-gray-700 bg-gray-800 p-8">
        <h1 className="mb-2 text-xl font-semibold text-white">
          Verify your email
        </h1>
        <p className="mb-6 text-sm text-gray-400">
          We sent a 6-digit code to <span className="text-white">{email}</span>.
          Enter it below to confirm your account.
        </p>

        <form onSubmit={handleVerify} className="space-y-4">
          <input
            type="text"
            inputMode="numeric"
            pattern="[0-9]{6}"
            maxLength={6}
            placeholder="123456"
            value={code}
            onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
            required
            className="w-full rounded border border-gray-600 bg-gray-900 px-3 py-2 text-center text-2xl tracking-widest text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />

          {error && <p className="text-sm text-red-400">{error}</p>}
          {resent && (
            <p className="text-sm text-green-400">Code resent — check your email.</p>
          )}

          <button
            type="submit"
            disabled={loading || code.length < 6}
            className="w-full rounded bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50"
          >
            {loading ? "Verifying…" : "Verify"}
          </button>
        </form>

        <button
          onClick={handleResend}
          className="mt-4 w-full text-sm text-gray-400 hover:text-white"
        >
          Resend code
        </button>
      </div>
    </div>
  );
}
