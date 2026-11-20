/**
 * lib/pdf-processor.ts
 * Browser-side PDF processing pipeline with precision slot & rosette preservation.
 * Runs entirely client-side using Canvas 2D and pdf-lib.
 * Zero API keys, 100% offline, zero server overhead.
 */

import { PDFDocument } from "pdf-lib";

export interface ProcessOptions {
  opacity: number;       // 0.08-0.50: fade level for Arabic text (default 0.18)
  keepWaqf: boolean;     // preserve margin waqf/ruku' marks (default true)
  keepAyat: boolean;     // preserve ayat rosette circles (default true)
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

interface Slot {
  yTop: number;
  yBot: number;
}

interface PageLayout {
  isVersePage: boolean;
  slots: Slot[];
  innerLeft: number;
  innerRight: number;
  horizLineMask: Uint8Array;
}

/**
 * Precision detection of Quran row divider lines, column frames, and slots.
 */
function analyzeQuranLayout(imageData: ImageData, scale: number): PageLayout {
  const { width, height, data } = imageData;
  const isDark = (idx: number) => {
    return (data[idx] + data[idx + 1] + data[idx + 2]) / 3 < 185;
  };

  const minHorizRun = Math.max(180, Math.floor(220 * (scale / 1.5)));
  const minVertRun = Math.max(140, Math.floor(180 * (scale / 1.5)));
  const minRowSpacing = Math.max(50, Math.floor(65 * (scale / 1.5)));
  const maxRowSpacing = Math.floor(135 * (scale / 1.5));

  // 1. Detect thin horizontal divider lines
  const horizLineRows = new Uint8Array(height);
  const horizLineMask = new Uint8Array(width * height);

  for (let y = 0; y < height; y++) {
    let maxRun = 0;
    let curRun = 0;
    const rowOffset = y * width;
    for (let x = 0; x < width; x++) {
      if (isDark((rowOffset + x) * 4)) {
        curRun++;
        if (curRun > maxRun) maxRun = curRun;
      } else {
        curRun = 0;
      }
    }
    if (maxRun >= minHorizRun) {
      horizLineRows[y] = 1;
      // Mark line pixels
      for (let x = 0; x < width; x++) {
        if (isDark((rowOffset + x) * 4)) {
          horizLineMask[rowOffset + x] = 1;
        }
      }
    }
  }

  // Group contiguous horizontal rows into single line positions
  const yLines: number[] = [];
  let inLine = false;
  let startY = 0;
  for (let y = 0; y < height; y++) {
    if (horizLineRows[y] === 1) {
      if (!inLine) {
        inLine = true;
        startY = y;
      }
    } else {
      if (inLine) {
        inLine = false;
        yLines.push(Math.floor((startY + y) / 2));
      }
    }
  }

  // Find regular Quran text slots
  const slots: Slot[] = [];
  for (let i = 0; i < yLines.length - 1; i++) {
    const spacing = yLines[i + 1] - yLines[i];
    if (spacing >= minRowSpacing && spacing <= maxRowSpacing) {
      slots.push({ yTop: yLines[i], yBot: yLines[i + 1] });
    }
  }

  // Non-verse pages (Cover, intro, tajwid guide) have < 5 regular slots
  const isVersePage = slots.length >= 5;

  // 2. Detect tall vertical frame lines
  const vertLineCols: number[] = [];
  for (let x = 0; x < width; x++) {
    let maxRun = 0;
    let curRun = 0;
    for (let y = 0; y < height; y++) {
      if (isDark((y * width + x) * 4)) {
        curRun++;
        if (curRun > maxRun) maxRun = curRun;
      } else {
        curRun = 0;
      }
    }
    if (maxRun >= minVertRun) {
      vertLineCols.push(x);
    }
  }

  const midX = width / 2;
  const leftCols = vertLineCols.filter((x) => x < midX);
  const rightCols = vertLineCols.filter((x) => x >= midX);

  const innerLeft = leftCols.length > 0 ? leftCols[leftCols.length - 1] + 2 : Math.floor(width * 0.14);
  const innerRight = rightCols.length > 0 ? rightCols[0] - 2 : Math.floor(width * 0.88);

  return {
    isVersePage,
    slots,
    innerLeft,
    innerRight,
    horizLineMask,
  };
}

/**
 * Detect Ayah rosette circles using connected component analysis in valid slots.
 */
function findAyahRosetteMask(
  imageData: ImageData,
  layout: PageLayout,
  scale: number,
): Uint8Array {
  const { width, height, data } = imageData;
  const rosetteMask = new Uint8Array(width * height);
  if (!layout.isVersePage) return rosetteMask;

  const minRosetteSize = Math.max(22, Math.floor(28 * (scale / 1.5)));
  const maxRosetteSize = Math.floor(75 * (scale / 1.5));
  const minPixels = Math.max(160, Math.floor(240 * (scale / 1.5)));

  // Analyze dark connected components within each verse slot
  const visited = new Uint8Array(width * height);
  const queueX = new Int32Array(width * height);
  const queueY = new Int32Array(width * height);

  for (const slot of layout.slots) {
    const yStart = slot.yTop + 2;
    const yEnd = slot.yBot - 2;

    for (let y = yStart; y <= yEnd; y++) {
      const rowOffset = y * width;
      for (let x = layout.innerLeft; x <= layout.innerRight; x++) {
        const offset = rowOffset + x;
        if (visited[offset]) continue;

        const idx = offset * 4;
        const brightness = (data[idx] + data[idx + 1] + data[idx + 2]) / 3;
        if (brightness >= 185) continue; // background

        // BFS connected component
        let qHead = 0;
        let qTail = 0;
        queueX[qTail] = x;
        queueY[qTail] = y;
        qTail++;
        visited[offset] = 1;

        let minX = x, maxX = x, minY = y, maxY = y;
        let count = 0;

        while (qHead < qTail) {
          const cx = queueX[qHead];
          const cy = queueY[qHead];
          qHead++;
          count++;

          if (cx < minX) minX = cx;
          if (cx > maxX) maxX = cx;
          if (cy < minY) minY = cy;
          if (cy > maxY) maxY = cy;

          // 4-connected neighbors
          const neighbors = [
            [cx + 1, cy], [cx - 1, cy],
            [cx, cy + 1], [cx, cy - 1]
          ];

          for (const [nx, ny] of neighbors) {
            if (nx >= layout.innerLeft && nx <= layout.innerRight && ny >= yStart && ny <= yEnd) {
              const noff = ny * width + nx;
              if (!visited[noff]) {
                const nidx = noff * 4;
                const nb = (data[nidx] + data[nidx + 1] + data[nidx + 2]) / 3;
                if (nb < 185) {
                  visited[noff] = 1;
                  queueX[qTail] = nx;
                  queueY[qTail] = ny;
                  qTail++;
                }
              }
            }
          }
        }

        const bw = maxX - minX + 1;
        const bh = maxY - minY + 1;
        const aspect = bw / bh;

        // Ayah Rosette characteristics: symmetrical, dense, medium size
        if (
          bw >= minRosetteSize && bw <= maxRosetteSize &&
          bh >= minRosetteSize && bh <= maxRosetteSize &&
          aspect >= 0.70 && aspect <= 1.30 &&
          count >= minPixels
        ) {
          const pad = 3;
          const py1 = Math.max(0, minY - pad);
          const py2 = Math.min(height - 1, maxY + pad);
          const px1 = Math.max(0, minX - pad);
          const px2 = Math.min(width - 1, maxX + pad);

          for (let ry = py1; ry <= py2; ry++) {
            const roff = ry * width;
            for (let rx = px1; rx <= px2; rx++) {
              rosetteMask[roff + rx] = 1;
            }
          }
        }
      }
    }
  }

  return rosetteMask;
}

/**
 * Apply precision fading only to Arabic verse text inside valid line slots.
 */
function applyPrecisionFade(
  imageData: ImageData,
  layout: PageLayout,
  rosetteMask: Uint8Array,
  opacity: number,
  keepAyat: boolean,
): void {
  if (!layout.isVersePage) return; // Leave cover / non-verse pages 100% untouched

  const { width, data } = imageData;

  // Build slot lookup
  const inSlot = new Uint8Array(imageData.width * imageData.height);
  for (const slot of layout.slots) {
    const y1 = slot.yTop + 2;
    const y2 = slot.yBot - 2;
    for (let y = y1; y <= y2; y++) {
      const rowOffset = y * width;
      for (let x = layout.innerLeft; x <= layout.innerRight; x++) {
        inSlot[rowOffset + x] = 1;
      }
    }
  }

  for (let offset = 0; offset < inSlot.length; offset++) {
    // Only fade pixels that are inside a valid verse slot
    if (!inSlot[offset]) continue;

    // Do NOT fade horizontal lines
    if (layout.horizLineMask[offset]) continue;

    // Do NOT fade Ayah rosettes if keepAyat is true
    if (keepAyat && rosetteMask[offset]) continue;

    const idx = offset * 4;
    const r = data[idx];
    const g = data[idx + 1];
    const b = data[idx + 2];
    const brightness = (r + g + b) / 3;

    // Fade dark verse text & harakat smoothly
    if (brightness < 190) {
      data[idx]     = Math.round(r * opacity + 255 * (1 - opacity));
      data[idx + 1] = Math.round(g * opacity + 255 * (1 - opacity));
      data[idx + 2] = Math.round(b * opacity + 255 * (1 - opacity));
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

  // Analyze page structure
  const layout = analyzeQuranLayout(imageData, scale);

  if (layout.isVersePage) {
    const rosetteMask = findAyahRosetteMask(imageData, layout, scale);
    applyPrecisionFade(imageData, layout, rosetteMask, options.opacity, options.keepAyat ?? true);
    ctx.putImageData(imageData, 0, 0);
  }

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
  return processOnePage(page, options, 140);
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
