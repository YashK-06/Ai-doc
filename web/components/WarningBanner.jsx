export default function WarningBanner({ warnings }) {
  if (!warnings || warnings.length === 0) {
    return (
      <div className="rounded-lg border border-emerald-900 bg-emerald-950/40 px-4 py-3 text-sm text-emerald-400">
        No validation warnings — all checks passed.
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-amber-900 bg-amber-950/40 px-4 py-3">
      <p className="mb-1.5 text-sm font-medium text-amber-400">
        {warnings.length} validation warning{warnings.length > 1 ? "s" : ""}
      </p>
      <ul className="list-inside list-disc space-y-0.5 text-sm text-amber-300/90">
        {warnings.map((warning, index) => (
          <li key={index}>{warning}</li>
        ))}
      </ul>
    </div>
  );
}
