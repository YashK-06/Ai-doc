export default function StatusChip({ ok, children, title }) {
  let style = "border-zinc-700 bg-zinc-800/60 text-zinc-400";
  if (ok === true) style = "border-emerald-800 bg-emerald-950/50 text-emerald-400";
  if (ok === false) style = "border-red-900 bg-red-950/40 text-red-400";

  return (
    <span
      title={title}
      className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium ${style}`}
    >
      {children}
    </span>
  );
}
