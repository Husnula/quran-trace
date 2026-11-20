"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  UploadSimple, FilePdf, SlidersHorizontal, Eye,
  CheckCircle, Warning, ArrowCounterClockwise, Download,
  Spinner, Info,
} from "@phosphor-icons/react";
import { processPdf, previewPage, getPdfPageCount, type ProcessOptions } from "@/lib/pdf-processor";

// ── Constants ────────────────────────────────────────────────────────────────
const PRESETS = [
  { label: "Sangat Samar", value: 0.12, desc: "12% — hampir tak terlihat" },
  { label: "Samar",        value: 0.22, desc: "22% — nyaman ditebalkan" },
  { label: "Agak Terlihat", value: 0.38, desc: "38% — panduan jelas" },
];

type State = "idle" | "previewing" | "processing" | "done" | "error";

// ── Main App ─────────────────────────────────────────────────────────────────
export default function TraceQuranApp() {
  const [file, setFile] = useState<File | null>(null);
  const [pageCount, setPageCount] = useState(0);
  const [previewNum, setPreviewNum] = useState(1);
  const [previewSrc, setPreviewSrc] = useState<string | null>(null);
  const [state, setState] = useState<State>("idle");
  const [progress, setProgress] = useState({ done: 0, total: 0 });
  const [error, setError] = useState("");
  const [isDragOver, setIsDragOver] = useState(false);

  // Options
  const [presetIdx, setPresetIdx] = useState(1); // "Samar" default
  const [opacity, setOpacity] = useState(0.22);
  const [keepWaqf, setKeepWaqf] = useState(true);
  const [keepAyat, setKeepAyat] = useState(false);

  const cancelRef = useRef({ cancelled: false });

  const opts: ProcessOptions = { opacity, keepWaqf, keepAyat };

  // ── File handling ──────────────────────────────────────────────────────────
  const handleFile = useCallback(async (f: File) => {
    if (!f.name.toLowerCase().endsWith(".pdf")) {
      setError("Hanya file PDF yang didukung.");
      setState("error");
      return;
    }
    setFile(f);
    setError("");
    setState("previewing");
    setPreviewSrc(null);
    try {
      const count = await getPdfPageCount(f);
      setPageCount(count);
      setPreviewNum(1);
      const src = await previewPage(f, 1, opts);
      setPreviewSrc(src);
      setState("idle");
    } catch (e: unknown) {
      setError(String(e));
      setState("error");
    }
  }, [opts]); // eslint-disable-line react-hooks/exhaustive-deps

  const refreshPreview = useCallback(async () => {
    if (!file) return;
    setState("previewing");
    setPreviewSrc(null);
    try {
      const src = await previewPage(file, previewNum, opts);
      setPreviewSrc(src);
      setState("idle");
    } catch (e: unknown) {
      setError(String(e));
      setState("error");
    }
  }, [file, previewNum, opts]);

  // Auto-refresh preview when settings change (debounced)
  useEffect(() => {
    if (!file || state === "processing") return;
    const timer = setTimeout(() => { refreshPreview(); }, 600);
    return () => clearTimeout(timer);
  }, [opacity, keepWaqf, keepAyat, previewNum]); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Processing ──────────────────────────────────────────────────────────────
  const handleProcess = async () => {
    if (!file || state === "processing") return;
    cancelRef.current.cancelled = false;
    setState("processing");
    setProgress({ done: 0, total: pageCount });
    try {
      await processPdf(
        file, opts,
        (done, total) => setProgress({ done, total }),
        cancelRef.current,
      );
      setState("done");
    } catch (e: unknown) {
      if (String(e).includes("Dibatalkan")) { setState("idle"); }
      else { setError(String(e)); setState("error"); }
    }
  };

  // ── Drag and Drop ───────────────────────────────────────────────────────────
  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  }, [handleFile]);

  const onDragOver = (e: React.DragEvent) => { e.preventDefault(); setIsDragOver(true); };
  const onDragLeave = () => setIsDragOver(false);

  const onInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) handleFile(f);
  };

  const pct = progress.total > 0 ? Math.round((progress.done / progress.total) * 100) : 0;

  // ── Render ──────────────────────────────────────────────────────────────────
  return (
    <div className="min-h-[100dvh] bg-[var(--color-bg-base)] flex flex-col">
      {/* Nav */}
      <nav className="h-14 bg-[var(--color-bg-panel)] border-b border-[var(--color-border-subtle)] flex items-center px-6">
        <div className="flex items-center gap-3">
          <span className="w-7 h-7 rounded-lg bg-[var(--color-accent)] flex items-center justify-center">
            <FilePdf weight="fill" className="text-white w-4 h-4" />
          </span>
          <span className="font-semibold text-[var(--color-text-primary)] tracking-tight">
            Trace Qur'an
          </span>
        </div>
        <span className="ml-auto text-xs text-[var(--color-text-muted)]">
          100% di browser - tidak ada upload ke server
        </span>
      </nav>

      {/* Main */}
      <div className="flex-1 flex flex-col lg:flex-row max-w-[1400px] mx-auto w-full px-4 lg:px-0 py-6 gap-6">
        {/* Left Panel */}
        <div className="w-full lg:w-[320px] shrink-0 flex flex-col gap-4">

          {/* Drop Zone */}
          <Section title="File PDF Al-Qur'an">
            <label
              onDrop={onDrop}
              onDragOver={onDragOver}
              onDragLeave={onDragLeave}
              className={[
                "flex flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed",
                "py-7 px-4 cursor-pointer transition-colors",
                isDragOver
                  ? "border-[var(--color-accent)] bg-[var(--color-accent-light)]"
                  : "border-[var(--color-border-strong)] bg-[var(--color-bg-sunken)] hover:border-[var(--color-accent-muted)]",
              ].join(" ")}
            >
              <input type="file" accept=".pdf" className="sr-only" onChange={onInputChange} />
              <UploadSimple className="w-6 h-6 text-[var(--color-text-muted)]" />
              <span className="text-sm text-[var(--color-text-muted)] text-center leading-snug">
                Drag PDF ke sini<br />
                <span className="text-[var(--color-accent)] font-medium">atau klik untuk pilih</span>
              </span>
            </label>
            {file && (
              <div className="flex items-center gap-2 mt-2 px-3 py-2 rounded-lg bg-[var(--color-accent-light)]">
                <CheckCircle weight="fill" className="text-[var(--color-accent)] w-4 h-4 shrink-0" />
                <span className="text-xs text-[var(--color-accent)] font-medium truncate">
                  {file.name} ({pageCount} halaman)
                </span>
              </div>
            )}
          </Section>

          {/* Fade Level */}
          <Section title="Tingkat Samar">
            <div className="flex flex-col gap-1">
              {PRESETS.map((p, i) => (
                <button
                  key={p.label}
                  onClick={() => { setPresetIdx(i); setOpacity(p.value); }}
                  className={[
                    "flex items-center justify-between px-3 py-2.5 rounded-lg text-left transition-colors",
                    presetIdx === i
                      ? "bg-[var(--color-accent)] text-white"
                      : "bg-[var(--color-bg-sunken)] text-[var(--color-text-primary)] hover:bg-[var(--color-border-subtle)]",
                  ].join(" ")}
                >
                  <span className="text-sm font-medium">{p.label}</span>
                  <span className={`text-xs ${presetIdx === i ? "text-white/70" : "text-[var(--color-text-muted)]"}`}>
                    {p.desc}
                  </span>
                </button>
              ))}
            </div>
            {/* Custom slider */}
            <div className="mt-3 flex items-center gap-3">
              <SlidersHorizontal className="w-4 h-4 text-[var(--color-text-muted)] shrink-0" />
              <input
                type="range" min={0.08} max={0.60} step={0.01}
                value={opacity}
                onChange={(e) => { setOpacity(+e.target.value); setPresetIdx(-1); }}
                className="flex-1 accent-[var(--color-accent)]"
              />
              <span className="text-xs font-mono text-[var(--color-text-secondary)] w-8 text-right">
                {Math.round(opacity * 100)}%
              </span>
            </div>
          </Section>

          {/* Options */}
          <Section title="Pertahankan Hitam">
            {[
              { label: "Border ornamen halaman", sub: "Selalu aktif", checked: true, disabled: true, onChange: () => {} },
              { label: "Tanda waqf (ع، ط، ص، ج dll)", sub: "Disarankan", checked: keepWaqf, disabled: false, onChange: (v: boolean) => setKeepWaqf(v) },
              { label: "Nomor ayat dalam lingkaran", sub: "Opsional", checked: keepAyat, disabled: false, onChange: (v: boolean) => setKeepAyat(v) },
            ].map((opt) => (
              <label
                key={opt.label}
                className={`flex items-start gap-3 py-2 ${opt.disabled ? "opacity-60" : "cursor-pointer"}`}
              >
                <div className="relative mt-0.5">
                  <input
                    type="checkbox" checked={opt.checked} disabled={opt.disabled}
                    onChange={(e) => opt.onChange(e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className={[
                    "w-4 h-4 rounded border-2 flex items-center justify-center transition-colors",
                    opt.checked
                      ? "bg-[var(--color-accent)] border-[var(--color-accent)]"
                      : "border-[var(--color-border-strong)] bg-white",
                  ].join(" ")}>
                    {opt.checked && <div className="w-2 h-2 bg-white rounded-sm" />}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-[var(--color-text-primary)]">{opt.label}</div>
                  <div className="text-xs text-[var(--color-text-muted)]">{opt.sub}</div>
                </div>
              </label>
            ))}
          </Section>

          {/* Preview nav */}
          {file && (
            <Section title="Preview Halaman">
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPreviewNum(Math.max(1, previewNum - 1))}
                  disabled={previewNum <= 1}
                  className="px-3 py-1.5 rounded-lg bg-[var(--color-bg-sunken)] text-sm text-[var(--color-text-secondary)] disabled:opacity-40 hover:bg-[var(--color-border-subtle)] transition-colors"
                >
                  ◄
                </button>
                <span className="flex-1 text-center text-sm text-[var(--color-text-primary)]">
                  {previewNum} / {pageCount}
                </span>
                <button
                  onClick={() => setPreviewNum(Math.min(pageCount, previewNum + 1))}
                  disabled={previewNum >= pageCount}
                  className="px-3 py-1.5 rounded-lg bg-[var(--color-bg-sunken)] text-sm text-[var(--color-text-secondary)] disabled:opacity-40 hover:bg-[var(--color-border-subtle)] transition-colors"
                >
                  ►
                </button>
                <button
                  onClick={refreshPreview}
                  disabled={state === "previewing"}
                  className="px-3 py-1.5 rounded-lg bg-[var(--color-bg-sunken)] text-sm text-[var(--color-text-secondary)] disabled:opacity-40 hover:bg-[var(--color-border-subtle)] transition-colors"
                >
                  <ArrowCounterClockwise className="w-4 h-4" />
                </button>
              </div>
            </Section>
          )}

          {/* Process button */}
          <div className="flex flex-col gap-2 mt-auto">
            {state === "processing" && (
              <div className="space-y-1">
                <div className="flex justify-between text-xs text-[var(--color-text-secondary)]">
                  <span>Memproses halaman {progress.done} dari {progress.total}...</span>
                  <span>{pct}%</span>
                </div>
                <div className="h-2 rounded-full bg-[var(--color-bg-sunken)] overflow-hidden">
                  <motion.div
                    className="h-full bg-[var(--color-accent)] rounded-full"
                    initial={{ width: "0%" }}
                    animate={{ width: `${pct}%` }}
                    transition={{ ease: "linear" }}
                  />
                </div>
              </div>
            )}

            {state === "done" && (
              <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-[var(--color-accent-light)]">
                <CheckCircle weight="fill" className="text-[var(--color-accent)] w-5 h-5" />
                <span className="text-sm text-[var(--color-accent)] font-medium">
                  Download otomatis dimulai!
                </span>
              </div>
            )}

            {state === "error" && (
              <div className="flex items-start gap-2 px-3 py-2 rounded-lg bg-[var(--color-error-bg)]">
                <Warning className="text-[var(--color-error)] w-4 h-4 mt-0.5 shrink-0" />
                <span className="text-xs text-[var(--color-error)]">{error}</span>
              </div>
            )}

            <button
              onClick={state === "processing" ? () => { cancelRef.current.cancelled = true; } : handleProcess}
              disabled={!file || state === "previewing"}
              className={[
                "w-full py-3 rounded-lg font-semibold text-sm flex items-center justify-center gap-2 transition-all active:scale-[0.98]",
                state === "processing"
                  ? "bg-[var(--color-error)] text-white hover:bg-red-700"
                  : !file || state === "previewing"
                  ? "bg-[var(--color-border-subtle)] text-[var(--color-text-muted)] cursor-not-allowed"
                  : "bg-[var(--color-accent)] text-white hover:bg-[var(--color-accent-hover)]",
              ].join(" ")}
            >
              {state === "processing" ? (
                <><Spinner className="w-4 h-4 animate-spin" /> Batalkan</>
              ) : state === "previewing" ? (
                <><Spinner className="w-4 h-4 animate-spin" /> Memuat Preview...</>
              ) : (
                <><Download className="w-4 h-4" /> Proses dan Unduh PDF</>
              )}
            </button>
          </div>
        </div>

        {/* Right: Preview Panel */}
        <div className="flex-1 min-w-0">
          <div className="bg-[var(--color-bg-panel)] rounded-xl border border-[var(--color-border-subtle)] overflow-hidden h-full min-h-[500px] flex flex-col">
            <div className="px-4 py-3 border-b border-[var(--color-border-subtle)] flex items-center gap-2">
              <Eye className="w-4 h-4 text-[var(--color-text-muted)]" />
              <span className="text-sm font-medium text-[var(--color-text-secondary)]">Preview</span>
              <span className="text-xs text-[var(--color-text-muted)] ml-auto flex items-center gap-1">
                <Info className="w-3.5 h-3.5" />
                Preview otomatis diperbarui saat pengaturan berubah
              </span>
            </div>

            <div className="flex-1 flex items-center justify-center p-6 bg-[var(--color-bg-sunken)]">
              <AnimatePresence mode="wait">
                {!file ? (
                  <motion.div
                    key="empty"
                    initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                    className="text-center space-y-3"
                  >
                    <FilePdf className="w-16 h-16 text-[var(--color-border-strong)] mx-auto" />
                    <p className="text-sm text-[var(--color-text-muted)] max-w-[280px]">
                      Pilih file PDF Al-Qur'an untuk melihat preview hasil trace
                    </p>
                  </motion.div>
                ) : state === "previewing" && !previewSrc ? (
                  <motion.div
                    key="loading"
                    initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                    className="flex flex-col items-center gap-3"
                  >
                    <Spinner className="w-8 h-8 text-[var(--color-accent)] animate-spin" />
                    <p className="text-sm text-[var(--color-text-muted)]">Memuat preview...</p>
                  </motion.div>
                ) : previewSrc ? (
                  <motion.div
                    key={previewSrc}
                    initial={{ opacity: 0, scale: 0.98 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
                    className="relative"
                  >
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={previewSrc}
                      alt={`Preview halaman ${previewNum}`}
                      className="max-h-[70vh] max-w-full object-contain rounded-lg shadow-md"
                    />
                    {state === "previewing" && (
                      <div className="absolute inset-0 bg-white/60 rounded-lg flex items-center justify-center">
                        <Spinner className="w-6 h-6 text-[var(--color-accent)] animate-spin" />
                      </div>
                    )}
                  </motion.div>
                ) : null}
              </AnimatePresence>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-[var(--color-border-subtle)] py-4 px-6 text-center">
        <p className="text-xs text-[var(--color-text-muted)]">
          Trace Qur'an - Duta Ilmu &middot; Semua proses terjadi di browser Anda, tidak ada data yang dikirim ke server
        </p>
      </footer>
    </div>
  );
}

// ── Helper component ─────────────────────────────────────────────────────────
function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-[var(--color-bg-panel)] rounded-xl border border-[var(--color-border-subtle)] p-4">
      <p className="text-[10px] font-semibold text-[var(--color-text-muted)] uppercase tracking-widest mb-3">
        {title}
      </p>
      {children}
    </div>
  );
}
