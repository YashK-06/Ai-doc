"use client";

import { useEffect, useState } from "react";
import { fetchCases } from "@/lib/api";

export default function HistoryPage() {
  const [data, setData] = useState({ cases: [], error: null });
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    try {
      setData(await fetchCases());
    } catch (err) {
      setData({ cases: [], error: err.message });
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  const cases = data.cases || [];

  return (
    <div className="pt-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">History</h1>
          <p className="mt-1 text-sm text-zinc-400">
            Extraction results persisted in MongoDB (ai_doc.court_cases).
          </p>
        </div>
        <button
          onClick={load}
          disabled={loading}
          className="rounded-md border border-zinc-700 px-3 py-1.5 text-sm text-zinc-300 transition-colors hover:bg-zinc-800 disabled:opacity-50"
        >
          {loading ? "Loading…" : "Refresh"}
        </button>
      </div>

      {data.error && (
        <div className="mt-4 rounded-lg border border-amber-900 bg-amber-950/40 px-4 py-3 text-sm text-amber-400">
          MongoDB unreachable — no saved records shown.
          <span className="mt-1 block text-xs text-amber-500/70">
            {data.error}
          </span>
        </div>
      )}

      {!loading && !data.error && cases.length === 0 && (
        <div className="mt-6 flex min-h-[200px] flex-col items-center justify-center gap-2 rounded-lg border border-zinc-800 bg-zinc-900/40 text-zinc-500">
          <p className="text-sm">No saved cases yet.</p>
          <p className="text-xs">
            Run an extraction on the Extract page to store one.
          </p>
        </div>
      )}

      {cases.length > 0 && (
        <div className="mt-6 overflow-x-auto rounded-lg border border-zinc-800">
          <table className="w-full min-w-[860px] text-sm">
            <thead>
              <tr className="border-b border-zinc-800 bg-zinc-900/80 text-left text-xs uppercase tracking-wider text-zinc-500">
                <th className="px-4 py-2.5 font-medium">Case number</th>
                <th className="px-4 py-2.5 font-medium">Applicant</th>
                <th className="px-4 py-2.5 font-medium">Respondent</th>
                <th className="px-4 py-2.5 font-medium">Court</th>
                <th className="px-4 py-2.5 font-medium">Type</th>
                <th className="px-4 py-2.5 font-medium">Filed</th>
                <th className="px-4 py-2.5 font-medium">Extracted at</th>
              </tr>
            </thead>
            <tbody>
              {cases.map((record) => {
                // Support both schemas: {fields: {...}} and flat records
                const fields = record.fields || record;
                const source =
                  record.filename ||
                  record.source_document ||
                  "—";
                return (
                  <tr
                    key={record._id || record.filename}
                    className="border-b border-zinc-800/60 last:border-0 hover:bg-zinc-900"
                  >
                    <td className="px-4 py-2.5 font-medium text-zinc-200">
                      {fields.case_number ?? "—"}
                    </td>
                    <td className="px-4 py-2.5 text-zinc-300">
                      {fields.applicant_name ?? "—"}
                    </td>
                    <td className="px-4 py-2.5 text-zinc-300">
                      {fields.respondent_name ?? "—"}
                    </td>
                    <td className="px-4 py-2.5 text-zinc-300">
                      {fields.court_name ?? "—"}
                    </td>
                    <td className="px-4 py-2.5">
                      {fields.case_type ? (
                        <span className="rounded-full border border-zinc-700 px-2 py-0.5 text-xs text-zinc-400">
                          {fields.case_type}
                        </span>
                      ) : (
                        "—"
                      )}
                    </td>
                    <td className="px-4 py-2.5 text-zinc-400">
                      {fields.filing_date ?? "—"}
                    </td>
                    <td
                      className="px-4 py-2.5 text-xs text-zinc-500"
                      title={source}
                    >
                      {record.extracted_at
                        ? new Date(record.extracted_at).toLocaleString()
                        : "—"}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
