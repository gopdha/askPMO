import { useQuery } from "@tanstack/react-query";
import { getJson, type ReadyOut } from "../api/client";

export default function ReadyBanner() {
  const { data, isError } = useQuery({
    queryKey: ["ready"],
    queryFn: () => getJson<ReadyOut>("/ready"),
    refetchInterval: 15000,
  });
  if (!isError && (!data || data.ready)) return null;
  const failing = data
    ? Object.entries(data.checks)
        .filter(([, check]) => !check.ok)
        .map(([name]) => name)
    : [];
  return (
    <div className="border-b border-amber-300 bg-amber-50 px-6 py-2 text-sm text-amber-900">
      Service not ready{failing.length ? ": " + failing.join(", ") + " unavailable" : ""}.
    </div>
  );
}
