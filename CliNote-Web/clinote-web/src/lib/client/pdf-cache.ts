/**
 * Tiny IndexedDB-backed cache for PDFs the doctor has staged but not yet
 * analyzed. Survives page reloads — File objects in component state don't.
 * Scoped per patientId so different patients don't clobber each other.
 *
 * No external dependency (native IDB wrapped in promises).
 */

const DB_NAME = "clinote";
const DB_VERSION = 1;
const STORE = "staged_pdfs";

interface StagedPdf {
  buffer: ArrayBuffer;
  name: string;
  type: string;
}

function openDB(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, DB_VERSION);
    req.onupgradeneeded = () => {
      const db = req.result;
      if (!db.objectStoreNames.contains(STORE)) {
        db.createObjectStore(STORE);
      }
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

export async function savePdf(patientId: string, file: File): Promise<void> {
  if (typeof window === "undefined") return;
  const buffer = await file.arrayBuffer();
  const db = await openDB();
  await new Promise<void>((resolve, reject) => {
    const tx = db.transaction(STORE, "readwrite");
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
    const data: StagedPdf = { buffer, name: file.name, type: file.type };
    tx.objectStore(STORE).put(data, patientId);
  });
}

export async function loadPdf(patientId: string): Promise<File | null> {
  if (typeof window === "undefined") return null;
  const db = await openDB();
  return await new Promise<File | null>((resolve, reject) => {
    const tx = db.transaction(STORE, "readonly");
    const req = tx.objectStore(STORE).get(patientId);
    req.onsuccess = () => {
      const data = req.result as StagedPdf | undefined;
      if (!data) return resolve(null);
      resolve(new File([data.buffer], data.name, { type: data.type }));
    };
    req.onerror = () => reject(req.error);
  });
}

export async function deletePdf(patientId: string): Promise<void> {
  if (typeof window === "undefined") return;
  const db = await openDB();
  await new Promise<void>((resolve, reject) => {
    const tx = db.transaction(STORE, "readwrite");
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
    tx.objectStore(STORE).delete(patientId);
  });
}
