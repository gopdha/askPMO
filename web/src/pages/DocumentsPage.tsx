import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState, type DragEvent } from "react";
import { getJson, uploadFiles, type DocumentOut, type IngestJobOut, type UploadItem } from "../api/client";

// Walk a dropped directory tree, keeping each file's path relative to the dropped folder's parent.
async function collectEntry(entry: FileSystemEntry, prefix: string, out: UploadItem[]): Promise<void> {
  if (entry.isFile) {
    const file = await new Promise<File>((resolve, reject) => (entry as FileSystemFileEntry).file(resolve, reject));
    out.push({ file, relPath: prefix + file.name });
    return;
  }
  const reader = (entry as FileSystemDirectoryEntry).createReader();
  let batch: FileSystemEntry[];
  do {
    batch = await new Promise<FileSystemEntry[]>((resolve, reject) => reader.readEntries(resolve, reject));
    for (const child of batch) await collectEntry(child, prefix + entry.name + "/", out);
  } while (batch.length > 0);
}

// Strip a single top-level folder (e.g. "corpus/") so paths start at the numbered folders.
function stripRoot(items: UploadItem[]): UploadItem[] {
  const roots = new Set(items.map((item) => item.relPath.split("/")[0]));
  if (roots.size !== 1 || items.some((item) => !item.relPath.includes("/"))) return items;
  const [root] = [...roots];
  if (/^\d{2}_/.test(root)) return items;
  return items.map((item) => ({ ...item, relPath: item.relPath.slice(root.length + 1) }));
}

function JobProgress({ jobId }: { jobId: string }) {
  const queryClient = useQueryClient();
  const { data: job } = useQuery({
    queryKey: ["ingest-job", jobId],
    queryFn: () => getJson<IngestJobOut>("/ingest-jobs/" + jobId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === "succeeded" || status === "failed") {
        void queryClient.invalidateQueries({ queryKey: ["documents"] });
        return false;
      }
      return 3000;
    },
  });
  if (!job) return null;
  const total = job.document_ids.length || 1;
  const percent = Math.round((100 * job.documents_done) / total);
  const barColor = job.status === "failed" ? "bg-red-500" : job.status === "succeeded" ? "bg-emerald-500" : "bg-sky-500";
  return (
    <div className="mt-4 rounded-md border border-slate-200 p-3 text-sm">
      <div className="mb-1 flex justify-between">
        <span>
          Ingest job <code className="text-xs">{job.id.slice(0, 8)}</code>: <strong>{job.status}</strong>
        </span>
        <span>
          {job.documents_done}/{job.document_ids.length} documents · {job.chunks_written} chunks
        </span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded bg-slate-200">
        <div className={"h-2 " + barColor} style={{ width: percent + "%" }} />
      </div>
      {job.error && <p className="mt-2 text-xs text-red-700">{job.error}</p>}
    </div>
  );
}

export default function DocumentsPage() {
  const [jobId, setJobId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const { data: documents } = useQuery({
    queryKey: ["documents"],
    queryFn: () => getJson<DocumentOut[]>("/documents"),
  });

  async function send(items: UploadItem[]) {
    if (items.length === 0) return;
    setError(null);
    setUploading(true);
    try {
      const result = await uploadFiles(stripRoot(items));
      setJobId(result.job_id);
    } catch (exc) {
      setError(String(exc));
    } finally {
      setUploading(false);
    }
  }

  async function onDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setDragging(false);
    const items: UploadItem[] = [];
    const entries = [...event.dataTransfer.items]
      .map((item) => item.webkitGetAsEntry())
      .filter((entry): entry is FileSystemEntry => entry !== null);
    for (const entry of entries) await collectEntry(entry, "", items);
    await send(items);
  }

  function onPick(files: FileList | null) {
    if (!files) return;
    void send([...files].map((file) => ({ file, relPath: file.webkitRelativePath || file.name })));
  }

  return (
    <div className="space-y-6">
      <section className="rounded-lg border border-slate-200 bg-white p-4">
        <h1 className="mb-3 text-xl font-semibold">Documents</h1>
        <div
          onDragOver={(event) => {
            event.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(event) => void onDrop(event)}
          className={
            "rounded-lg border-2 border-dashed p-8 text-center text-sm " +
            (dragging ? "border-sky-500 bg-sky-50" : "border-slate-300 text-slate-600")
          }
        >
          <p>Drop the corpus folder here (folder paths are preserved).</p>
          <label className="mt-3 inline-block cursor-pointer rounded-md bg-slate-900 px-3 py-1.5 text-white">
            Choose folder
            <input
              type="file"
              className="hidden"
              multiple
              // @ts-expect-error non-standard attribute for folder selection
              webkitdirectory=""
              onChange={(event) => onPick(event.target.files)}
            />
          </label>
          {uploading && <p className="mt-2">Uploading…</p>}
          {error && <p className="mt-2 text-red-700">{error}</p>}
        </div>
        {jobId && <JobProgress jobId={jobId} />}
      </section>

      <section className="rounded-lg border border-slate-200 bg-white p-4">
        <h2 className="mb-3 font-semibold">Indexed documents ({documents?.length ?? 0})</h2>
        <table className="w-full text-left text-sm">
          <thead className="border-b border-slate-200 text-xs uppercase text-slate-500">
            <tr>
              <th className="py-2">Path</th>
              <th>Type</th>
              <th>Date</th>
              <th>Week</th>
              <th className="text-right">Chunks</th>
              <th className="text-right">Status</th>
            </tr>
          </thead>
          <tbody>
            {documents?.map((doc) => (
              <tr key={doc.id} className="border-b border-slate-100">
                <td className="py-1.5 font-mono text-xs">{doc.rel_path}</td>
                <td>{doc.doc_type ?? "—"}</td>
                <td>{doc.doc_date ?? "—"}</td>
                <td>{doc.week ?? "—"}</td>
                <td className="text-right">{doc.chunk_count}</td>
                <td className="text-right">
                  <span
                    className={
                      "rounded px-1.5 py-0.5 text-xs " +
                      (doc.status === "indexed"
                        ? "bg-emerald-100 text-emerald-800"
                        : doc.status === "failed"
                          ? "bg-red-100 text-red-800"
                          : "bg-slate-100 text-slate-700")
                    }
                  >
                    {doc.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
