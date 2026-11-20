"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  UploadSimple, FilePdf, Eye, CheckCircle, Warning,
  ArrowCounterClockwise, Download, Spinner, Sparkle,
  PenNib, Check, Image as ImageIcon, BookOpen, CaretLeft, CaretRight,
  ArrowsClockwise, MagnifyingGlass
} from "@phosphor-icons/react";
import {
  processPdf,
  previewPage,
  renderOriginalPage,
  getPdfPageCount,
  type ProcessOptions,
  type TracingModel,
} from "@/lib/pdf-processor";

type State = "idle" | "previewing" | "processing" | "done" | "error";
type PreviewTab = "traced" | "original";

export default function TraceQuranApp() {
  const [file, setFile] = useState<File | null>(null);
  const [pageCount, setPageCount] = useState(0);
  const [activePage, setActivePage] = useState(1);
  const [previewTab, setPreviewTab] = useState<PreviewTab>("traced");

  // Previews cache: pageNum -> dataUrl
  const [tracedPreview, setTracedPreview] = useState<string | null>(null);
  const [originalPreview, setOriginalPreview] = useState<string | null>(null);

  const [state, setState] = useState<State>("idle");
  const [progress, setProgress] = useState({ done: 0, total: 0 });
  const [error, setError] = useState("");
  const [isDragOver, setIsDragOver] = useState(false);

  // Tracing Options
  const [model, setModel] = useState<TracingModel>("gray");
  const [opacity, setOpacity] = useState(0.18);
  const [keepBorder, setKeepBorder] = useState(true);
  const [keepWaqf, setKeepWaqf] = useState(true);
  const [keepAyat, setKeepAyat] = useState(true);

  // Range options
  const [rangeMode, setRangeMode] = useState<"all" | "custom">("all");
  const [rangeStart, setRangeStart] = useState(1);
  const [rangeEnd, setRangeEnd] = useState(1);

  const cancelRef = useRef({ cancelled: false });
  const fileInputRef = useRef<HTMLInputElement>(null);

  const opts: ProcessOptions = {
    model,
    opacity,
    keepWaqf,
    keepAyat,
  };

  // ── Load Original Page ───────────────────────────────────────────────────
  const loadOriginalPreview = useCallback(async (f: File, pageNum: number) => {
    try {
      const src = await renderOriginalPage(f, pageNum, 140);
      setOriginalPreview(src);
    } catch {
      // non-blocking
    }
  }, []);

  // ── Generate Traced Preview for Active Page ──────────────────────────────
  const handleTraceCurrentPage = useCallback(async (targetPage?: number) => {
    if (!file) return;
    const pageNum = targetPage ?? activePage;
    setState("previewing");
    setError("");

    try {
      // Fetch both original & traced
      const [tracedSrc, origSrc] = await Promise.all([
        previewPage(file, pageNum, opts),
        renderOriginalPage(file, pageNum, 140),
      ]);
      setTracedPreview(tracedSrc);
      setOriginalPreview(origSrc);
      setPreviewTab("traced");
      setState("idle");
    } catch (e: unknown) {
      setError(String(e));
      setState("error");
    }
  }, [file, activePage, opts]);

  // ── File Selection ───────────────────────────────────────────────────────
  const handleFileSelect = useCallback(async (f: File) => {
    if (!f.name.toLowerCase().endsWith(".pdf")) {
      setError("Hanya file PDF yang didukung saat ini.");
      setState("error");
      return;
    }
    setFile(f);
    setError("");
    setState("previewing");
    setTracedPreview(null);
    setOriginalPreview(null);
    setActivePage(2); // Default ke halaman 2 (Al-Fatihah) agar langsung terlihat teksnya!

    try {
      const count = await getPdfPageCount(f);
      setPageCount(count);
      setRangeEnd(count);

      // Otomatis trace halaman 2 sebagai awal
      const [tracedSrc, origSrc] = await Promise.all([
        previewPage(f, 2, opts),
        renderOriginalPage(f, 2, 140),
      ]);
      setTracedPreview(tracedSrc);
      setOriginalPreview(origSrc);
      setState("idle");
    } catch (e: unknown) {
      setError(String(e));
      setState("error");
    }
  }, [opts]);

  // ── Navigation ───────────────────────────────────────────────────────────
  const goToPage = (newPage: number) => {
    if (!file || newPage < 1 || newPage > pageCount) return;
    setActivePage(newPage);
    handleTraceCurrentPage(newPage);
  };

  // ── Reset ────────────────────────────────────────────────────────────────
  const handleReset = () => {
    setFile(null);
    setPageCount(0);
    setActivePage(1);
    setTracedPreview(null);
    setOriginalPreview(null);
    setState("idle");
    setError("");
    setModel("gray");
    setOpacity(0.18);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  // ── Batch Process & Download ─────────────────────────────────────────────
  const handleProcessFull = async () => {
    if (!file) return;
    setState("processing");
    setProgress({ done: 0, total: rangeMode === "all" ? pageCount : (rangeEnd - rangeStart + 1) });
    cancelRef.current.cancelled = false;

    try {
      const pageRange = rangeMode === "custom"
        ? { start: Math.max(1, rangeStart), end: Math.min(pageCount, rangeEnd) }
        : undefined;

      await processPdf(
        file,
        opts,
        (done, total) => setProgress({ done, total }),
        cancelRef.current,
        pageRange
      );
      setState("done");
    } catch (e: unknown) {
      if ((e as Error)?.message === "Dibatalkan") {
        setState("idle");
      } else {
        setError(String(e));
        setState("error");
      }
    }
  };

  const handleCancel = () => {
    cancelRef.current.cancelled = true;
    setState("idle");
  };

  return (
    <div className="min-h-screen bg-[#F4F6F4] text-[#1C1917] font-sans antialiased flex flex-col">
      {/* ── TOP HEADER BAR ── */}
      <header className="bg-[#1b4332] text-white shadow-md border-b-4 border-[#FBBF24]">
        <div className="max-w-[1500px] mx-auto px-4 sm:px-6 py-3.5 flex flex-wrap items-center justify-between gap-3">
          {/* Logo & Title */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-[#FBBF24] flex items-center justify-center text-[#1b4332] shadow-sm">
              <PenNib size={22} weight="fill" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-lg sm:text-xl font-extrabold tracking-wide text-white uppercase">
                  Arabic Tracing Maker
                </h1>
                <span className="bg-[#FBBF24] text-[#1b4332] text-[11px] font-black px-2 py-0.5 rounded-full tracking-wider uppercase shadow-xs">
                  Duta Ilmu
                </span>
              </div>
              <p className="text-xs text-[#95d5b2] font-medium hidden sm:block">
                Ubah PDF & Gambar Tulisan Arab Menjadi Lembar Latihan Menebalkan
              </p>
            </div>
          </div>

          {/* Right Status & Action */}
          <div className="flex items-center gap-2.5">
            <div className="flex items-center gap-2 bg-[#2d6a4f] px-3 py-1.5 rounded-full text-xs font-semibold text-white shadow-xs">
              {state === "processing" ? (
                <>
                  <Spinner size={14} className="animate-spin text-[#FBBF24]" />
                  <span>Memproses ({progress.done}/{progress.total})...</span>
                </>
              ) : state === "previewing" ? (
                <>
                  <Spinner size={14} className="animate-spin text-[#FBBF24]" />
                  <span>Merender Halaman...</span>
                </>
              ) : file ? (
                <>
                  <span className="w-2 h-2 rounded-full bg-[#52b788] animate-pulse" />
                  <span>File Siap Diproses</span>
                </>
              ) : (
                <>
                  <span className="w-2 h-2 rounded-full bg-[#FBBF24]" />
                  <span>Siap Digunakan</span>
                </>
              )}
            </div>

            <button
              onClick={handleReset}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-[#2d6a4f] hover:bg-[#40916c] text-white rounded-full text-xs font-semibold transition-colors cursor-pointer border border-[#40916c]"
              title="Reset ke pengaturan awal"
            >
              <ArrowsClockwise size={14} />
              <span>Reset</span>
            </button>
          </div>
        </div>
      </header>

      {/* ── MAIN CONTENT 2-COLUMN LAYOUT ── */}
      <main className="max-w-[1500px] mx-auto w-full px-4 sm:px-6 py-6 flex-1 grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* ── LEFT COLUMN (CONTROLS: STEPS 1, 2, 3) ── */}
        <div className="lg:col-span-5 flex flex-col gap-5">
          {/* STEP 1: UPLOAD */}
          <section className="bg-white rounded-2xl border border-[#D8E2DC] p-5 shadow-xs">
            <div className="flex items-center gap-2.5 mb-3.5">
              <span className="w-6 h-6 rounded-full bg-[#2d6a4f] text-white text-xs font-bold flex items-center justify-center">
                1
              </span>
              <h2 className="text-sm font-bold text-[#1b4332] uppercase tracking-wide">
                Upload File PDF atau Gambar
              </h2>
            </div>

            <div
              onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
              onDragLeave={() => setIsDragOver(false)}
              onDrop={(e) => {
                e.preventDefault();
                setIsDragOver(false);
                const dropped = e.dataTransfer.files[0];
                if (dropped) handleFileSelect(dropped);
              }}
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all ${
                isDragOver
                  ? "border-[#2d6a4f] bg-[#e8f5e9]"
                  : file
                  ? "border-[#52b788] bg-[#f8fdf9]"
                  : "border-[#B7C4B8] hover:border-[#2d6a4f] bg-[#FAFCFA] hover:bg-[#F2F7F2]"
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,application/pdf"
                className="hidden"
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (f) handleFileSelect(f);
                }}
              />

              <div className="w-12 h-12 rounded-full bg-[#e8f5e9] text-[#2d6a4f] flex items-center justify-center mx-auto mb-3 shadow-xs">
                <UploadSimple size={24} weight="bold" />
              </div>
              <p className="text-sm font-bold text-[#1b4332]">
                Klik untuk Memilih File atau Tarik ke Sini
              </p>
              <p className="text-xs text-[#52796f] mt-1">
                Mendukung PDF Mushaf Al-Qur'an (Juz 1-30)
              </p>
            </div>

            {/* File Chip if loaded */}
            {file && (
              <div className="mt-3.5 p-3 rounded-xl bg-[#e8f5e9] border border-[#b7e4c7] flex items-center justify-between">
                <div className="flex items-center gap-2.5 min-w-0">
                  <FilePdf size={24} className="text-[#2d6a4f] shrink-0" weight="fill" />
                  <div className="min-w-0">
                    <p className="text-xs font-bold text-[#1b4332] truncate">{file.name}</p>
                    <p className="text-[11px] text-[#52796f]">
                      {pageCount} Halaman • {(file.size / (1024 * 1024)).toFixed(1)} MB
                    </p>
                  </div>
                </div>
                <button
                  onClick={(e) => { e.stopPropagation(); fileInputRef.current?.click(); }}
                  className="text-xs font-semibold text-[#2d6a4f] hover:underline px-2 py-1 shrink-0 cursor-pointer"
                >
                  Ganti
                </button>
              </div>
            )}
          </section>

          {/* STEP 2: PILIH MODEL TRACING */}
          <section className="bg-white rounded-2xl border border-[#D8E2DC] p-5 shadow-xs">
            <div className="flex items-center gap-2.5 mb-3.5">
              <span className="w-6 h-6 rounded-full bg-[#2d6a4f] text-white text-xs font-bold flex items-center justify-center">
                2
              </span>
              <h2 className="text-sm font-bold text-[#1b4332] uppercase tracking-wide">
                Pilih Model Tracing
              </h2>
            </div>

            {/* Radio Model Cards */}
            <div className="grid grid-cols-2 gap-3 mb-4">
              {/* MODEL A: Light Gray */}
              <div
                onClick={() => setModel("gray")}
                className={`p-3.5 rounded-xl border-2 cursor-pointer transition-all ${
                  model === "gray"
                    ? "border-[#2d6a4f] bg-[#e8f5e9]/70 shadow-xs"
                    : "border-[#D8E2DC] hover:border-[#b7c4b8] bg-white"
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[11px] font-black text-[#2d6a4f] tracking-wider uppercase">
                    Model A
                  </span>
                  <div className={`w-4 h-4 rounded-full flex items-center justify-center ${
                    model === "gray" ? "bg-[#2d6a4f] text-white" : "border border-[#b7c4b8]"
                  }`}>
                    {model === "gray" && <Check size={10} weight="bold" />}
                  </div>
                </div>
                <p className="text-sm font-bold text-[#1b4332]">Light Gray</p>
                <p className="text-[11px] text-[#52796f] mt-1 leading-tight">
                  Tulisan Arab menjadi abu-abu tipis presisi (standar FunFurqan).
                </p>
              </div>

              {/* MODEL B: Outline */}
              <div
                onClick={() => setModel("outline")}
                className={`p-3.5 rounded-xl border-2 cursor-pointer transition-all ${
                  model === "outline"
                    ? "border-[#2d6a4f] bg-[#e8f5e9]/70 shadow-xs"
                    : "border-[#D8E2DC] hover:border-[#b7c4b8] bg-white"
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[11px] font-black text-[#2d6a4f] tracking-wider uppercase">
                    Model B
                  </span>
                  <div className={`w-4 h-4 rounded-full flex items-center justify-center ${
                    model === "outline" ? "bg-[#2d6a4f] text-white" : "border border-[#b7c4b8]"
                  }`}>
                    {model === "outline" && <Check size={10} weight="bold" />}
                  </div>
                </div>
                <p className="text-sm font-bold text-[#1b4332]">Outline</p>
                <p className="text-[11px] text-[#52796f] mt-1 leading-tight">
                  Garis tepi tipis, dalam huruf putih (hollow kaligrafi).
                </p>
              </div>
            </div>

            {/* Slider Kepekatan */}
            <div className="p-3.5 rounded-xl bg-[#FAFCFA] border border-[#E2E8E2] mb-4">
              <div className="flex items-center justify-between text-xs font-semibold mb-2">
                <span className="text-[#1b4332]">
                  {model === "gray" ? "Kepekatan Abu-abu" : "Ketebalan Garis Tepi"}
                </span>
                <span className="text-[#2d6a4f] font-mono font-bold bg-[#e8f5e9] px-2 py-0.5 rounded-md">
                  {Math.round(opacity * 100)}%
                </span>
              </div>
              <input
                type="range"
                min={0.06}
                max={0.45}
                step={0.01}
                value={opacity}
                onChange={(e) => setOpacity(parseFloat(e.target.value))}
                className="w-full accent-[#2d6a4f] cursor-pointer"
              />
              <div className="flex justify-between text-[10px] text-[#849a88] mt-1.5 font-medium">
                <span>Lebih Samar (8%)</span>
                <span>Standar (18%)</span>
                <span>Lebih Jelas (35%)</span>
              </div>
            </div>

            {/* Checklists */}
            <div className="space-y-2 text-xs">
              <label className="flex items-center gap-2 cursor-pointer text-[#2d6a4f] font-medium">
                <input
                  type="checkbox"
                  checked={keepBorder}
                  onChange={(e) => setKeepBorder(e.target.checked)}
                  className="rounded accent-[#2d6a4f]"
                />
                <span>Border ornamen halaman (tetap hitam asli)</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer text-[#2d6a4f] font-medium">
                <input
                  type="checkbox"
                  checked={keepWaqf}
                  onChange={(e) => setKeepWaqf(e.target.checked)}
                  className="rounded accent-[#2d6a4f]"
                />
                <span>Tanda waqf margin ('ع' waqf lazim & ruku')</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer text-[#2d6a4f] font-medium">
                <input
                  type="checkbox"
                  checked={keepAyat}
                  onChange={(e) => setKeepAyat(e.target.checked)}
                  className="rounded accent-[#2d6a4f]"
                />
                <span>Nomor ayat dalam roset (tetap hitam tajam)</span>
              </label>
            </div>
          </section>

          {/* STEP 3: PROSES TRACING & AKSI */}
          <section className="bg-white rounded-2xl border border-[#D8E2DC] p-5 shadow-xs">
            <div className="flex items-center gap-2.5 mb-3.5">
              <span className="w-6 h-6 rounded-full bg-[#2d6a4f] text-white text-xs font-bold flex items-center justify-center">
                3
              </span>
              <h2 className="text-sm font-bold text-[#1b4332] uppercase tracking-wide">
                Proses Tracing
              </h2>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-col gap-3">
              {/* Button: Trace Halaman Ini */}
              <button
                disabled={!file || state === "processing"}
                onClick={() => handleTraceCurrentPage()}
                className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl font-bold text-sm bg-[#e8f5e9] text-[#1b4332] hover:bg-[#d8f3dc] border-2 border-[#b7e4c7] transition-all cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed shadow-xs"
              >
                {state === "previewing" ? (
                  <Spinner size={18} className="animate-spin text-[#2d6a4f]" />
                ) : (
                  <MagnifyingGlass size={18} weight="bold" className="text-[#2d6a4f]" />
                )}
                <span>Trace Halaman Ini ({activePage}/{pageCount || "?"})</span>
              </button>

              {/* Range Selector */}
              <div className="bg-[#FAFCFA] p-3 rounded-xl border border-[#E2E8E2] text-xs">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-semibold text-[#1b4332]">Jangkauan Pemrosesan:</span>
                  <div className="flex items-center gap-3">
                    <label className="flex items-center gap-1 cursor-pointer">
                      <input
                        type="radio"
                        name="rangeMode"
                        checked={rangeMode === "all"}
                        onChange={() => setRangeMode("all")}
                        className="accent-[#2d6a4f]"
                      />
                      <span>Semua Halaman</span>
                    </label>
                    <label className="flex items-center gap-1 cursor-pointer">
                      <input
                        type="radio"
                        name="rangeMode"
                        checked={rangeMode === "custom"}
                        onChange={() => setRangeMode("custom")}
                        className="accent-[#2d6a4f]"
                      />
                      <span>Rentang</span>
                    </label>
                  </div>
                </div>

                {rangeMode === "custom" && (
                  <div className="flex items-center gap-2 mt-2 pt-2 border-t border-[#E2E8E2]">
                    <span>Hal:</span>
                    <input
                      type="number"
                      min={1}
                      max={pageCount || 1}
                      value={rangeStart}
                      onChange={(e) => setRangeStart(parseInt(e.target.value) || 1)}
                      className="w-16 px-2 py-1 text-center border rounded font-mono"
                    />
                    <span>s.d.</span>
                    <input
                      type="number"
                      min={1}
                      max={pageCount || 1}
                      value={rangeEnd}
                      onChange={(e) => setRangeEnd(parseInt(e.target.value) || 1)}
                      className="w-16 px-2 py-1 text-center border rounded font-mono"
                    />
                  </div>
                )}
              </div>

              {/* Button: Proses Seluruh Halaman & Unduh PDF */}
              {state === "processing" ? (
                <div className="p-4 rounded-xl bg-[#e8f5e9] border border-[#52b788] text-center">
                  <div className="flex items-center justify-between text-xs font-bold text-[#1b4332] mb-2">
                    <span>Sedang memproses halaman {progress.done} dari {progress.total}...</span>
                    <span>{Math.round((progress.done / (progress.total || 1)) * 100)}%</span>
                  </div>
                  <div className="w-full bg-[#c7e9ce] h-2.5 rounded-full overflow-hidden mb-3">
                    <div
                      className="bg-[#2d6a4f] h-full transition-all duration-300"
                      style={{ width: `${(progress.done / (progress.total || 1)) * 100}%` }}
                    />
                  </div>
                  <button
                    onClick={handleCancel}
                    className="text-xs font-bold text-[#b91c1c] hover:underline cursor-pointer"
                  >
                    Batal Memproses
                  </button>
                </div>
              ) : (
                <button
                  disabled={!file}
                  onClick={handleProcessFull}
                  className="w-full flex items-center justify-center gap-2.5 px-5 py-3.5 rounded-xl font-extrabold text-sm bg-[#1b4332] text-white hover:bg-[#2d6a4f] shadow-md transition-all cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed hover:shadow-lg active:scale-[0.99]"
                >
                  <Download size={20} weight="bold" className="text-[#FBBF24]" />
                  <span>Proses & Unduh PDF Trace</span>
                </button>
              )}
            </div>

            {error && (
              <div className="mt-3 p-3 rounded-xl bg-[#fee2e2] text-[#991b1b] text-xs flex items-center gap-2 border border-[#fca5a5]">
                <Warning size={16} className="shrink-0" weight="fill" />
                <span>{error}</span>
              </div>
            )}
          </section>
        </div>

        {/* ── RIGHT COLUMN (PREVIEW AREA: STEP 4) ── */}
        <div className="lg:col-span-7 flex flex-col gap-4">
          <section className="bg-white rounded-2xl border border-[#D8E2DC] p-5 shadow-xs flex flex-col min-h-[680px]">
            {/* Header: Title, Segmented Tabs, Pagination */}
            <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-[#E8ECE8]">
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-[#2d6a4f] text-white text-xs font-bold flex items-center justify-center">
                  4
                </span>
                <h2 className="text-sm font-bold text-[#1b4332] uppercase tracking-wide">
                  Preview Hasil
                </h2>
              </div>

              {/* Segmented Tabs: Hasil Tracing vs Gambar Asli */}
              <div className="flex items-center bg-[#E8ECE8] p-1 rounded-xl text-xs font-bold">
                <button
                  onClick={() => setPreviewTab("traced")}
                  className={`px-3 py-1.5 rounded-lg transition-all cursor-pointer ${
                    previewTab === "traced"
                      ? "bg-[#2d6a4f] text-white shadow-xs"
                      : "text-[#52796f] hover:text-[#1b4332]"
                  }`}
                >
                  Hasil Tracing
                </button>
                <button
                  onClick={() => {
                    setPreviewTab("original");
                    if (!originalPreview && file) loadOriginalPreview(file, activePage);
                  }}
                  className={`px-3 py-1.5 rounded-lg transition-all cursor-pointer ${
                    previewTab === "original"
                      ? "bg-[#2d6a4f] text-white shadow-xs"
                      : "text-[#52796f] hover:text-[#1b4332]"
                  }`}
                >
                  Gambar Asli
                </button>
              </div>

              {/* Pagination Controls */}
              <div className="flex items-center gap-2">
                <button
                  disabled={!file || activePage <= 1}
                  onClick={() => goToPage(activePage - 1)}
                  className="w-8 h-8 rounded-lg bg-[#FAFCFA] hover:bg-[#e8f5e9] border border-[#D8E2DC] flex items-center justify-center text-[#1b4332] disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer transition-colors"
                  title="Halaman Sebelumnya"
                >
                  <CaretLeft size={16} weight="bold" />
                </button>

                <div className="text-xs font-mono font-bold text-[#1b4332] px-2 py-1 bg-[#FAFCFA] border border-[#D8E2DC] rounded-lg">
                  Hal {file ? activePage : 0} / {pageCount}
                </div>

                <button
                  disabled={!file || activePage >= pageCount}
                  onClick={() => goToPage(activePage + 1)}
                  className="w-8 h-8 rounded-lg bg-[#FAFCFA] hover:bg-[#e8f5e9] border border-[#D8E2DC] flex items-center justify-center text-[#1b4332] disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer transition-colors"
                  title="Halaman Selanjutnya"
                >
                  <CaretRight size={16} weight="bold" />
                </button>
              </div>
            </div>

            {/* Canvas / Preview Container with Dot-Grid Background */}
            <div className="flex-1 rounded-xl bg-[#F7F9F7] border border-[#E8ECE8] mt-4 flex items-center justify-center p-4 overflow-auto min-h-[560px] relative"
                 style={{
                   backgroundImage: "radial-gradient(#CBD5E1 1px, transparent 1px)",
                   backgroundSize: "20px 20px",
                 }}>
              {state === "previewing" && (
                <div className="absolute inset-0 bg-white/70 backdrop-blur-xs flex flex-col items-center justify-center gap-2 z-10">
                  <Spinner size={32} className="animate-spin text-[#2d6a4f]" />
                  <p className="text-xs font-bold text-[#1b4332]">Memproses Preview Halaman {activePage}...</p>
                </div>
              )}

              {file ? (
                previewTab === "traced" ? (
                  tracedPreview ? (
                    <motion.div
                      key={`traced-${activePage}`}
                      initial={{ opacity: 0, scale: 0.98 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ duration: 0.2 }}
                      className="bg-white rounded-lg shadow-xl p-2 border border-[#E2E8E2] max-w-full"
                    >
                      <img
                        src={tracedPreview}
                        alt={`Trace Preview Hal ${activePage}`}
                        className="max-h-[640px] w-auto object-contain rounded"
                      />
                    </motion.div>
                  ) : (
                    <div className="text-center text-xs text-[#52796f]">
                      <Spinner size={24} className="animate-spin text-[#2d6a4f] mx-auto mb-2" />
                      <span>Sedang memuat preview...</span>
                    </div>
                  )
                ) : originalPreview ? (
                  <motion.div
                    key={`orig-${activePage}`}
                    initial={{ opacity: 0, scale: 0.98 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.2 }}
                    className="bg-white rounded-lg shadow-xl p-2 border border-[#E2E8E2] max-w-full"
                  >
                    <img
                      src={originalPreview}
                      alt={`Original Preview Hal ${activePage}`}
                      className="max-h-[640px] w-auto object-contain rounded"
                    />
                  </motion.div>
                ) : (
                  <div className="text-center text-xs text-[#52796f]">
                    <Spinner size={24} className="animate-spin text-[#2d6a4f] mx-auto mb-2" />
                    <span>Sedang memuat gambar asli...</span>
                  </div>
                )
              ) : (
                /* Empty state matching the user's mockup */
                <div className="text-center p-8 max-w-xs">
                  <div className="w-16 h-16 rounded-2xl bg-[#e8f5e9] text-[#2d6a4f] flex items-center justify-center mx-auto mb-3.5 shadow-sm">
                    <BookOpen size={32} weight="duotone" />
                  </div>
                  <h3 className="text-sm font-bold text-[#1b4332] mb-1">
                    Belum Ada Dokumen
                  </h3>
                  <p className="text-xs text-[#52796f] leading-relaxed">
                    Upload file PDF Al-Qur'an di sebelah kiri untuk melihat hasil tracing dan mulai membuat lembar latihan.
                  </p>
                </div>
              )}
            </div>
          </section>
        </div>
      </main>

      {/* ── FOOTER ── */}
      <footer className="py-4 border-t border-[#D8E2DC] bg-white text-center text-xs text-[#52796f]">
        Trace Qur'an — Duta Ilmu • 100% Client-Side Processing • Tanpa Upload Server • Aman & Offline
      </footer>
    </div>
  );
}
