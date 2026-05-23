import type { Metadata } from "next";
import "./globals.css";
import { AmplifyProvider } from "@/components/AmplifyProvider";

export const metadata: Metadata = {
  title: "OneCompression Management System",
  description: "LLM quantization pipeline management",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ja">
      <body>
        <AmplifyProvider>{children}</AmplifyProvider>
      </body>
    </html>
  );
}
