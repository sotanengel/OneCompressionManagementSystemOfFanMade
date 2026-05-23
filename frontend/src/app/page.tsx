import Link from "next/link";

export default function Home() {
  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-6">OneCompression 管理システム</h1>
      <div className="flex gap-4">
        <Link
          href="/jobs"
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          ジョブ一覧
        </Link>
        <Link
          href="/new-job"
          className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
        >
          新規ジョブ投入
        </Link>
        <Link
          href="/dashboard"
          className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700"
        >
          コストダッシュボード
        </Link>
      </div>
    </div>
  );
}
