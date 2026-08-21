export default function ModelChip({ health }) {
  if (!health) return null;

  const { model_ready, model_used, hint } = health;

  let dot = "bg-red-500";
  let label = "no model installed";

  if (model_ready) {
    dot = "bg-emerald-500";
    label = `local · ${model_used}`;
  } else if (model_used) {
    dot = "bg-amber-500";
    label = `cloud · ${model_used}`;
  }

  return (
    <span
      title={hint || label}
      className="inline-flex items-center gap-1.5 rounded-full border border-zinc-700 bg-zinc-800/60 px-2.5 py-0.5 text-xs font-medium text-zinc-300"
    >
      <span className={`h-1.5 w-1.5 rounded-full ${dot}`} />
      {label}
    </span>
  );
}
