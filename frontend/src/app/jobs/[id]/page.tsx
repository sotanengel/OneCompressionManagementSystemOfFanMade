export default function JobDetailPage({ params }: { params: { id: string } }) {
  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">ジョブ詳細: {params.id}</h1>
      <p className="text-gray-500">W5 で SSE ログストリームを実装予定</p>
    </div>
  );
}
