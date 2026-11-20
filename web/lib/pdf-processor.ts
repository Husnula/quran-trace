/**
 * lib/pdf-processor.ts
 * Browser-side PDF processing pipeline.
 * Uses pdf.js to render, Canvas 2D to fade, pdf-lib to output.
 * Runs entirely client-side - no server, no upload.
 */

import { PDFDocument } from "pdf-lib";

export interface ProcessOptions {
  opacity: number;       // 0.08-0.60: fade level for Arabic text
  keepWaqf: boolean;     // preserve small waqf marks
  keepAyat: boolean;     // preserve ayat circle numbers
  dpi?: number;          // render DPI (default 150 for web preview, 200 for output)
}

export interface PageResult {
  pageNum: number;
  dataUrl: string;       // PNG data URL for preview
}

export type ProgressCallback = (done: number, total: number) => void;

// --- PDF.js dynamic import (avoid SSR issues) ---
let pdfjsLib: typeof import("pdfjs-dist") | null = null;

async function getPdfjs() {
  if (!pdfjsLib) {
    pdfjsLib = await import("pdfjs-dist");
    // Worker via CDN (avoids bundler issues with static export)
    pdfjsLib.GlobalWorkerOptions.workerSrc = `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.mjs`;
  }
  return pdfjsLib;
}

// --- Region detection (port of Python logic) ---
interface Zone {
  x1: number; y1: number; x2: number; y2: number;
}

function detectTextZone(imageData: ImageData, innerMargin = 50): Zone {
  const { width, height, data } = imageData;

  // Build grayscale + dark pixel column/row density
  const colDensity = new Float32Array(width);
  const rowDensity = new Float32Array(height);

  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const idx = (y * width + x) * 4;
      const brightness = (data[idx] + data[idx + 1] + data[idx + 2]) / 3;
      if (brightness < 180) {
        colDensity[x] += 100 / height;
        rowDensity[y] += 100 / width;
      }
    }
  }

  const THRESH = 12;
  const THIRD = Math.floor(width / 3);
  const H_FIFTH = Math.floor(height / 5);

  // Find left border edge
  let leftX = Math.floor(width * 0.08);
  outer: for (let x = 0; x < THIRD; x++) {
    if (colDensity[x] > THRESH) {
      for (let x2 = x; x2 < THIRD; x2++) {
        if (colDensity[x2] < THRESH * 0.3) { leftX = x2; break outer; }
      }
    }
  }

  // Find right border edge
  let rightX = Math.floor(width * 0.92);
  outer: for (let x = width - 1; x > width * 2 / 3; x--) {
    if (colDensity[x] > THRESH) {
      for (let x2 = x; x2 > width * 2 / 3; x2--) {
        if (colDensity[x2] < THRESH * 0.3) { rightX = x2; break outer; }
      }
    }
  }

  // Find top border edge
  let topY = Math.floor(height * 0.05);
  outer: for (let y = 0; y < H_FIFTH; y++) {
    if (rowDensity[y] > THRESH) {
      for (let y2 = y; y2 < H_FIFTH; y2++) {
        if (rowDensity[y2] < THRESH * 0.3) { topY = y2; break outer; }
      }
    }
  }

  // Find bottom border edge
  let bottomY = Math.floor(height * 0.95);
  outer: for (let y = height - 1; y > height * 4 / 5; y--) {
    if (rowDensity[y] > THRESH) {
      for (let y2 = y; y2 > height * 4 / 5; y2--) {
        if (rowDensity[y2] < THRESH * 0.3) { bottomY = y2; break outer; }
      }
    }
  }

  let x1 = Math.min(leftX + innerMargin, Math.floor(width / 2));
  let x2 = Math.max(rightX - innerMargin, Math.floor(width / 2));
  let y1 = Math.min(topY + Math.floor(innerMargin / 2), Math.floor(height / 2));
  let y2 = Math.max(bottomY - Math.floor(innerMargin / 2), Math.floor(height / 2));

  // Fallback if zone is too small
  if (x2 - x1 < width * 0.3 || y2 - y1 < height * 0.3) {
    const mx = Math.floor(width * 0.08);
    const my = Math.floor(height * 0.05);
    return { x1: mx, y1: my, x2: width - mx, y2: height - my };
  }

  return { x1, y1, x2, y2 };
}

// --- Fade engine ---
function applyFade(
  imageData: ImageData,
  zone: Zone,
  opacity: number,
  keepWaqf: boolean,
): void {
  const { width, data } = imageData;
  const DARK_THRESH = 200; // pixel dengan rata-rata RGB < ini dianggap teks

  for (let y = zone.y1; y < zone.y2; y++) {
    for (let x = zone.x1; x < zone.x2; x++) {
      const idx = (y * width + x) * 4;
      const r = data[idx], g = data[idx + 1], b = data[idx + 2];
      const brightness = (r + g + b) / 3;

      if (brightness < DARK_THRESH) {
        // Blend pixel gelap ke putih sesuai opacity
        data[idx]     = Math.round(r * opacity + 255 * (1 - opacity));
        data[idx + 1] = Math.round(g * opacity + 255 * (1 - opacity));
        data[idx + 2] = Math.round(b * opacity + 255 * (1 - opacity));
      }
    }
  }
}

// --- Single page processor ---
async function processOnePage(
  pdfPage: import("pdfjs-dist").PDFPageProxy,
  options: ProcessOptions,
  dpi: number,
): Promise<string> {
  const scale = dpi / 72;
  const viewport = pdfPage.getViewport({ scale });

  const canvas = document.createElement("canvas");
  canvas.width = viewport.width;
  canvas.height = viewport.height;
  const ctx = canvas.getContext("2d", { willReadFrequently: true })!;

  // Render PDF page to canvas
  await pdfPage.render({ canvasContext: ctx, viewport }).promise;

  // Get pixel data
  const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);

  // Detect text zone (inside border)
  const zone = detectTextZone(imageData, 50);

  // Apply fade
  applyFade(imageData, zone, options.opacity, options.keepWaqf);

  // Write back
  ctx.putImageData(imageData, 0, 0);

  return canvas.toDataURL("image/jpeg", 0.92);
}

// --- Main: process all pages → download PDF ---
export async function processPdf(
  file: File,
  options: ProcessOptions,
  onProgress: ProgressCallback,
  cancelRef: { cancelled: boolean },
): Promise<void> {
  const pdfjs = await getPdfjs();

  const arrayBuffer = await file.arrayBuffer();
  const pdfDoc = await pdfjs.getDocument({ data: arrayBuffer }).promise;
  const totalPages = pdfDoc.numPages;

  // Output PDF
  const outDoc = await PDFDocument.create();
  const outputDpi = options.dpi ?? 180;

  for (let i = 1; i <= totalPages; i++) {
    if (cancelRef.cancelled) throw new Error("Dibatalkan");

    const page = await pdfDoc.getPage(i);
    const dataUrl = await processOnePage(page, options, outputDpi);

    // Embed JPEG into output PDF
    const jpegBytes = dataUrlToUint8Array(dataUrl);
    const jpegImage = await outDoc.embedJpg(jpegBytes);

    // Page size: match original (in PDF points)
    const viewport = page.getViewport({ scale: 1 });
    const pdfPage = outDoc.addPage([viewport.width, viewport.height]);
    pdfPage.drawImage(jpegImage, {
      x: 0, y: 0,
      width: viewport.width,
      height: viewport.height,
    });

    onProgress(i, totalPages);
  }

  // Trigger download
  const pdfBytes = await outDoc.save();
  const blob = new Blob([pdfBytes as unknown as BlobPart], { type: "application/pdf" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = file.name.replace(/\.pdf$/i, "_trace.pdf");
  a.click();
  URL.revokeObjectURL(url);
}

// --- Preview: render ONE page (for preview panel) ---
export async function previewPage(
  file: File,
  pageNum: number,
  options: ProcessOptions,
): Promise<string> {
  const pdfjs = await getPdfjs();
  const arrayBuffer = await file.arrayBuffer();
  const pdfDoc = await pdfjs.getDocument({ data: arrayBuffer }).promise;
  const page = await pdfDoc.getPage(pageNum);
  return processOnePage(page, options, 120); // lower DPI for fast preview
}

export async function getPdfPageCount(file: File): Promise<number> {
  const pdfjs = await getPdfjs();
  const arrayBuffer = await file.arrayBuffer();
  const pdfDoc = await pdfjs.getDocument({ data: arrayBuffer }).promise;
  return pdfDoc.numPages;
}

function dataUrlToUint8Array(dataUrl: string): Uint8Array {
  const base64 = dataUrl.split(",")[1];
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  return bytes;
}
