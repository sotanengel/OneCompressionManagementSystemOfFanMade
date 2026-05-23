import { JobTable } from "@/components/JobTable";

export default function JobsPage() {
  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">ジョブ一覧</h1>
        <a
          href="/new-job"
          className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
        >
          新規ジョブ投入
        </a>
      </div>
      <JobTable />
    </div>
  );
}
