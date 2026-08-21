"use client";

import { Fragment, useEffect, useState } from "react";
import { FIELDS, evaluateDocument, fetchDocuments } from "@/lib/api";

function AccuracyBar({ value }) {
  const pct = Math.max(0, Math.min(100, value ?? 0));
  const color =
    pct >= 87.5 ? "bg-emerald-500" : pct >= 50 ? "bg-amber-500" : "bg-red-500";
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-28 overflow-hidden rounded-full bg-zinc-800">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="w-12 text-right text-xs text-zinc-400">
        {pct.toFixed(0)}%
      </span>
    </div>
  );
}

const STATUS_ICON = {
  pending: <span className="text-zinc-600">·</span>,
  running: (
    <span className="inline-block h-3 w-3 animate-spin rounded-full border border-zinc-600 border-t-emerald-500" />
  ),
  done: <span className="text-emerald-500">✓</span>,
  error: <span className="text-red-500">✗</span>,
};

export default function EvaluatePage() {
  const [documents, setDocuments] = useState([]);
  const [rows, setRows] = useState({});
  const [running, setRunning] = useState(false);
  const [overall, setOverall] = useState(null);
  const [expanded, setExpanded] = useState(null);
  const [loadError, setLoadError] = useState(null);

  useEffect(() => {
    fetchDocuments()
      .then((data) => setDocuments(data.documents))
      .catch((err) => setLoadError(err.message));
  }, []);

  async function runAll() {
    setRunning(true);
    setOverall(null);
    setExpanded(null);

    const names = documents.map((doc) => doc.name);
    setRows(Object.fromEntries(names.map((name) => [name, { status: "pending" }])));

    let passedSum = 0;
    let totalSum = 0;

    for (const name of names) {
      setRows((prev) => ({ ...prev, [name]: { status: "running" } }));
      try {
        const data = await evaluateDocument(name);
        passedSum += data.passed;
        totalSum += data.total;
        setRows((prev) => ({ ...prev, [name]: { status: "done", ...data } }));
        setOverall({ passed: passedSum, total: totalSum });
      } catch (err) {
        setRows((prev) => ({
          ...prev,
          [name]: { status: "error", error: err.message },
        }));
      }
    }

    setRunning(false);
  }

  const names = documents.map((doc) => doc.name);
  const doneCount = names.filter((n) => rows[n]?.status === "done").length;

  return (
    <div className="pt-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">Evaluation</h1>
          <p className="mt-1 text-sm text-zinc-400">
            Run the extraction pipeline on every dataset document and compare
            against ground-truth labels.
          </p>
        </div>
        <button
          onClick={runAll}
          disabled={running || documents.length === 0}
          className="rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-emerald-500 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {running ? "Running…" : "Run full evaluation"}
        </button>
      </div>

      {loadError && (
        <div className="mt-4 rounded-lg border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-400">
          {loadError}
        </div>
      )}

      {/* Summary */}
      <div className="mt-6 grid grid-cols-3 gap-4">
        <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-4">
          <p className="text-xs uppercase tracking-wider text-zinc-500">
            Overall accuracy
          </p>
          <p className="mt-1 text-2xl font-semibold">
            {overall
              ? `${((overall.passed / overall.total) * 100).toFixed(1)}%`
              : running
                ? "…"
                : "—"}
          </p>
          {overall && (
            <p className="mt-0.5 text-xs text-zinc-500">
              {overall.passed}/{overall.total} fields correct
            </p>
          )}
        </div>
        <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-4">
          <p className="text-xs uppercase tracking-wider text-zinc-500">
            Documents evaluated
          </p>
          <p className="mt-1 text-2xl font-semibold">
            {doneCount}
            <span className="text-base text-zinc-500">/{names.length}</span>
          </p>
        </div>
        <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-4">
          <p className="text-xs uppercase tracking-wider text-zinc-500">
            Fields passed
          </p>
          <p className="mt-1 text-2xl font-semibold">
            {overall ? overall.passed : "—"}
            <span className="text-base text-zinc-500">
              /{overall ? overall.total : names.length * FIELDS.length}
            </span>
          </p>
        </div>
      </div>

      {/* Table */}
      <div className="mt-6 overflow-hidden rounded-lg border border-zinc-800">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-zinc-800 bg-zinc-900/80 text-left text-xs uppercase tracking-wider text-zinc-500">
              <th className="px-4 py-2.5 font-medium">Document</th>
              <th className="px-4 py-2.5 font-medium">Status</th>
              <th className="px-4 py-2.5 font-medium">Accuracy</th>
              <th className="px-4 py-2.5 font-medium">Fields</th>
            </tr>
          </thead>
          <tbody>
            {names.map((name) => {
              const row = rows[name];
              return (
                <Fragment key={name}>
                  <tr
                    onClick={() =>
                      row?.status === "done" &&
                      setExpanded(expanded === name ? null : name)
                    }
                    className={`border-b border-zinc-800/60 last:border-0 ${
                      row?.status === "done"
                        ? "cursor-pointer hover:bg-zinc-900"
                        : ""
                    }`}
                  >
                    <td className="px-4 py-2.5 font-medium text-zinc-200">
                      {name}
                    </td>
                    <td className="px-4 py-2.5">
                      <span className="flex items-center gap-2">
                        {STATUS_ICON[row?.status || "pending"]}
                        <span className="text-xs text-zinc-500">
                          {row?.error || row?.status || "pending"}
                        </span>
                      </span>
                    </td>
                    <td className="px-4 py-2.5">
                      {row?.status === "done" ? (
                        <AccuracyBar value={row.accuracy} />
                      ) : (
                        <span className="text-zinc-600">—</span>
                      )}
                    </td>
                    <td className="px-4 py-2.5 text-zinc-400">
                      {row?.status === "done" ? `${row.passed}/${row.total}` : "—"}
                    </td>
                  </tr>
                  {expanded === name && row?.results && (
                    <tr className="border-b border-zinc-800/60 last:border-0">
                      <td colSpan={4} className="bg-zinc-900/60 px-4 py-3">
                        <div className="grid grid-cols-4 gap-2">
                          {row.results.map((fieldResult) => (
                            <div
                              key={fieldResult.field}
                              className={`rounded-md border px-2.5 py-1.5 ${
                                fieldResult.match
                                  ? "border-emerald-900 bg-emerald-950/30"
                                  : "border-red-900 bg-red-950/30"
                              }`}
                            >
                              <p className="flex items-center justify-between text-[10px] uppercase tracking-wider text-zinc-500">
                                {fieldResult.field}
                                <span
                                  className={
                                    fieldResult.match
                                      ? "text-emerald-500"
                                      : "text-red-500"
                                  }
                                >
                                  {fieldResult.match ? "✓" : "✗"}
                                </span>
                              </p>
                              {!fieldResult.match && (
                                <p className="mt-1 truncate text-[11px] text-zinc-400">
                                  got:{" "}
                                  {fieldResult.predicted == null
                                    ? "null"
                                    : fieldResult.predicted}
                                </p>
                              )}
                            </div>
                          ))}
                        </div>
                      </td>
                    </tr>
                  )}
                </Fragment>
              );
            })}
            {names.length === 0 && !loadError && (
              <tr>
                <td colSpan={4} className="px-4 py-6 text-center text-zinc-500">
                  Loading documents…
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {names.length > 0 && !running && !overall && (
        <p className="mt-3 text-xs text-zinc-500">
          Each document runs sequentially through the LLM — expect roughly a
          minute per document.
        </p>
      )}
    </div>
  );
}
