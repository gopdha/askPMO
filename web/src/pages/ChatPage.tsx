import { useQuery } from "@tanstack/react-query";
import { getJson, type ProfileOut } from "../api/client";

export default function ChatPage() {
  const { data: profiles } = useQuery({
    queryKey: ["profiles"],
    queryFn: () => getJson<ProfileOut[]>("/profiles"),
  });
  return (
    <div className="grid grid-cols-5 gap-6">
      <section className="col-span-3 rounded-lg border border-slate-200 bg-white p-4">
        <h1 className="mb-2 text-xl font-semibold">Chat</h1>
        <p className="text-sm text-slate-600">Ask questions about Project Atlas (arrives in P2).</p>
        <p className="mt-4 text-xs text-slate-500">
          Profiles: {profiles?.map((profile) => profile.name).join(", ") ?? "…"}
        </p>
      </section>
      <aside className="col-span-2 rounded-lg border border-slate-200 bg-white p-4">
        <h2 className="mb-2 font-semibold">Under the hood</h2>
        <p className="text-sm text-slate-600">Stage traces appear here.</p>
      </aside>
    </div>
  );
}
