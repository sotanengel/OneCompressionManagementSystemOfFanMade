import { JobForm } from "@/components/JobForm";

export default function NewJobPage() {
  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-6">新規ジョブ投入</h1>
      <JobForm />
    </div>
  );
}
