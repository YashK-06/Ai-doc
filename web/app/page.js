"use client";

import { useEffect, useRef, useState } from "react";
import {
  FIELDS,
  extractDocument,
  fetchDocuments,
  fetchHealth,
  uploadDocument,
} from "@/lib/api";
import FieldCard from "@/components/FieldCard";
import ModelChip from "@/components/ModelChip";
import StatusChip from "@/components/StatusChip";
import WarningBanner from "@/components/WarningBanner";

export default function ExtractPage() {
  const [documents, setDocuments] = useState([]);
  const [health, setHealth] = useState(null);
  const [selected, setSelected] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [showJson, setShowJson] = useState(false);
  const fileInputRef = useRef(null);

  useEffect(() => {
    fetchDocuments()
      .then((data) => setDocuments(data.documents))
      .catch((err) => setError(err.message));
    fetchHealth()
      .then(setHealth)
      .catch(() => setHealth(null));
  }, []);

  async function handleExtract(name) {
    setSelected(name);
    setResult(null);
    setError(null);
    setLoading(true);
    try {
      const data = await extractDocument(name);
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleUpload(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    setSelected(null);
    setResult(null);
    setError(null);
    setUploading(true);
    try {
      const data = await uploadDocument(file);
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
      event.target.value = "";
    }
  }

  return (
    <div className="pt-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">Extract fields</h1>
          <p className="mt-1 text-sm text-zinc-400">
            Pick a dataset document or upload a .docx file to extract the eight
            case fields with a local LLM.
          </p>
        </div>
        <ModelChip health={health} />
      </div>

      <div className="mt-6 grid grid-cols-[260px_1fr] items-start gap-6">
        {/* Sidebar */}
        <aside className="space-y-4">
          <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-3">
            <h2 className="mb-2 px-1 text-xs font-medium uppercase tracking-wider text-zinc-500">
              Dataset documents
            </h2>
            <ul className="space-y-1">
              {documents.map((doc) => (
                <li key={doc.name}>
                  <button
                    onClick={() => handleExtract(doc.name)}
                    disabled={loading || uploading}
                    className={`flex w-full items-center justify-between rounded-md px-2.5 py-1.5 text-left text-sm transition-colors ${
                      selected === doc.name
                        ? "bg-emerald-950/60 text-emerald-300"
                        : "text-zinc-300 hover:bg-zinc-800"
                    } disabled:opacity-50`}
                  >
                    <span>{doc.name}</span>
                    <span className="flex gap-1 text-[10px] text-zinc-500">
                      {doc.has_label && (
                        <span title="Has ground-truth label">L</span>
                      )}
                      {doc.has_output && (
                        <span title="Has saved output">O</span>
                      )}
                    </span>
                  </button>
                </li>
              ))}
              {documents.length === 0 && !error && (
                <li className="px-2 py-1 text-sm text-zinc-500">Loading…</li>
              )}
            </ul>
          </div>

          <div>
            <input
              ref={fileInputRef}
              type="file"
              accept=".docx"
              onChange={handleUpload}
              className="hidden"
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={loading || uploading}
              className="w-full rounded-lg border border-dashed border-zinc-700 bg-zinc-900/60 px-3 py-6 text-center text-sm text-zinc-400 transition-colors hover:border-emerald-700 hover:text-emerald-400 disabled:opacity-50"
            >
              {uploading ? "Uploading…" : "Drop or click to upload a .docx"}
            </button>
          </div>
        </aside>

        {/* Result panel */}
        <section className="min-h-[400px] space-y-4">
          {error && (
            <div className="rounded-lg border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-400">
              {error}
            </div>
          )}

          {(loading || uploading) && (
            <div className="flex min-h-[300px] flex-col items-center justify-center gap-3 rounded-lg border border-zinc-800 bg-zinc-900/50 text-zinc-400">
              <div className="h-8 w-8 animate-spin rounded-full border-2 border-zinc-700 border-t-emerald-500" />
              <p className="text-sm">
                Running extraction with the local model — this can take up to
                a minute…
              </p>
            </div>
          )}

          {!result && !loading && !uploading && !error && (
            <div className="flex min-h-[300px] flex-col items-center justify-center gap-2 rounded-lg border border-zinc-800 bg-zinc-900/40 text-zinc-500">
              <p className="text-sm">No extraction yet.</p>
              <p className="text-xs">
                Select a document on the left to run the pipeline.
              </p>
            </div>
          )}

          {result && (
            <>
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="flex flex-wrap items-center gap-2">
                  <h2 className="text-lg font-medium">{result.filename}</h2>
                  <StatusChip ok={true}>extracted</StatusChip>
                  {result.model_used && (
                    <StatusChip
                      title={
                        health?.model_ready
                          ? "Ran on a local model"
                          : "Ran on a cloud model — document text left your machine"
                      }
                    >
                      via {result.model_used}
                    </StatusChip>
                  )}
                  <StatusChip
                    ok={result.db_saved}
                    title={result.db_error || undefined}
                  >
                    {result.db_saved ? "saved to MongoDB" : "MongoDB not saved"}
                  </StatusChip>
                </div>
                <button
                  onClick={() => setShowJson((v) => !v)}
                  className="rounded-md border border-zinc-700 px-3 py-1.5 text-xs text-zinc-300 transition-colors hover:bg-zinc-800"
                >
                  {showJson ? "Hide raw JSON" : "Show raw JSON"}
                </button>
              </div>

              <WarningBanner warnings={result.warnings} />

              <div className="grid grid-cols-2 gap-3">
                {FIELDS.map((field) => (
                  <FieldCard
                    key={field}
                    field={field}
                    value={result.fields?.[field]}
                    expected={result.label?.[field]}
                  />
                ))}
              </div>

              {showJson && (
                <pre className="max-h-96 overflow-auto rounded-lg border border-zinc-800 bg-zinc-900 p-4 text-xs leading-relaxed text-zinc-300">
                  {JSON.stringify(result.fields, null, 2)}
                </pre>
              )}
            </>
          )}
        </section>
      </div>
    </div>
  );
}
