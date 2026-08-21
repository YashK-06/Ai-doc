export default function FieldCard({ field, value, expected }) {
  const hasExpected = expected !== undefined;
  const match = hasExpected && value === expected;

  return (
    <div
      className={`rounded-lg border bg-zinc-900 p-3 ${
        !hasExpected
          ? "border-zinc-800"
          : match
            ? "border-emerald-900"
            : "border-red-900"
      }`}
    >
      <p className="text-xs font-medium uppercase tracking-wider text-zinc-500">
        {field}
      </p>
      <p className={`mt-1 text-sm ${value == null ? "text-zinc-600 italic" : "text-zinc-100"}`}>
        {value == null ? "null" : value}
      </p>

      {hasExpected && (
        <div className="mt-2 border-t border-zinc-800 pt-2">
          <div className="flex items-start justify-between gap-2">
            <div className="min-w-0">
              <p className="text-[10px] uppercase tracking-wider text-zinc-600">
                Ground truth
              </p>
              <p className="truncate text-xs text-zinc-400" title={expected ?? "null"}>
                {expected == null ? "null" : expected}
              </p>
            </div>
            <span className={match ? "text-emerald-500" : "text-red-500"}>
              {match ? "✓" : "✗"}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
