/**
 * lib/pdf-processor.ts
 * Browser-side PDF & Image processing pipeline with precision slot & rosette preservation.
 * Supports Model A (Light Gray) & Model B (Outline / Hollow).
 * Runs 100% client-side - zero server, zero API key, 100% offline.
 */

import { PDFDocument } from "pdf-lib";

export type TracingModel = "gray" | "outline";

export interface ProcessOptions {
  model?: TracingModel;  // "gray" (default) or "outline"
  opacity: number;       // for gray: 0.08-0.50 (default 0.18)
  outlineWidth?: number; // for outline: 1 or 2 (default 1)
  keepWaqf: boolean;     // preserve margin waqf/ruku' marks (default true)
  keepAyat: boolean;     // preserve ayat rosette circles (default true)
  dpi?: number;          // render DPI
}

export type ProgressCallback = (done: number, total: number) => void;

// --- PDF.js dynamic import (avoid SSR issues) ---
let pdfjsLib: typeof import("pdfjs-dist") | null = null;

async function getPdfjs() {
  if (!pdfjsLib) {
    pdfjsLib = await import("pdfjs-dist");
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
 * Scales dynamically to any canvas DPI / resolution.
 */
function analyzeQuranLayout(imageData: ImageData): PageLayout {
  const { width, height, data } = imageData;
  const isDark = (idx: number) => {
    return (data[idx] + data[idx + 1] + data[idx + 2]) / 3 < 185;
  };

  // Proportional parameters (resolution independent)
  const minHorizRun = Math.round(width * 0.25);
  const minVertRun = Math.round(height * 0.12);
  const minRowSpacing = Math.round(height * 0.048);
  const maxRowSpacing = Math.round(height * 0.082);

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
      for (let x = 0; x < width; x++) {
        if (isDark((rowOffset + x) * 4)) {
          horizLineMask[rowOffset + x] = 1;
        }
      }
    }
  }

  // Group contiguous horizontal rows into line positions
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
): Uint8Array {
  const { width, height, data } = imageData;
  const rosetteMask = new Uint8Array(width * height);
  if (!layout.isVersePage) return rosetteMask;

  const minRosetteW = Math.round(width * 0.035);
  const maxRosetteW = Math.round(width * 0.080);
  const minRosetteH = Math.round(height * 0.025);
  const maxRosetteH = Math.round(height * 0.060);
  const minPixels = Math.round(width * height * 0.00050);

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
        if (brightness >= 185) continue;

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
        const fillDensity = count / (bw * bh);

        // Check horizontal transitions to ensure it is an ornate rosette (outer ring + inner ring + digit)
        // and NOT a solid Arabic word (like 'بِكُمْ' or 'ذَهَبَ')
        let maxHTransitions = 0;
        const sampleYs = [
          Math.floor((minY + maxY) / 2),
          Math.floor((minY + maxY) / 2) - 3,
          Math.floor((minY + maxY) / 2) + 3,
        ];

        for (const testY of sampleYs) {
          if (testY >= yStart && testY <= yEnd) {
            let transitions = 0;
            let lastDark = false;
            for (let x = minX; x <= maxX; x++) {
              const o = (testY * width + x) * 4;
              const isDarkPixel = (data[o] + data[o + 1] + data[o + 2]) / 3 < 185;
              if (isDarkPixel !== lastDark) {
                transitions++;
                lastDark = isDarkPixel;
              }
            }
            if (transitions > maxHTransitions) maxHTransitions = transitions;
          }
        }

        if (
          bw >= minRosetteW && bw <= maxRosetteW &&
          bh >= minRosetteH && bh <= maxRosetteH &&
          aspect >= 0.70 && aspect <= 1.30 &&
          count >= minPixels &&
          fillDensity <= 0.38 && // Exclude solid Arabic words
          maxHTransitions >= 5  // Must have nested circular/petal transitions
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
 * Apply precision fading (Model A: Light Gray or Model B: Outline).
 */
function applyPrecisionFade(
  imageData: ImageData,
  layout: PageLayout,
  rosetteMask: Uint8Array,
  options: ProcessOptions,
): void {
  if (!layout.isVersePage) return;

  const { width, height, data } = imageData;
  const model = options.model ?? "gray";
  const opacity = options.opacity ?? 0.18;
  const keepAyat = options.keepAyat ?? true;

  // Build slot lookup
  const inSlot = new Uint8Array(width * height);
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

  // Pre-calculate dark text mask for outline computation
  const isTextPixel = new Uint8Array(width * height);
  for (let offset = 0; offset < inSlot.length; offset++) {
    if (!inSlot[offset]) continue;
    if (layout.horizLineMask[offset]) continue;
    if (keepAyat && rosetteMask[offset]) continue;

    const idx = offset * 4;
    const b = (data[idx] + data[idx + 1] + data[idx + 2]) / 3;
    if (b < 190) {
      isTextPixel[offset] = 1;
    }
  }

  if (model === "outline") {
    // MODEL B: Outline (Hollow Letters)
    // Edge pixel = text pixel adjacent to at least one non-text pixel
    for (let y = 1; y < height - 1; y++) {
      const rowOffset = y * width;
      for (let x = layout.innerLeft; x <= layout.innerRight; x++) {
        const offset = rowOffset + x;
        if (!isTextPixel[offset]) continue;

        // Check 8-neighborhood
        const isEdge =
          !isTextPixel[offset - 1] ||
          !isTextPixel[offset + 1] ||
          !isTextPixel[offset - width] ||
          !isTextPixel[offset + width] ||
          !isTextPixel[offset - width - 1] ||
          !isTextPixel[offset - width + 1] ||
          !isTextPixel[offset + width - 1] ||
          !isTextPixel[offset + width + 1];

        const idx = offset * 4;
        if (isEdge) {
          // Sharp gray outline line
          const lineVal = Math.round(110 * (1 - opacity * 0.5));
          data[idx] = lineVal;
          data[idx + 1] = lineVal;
          data[idx + 2] = lineVal;
        } else {
          // Hollow white inside
          data[idx] = 255;
          data[idx + 1] = 255;
          data[idx + 2] = 255;
        }
      }
    }
  } else {
    // MODEL A: Light Gray (FunFurqan standard)
    for (let offset = 0; offset < inSlot.length; offset++) {
      if (!isTextPixel[offset]) continue;

      const idx = offset * 4;
      const r = data[idx];
      const g = data[idx + 1];
      const b = data[idx + 2];

      data[idx]     = Math.round(r * opacity + 255 * (1 - opacity));
      data[idx + 1] = Math.round(g * opacity + 255 * (1 - opacity));
      data[idx + 2] = Math.round(b * opacity + 255 * (1 - opacity));
    }
  }
}

// --- Render Original Page (for "Gambar Asli" tab) ---
export async function renderOriginalPage(
  file: File,
  pageNum: number,
  dpi = 140,
): Promise<string> {
  const pdfjs = await getPdfjs();
  const arrayBuffer = await file.arrayBuffer();
  const pdfDoc = await pdfjs.getDocument({ data: arrayBuffer }).promise;
  const page = await pdfDoc.getPage(pageNum);

  const scale = dpi / 72;
  const viewport = page.getViewport({ scale });
  const canvas = document.createElement("canvas");
  canvas.width = Math.round(viewport.width);
  canvas.height = Math.round(viewport.height);
  const ctx = canvas.getContext("2d")!;

  await page.render({ canvasContext: ctx, viewport }).promise;
  return canvas.toDataURL("image/jpeg", 0.92);
}

// --- Process single page to canvas ---
async function processOnePage(
  pdfPage: import("pdfjs-dist").PDFPageProxy,
  options: ProcessOptions,
  dpi: number,
): Promise<string> {
  const scale = dpi / 72;
  const viewport = pdfPage.getViewport({ scale });

  const canvas = document.createElement("canvas");
  canvas.width = Math.round(viewport.width);
  canvas.height = Math.round(viewport.height);
  const ctx = canvas.getContext("2d", { willReadFrequently: true })!;

  await pdfPage.render({ canvasContext: ctx, viewport }).promise;

  const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
  const layout = analyzeQuranLayout(imageData);

  if (layout.isVersePage) {
    const rosetteMask = findAyahRosetteMask(imageData, layout);
    applyPrecisionFade(imageData, layout, rosetteMask, options);
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
  pageRange?: { start: number; end: number },
): Promise<void> {
  const pdfjs = await getPdfjs();

  const arrayBuffer = await file.arrayBuffer();
  const pdfDoc = await pdfjs.getDocument({ data: arrayBuffer }).promise;
  const totalPages = pdfDoc.numPages;

  const startPage = pageRange ? Math.max(1, pageRange.start) : 1;
  const endPage = pageRange ? Math.min(totalPages, pageRange.end) : totalPages;
  const pagesToProcess = endPage - startPage + 1;

  const outDoc = await PDFDocument.create();
  const outputDpi = options.dpi ?? 180;

  let processedCount = 0;
  for (let i = startPage; i <= endPage; i++) {
    if (cancelRef.cancelled) throw new Error("Dibatalkan");

    const page = await pdfDoc.getPage(i);
    const dataUrl = await processOnePage(page, options, outputDpi);

    const jpegBytes = dataUrlToUint8Array(dataUrl);
    const jpegImage = await outDoc.embedJpg(jpegBytes);

    const viewport = page.getViewport({ scale: 1 });
    const pdfPage = outDoc.addPage([viewport.width, viewport.height]);
    pdfPage.drawImage(jpegImage, {
      x: 0, y: 0,
      width: viewport.width,
      height: viewport.height,
    });

    processedCount++;
    onProgress(processedCount, pagesToProcess);
  }

  const pdfBytes = await outDoc.save();
  const blob = new Blob([pdfBytes as unknown as BlobPart], { type: "application/pdf" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  const suffix = options.model === "outline" ? "_trace_outline.pdf" : "_trace.pdf";
  a.download = file.name.replace(/\.pdf$/i, suffix);
  a.click();
  URL.revokeObjectURL(url);
}

// --- Process single image file (JPG / PNG) ---
export async function processSingleImage(
  imageFile: File,
  options: ProcessOptions,
): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const img = new Image();
      img.onload = () => {
        const canvas = document.createElement("canvas");
        canvas.width = img.width;
        canvas.height = img.height;
        const ctx = canvas.getContext("2d", { willReadFrequently: true })!;
        ctx.drawImage(img, 0, 0);

        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const layout = analyzeQuranLayout(imageData);
        if (layout.isVersePage) {
          const rosetteMask = findAyahRosetteMask(imageData, layout);
          applyPrecisionFade(imageData, layout, rosetteMask, options);
          ctx.putImageData(imageData, 0, 0);
        }
        resolve(canvas.toDataURL("image/jpeg", 0.92));
      };
      img.onerror = reject;
      img.src = e.target?.result as string;
    };
    reader.onerror = reject;
    reader.readAsDataURL(imageFile);
  });
}

// --- Preview single page ---
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
