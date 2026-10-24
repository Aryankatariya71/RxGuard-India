/** Browser-local OCR via bundled tesseract.js + eng.traineddata (no image upload). */

import type { Worker } from 'tesseract.js'

let workerPromise: Promise<Worker> | null = null

async function getWorker(): Promise<Worker> {
  if (!workerPromise) {
    workerPromise = (async () => {
      const { createWorker } = await import('tesseract.js')
      return createWorker('eng', 1, {
        workerPath: '/tesseract/worker.min.js',
        corePath: '/tesseract/tesseract-core-simd-lstm.wasm.js',
        langPath: '/tessdata',
        gzip: true,
        logger: () => undefined,
      })
    })()
  }
  return workerPromise
}

export async function recognizeImageLocal(source: File | Blob | string): Promise<string> {
  const worker = await getWorker()
  const { data } = await worker.recognize(source)
  return (data.text || '').trim()
}

export async function terminateOcrWorker(): Promise<void> {
  if (!workerPromise) return
  const w = await workerPromise
  await w.terminate()
  workerPromise = null
}
