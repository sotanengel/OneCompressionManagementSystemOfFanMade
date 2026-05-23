"use client";

import { Authenticator } from "@aws-amplify/ui-react";
import "@aws-amplify/ui-react/styles.css";
import { configureAmplify } from "@/lib/auth";

const isDev =
  process.env.NODE_ENV === "development" &&
  !process.env.NEXT_PUBLIC_COGNITO_USER_POOL_ID;

if (!isDev) {
  configureAmplify();
}

function DevNav({ children }: { children: React.ReactNode }) {
  return (
    <div>
      <nav className="flex items-center justify-between p-4 bg-gray-900 text-white">
        <span className="font-semibold">OneCompression</span>
        <span className="text-xs text-yellow-400">開発モード（認証スキップ）</span>
      </nav>
      <main>{children}</main>
    </div>
  );
}

export function AmplifyProvider({ children }: { children: React.ReactNode }) {
  if (isDev) {
    return <DevNav>{children}</DevNav>;
  }

  return (
    <Authenticator loginMechanisms={["email"]} signUpAttributes={["email"]}>
      {({ signOut, user }) => (
        <div>
          <nav className="flex items-center justify-between p-4 bg-gray-900 text-white">
            <span className="font-semibold">OneCompression</span>
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-400">{user?.signInDetails?.loginId}</span>
              <button
                onClick={signOut}
                className="text-sm px-3 py-1 rounded bg-gray-700 hover:bg-gray-600"
              >
                サインアウト
              </button>
            </div>
          </nav>
          <main>{children}</main>
        </div>
      )}
    </Authenticator>
  );
}
