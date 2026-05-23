export default async function JobDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">ジョブ詳細: {id}</h1>
    </div>
  );
}
