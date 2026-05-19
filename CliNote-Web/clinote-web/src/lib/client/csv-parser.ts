/**
 * Lightweight CSV parser for MIMIC-format files.
 * Handles:
 *  - quoted fields containing commas
 *  - quoted fields containing newlines (important for clinical notes!)
 *  - escaped double-quotes ("")
 *  - \r\n and \n line endings
 */

export interface ParsedCsv {
  headers: string[];
  rows: Record<string, string>[];
}

export function parseCsv(text: string): ParsedCsv {
  // Strip BOM if present
  if (text.charCodeAt(0) === 0xfeff) {
    text = text.slice(1);
  }

  const records: string[][] = [];
  let current: string[] = [];
  let field = "";
  let inQuotes = false;

  for (let i = 0; i < text.length; i++) {
    const ch = text[i];

    if (inQuotes) {
      if (ch === '"') {
        if (text[i + 1] === '"') {
          // Escaped quote
          field += '"';
          i++;
        } else {
          inQuotes = false;
        }
      } else {
        field += ch;
      }
      continue;
    }

    if (ch === '"') {
      inQuotes = true;
      continue;
    }

    if (ch === ",") {
      current.push(field);
      field = "";
      continue;
    }

    if (ch === "\r") {
      // Handle \r\n
      if (text[i + 1] === "\n") i++;
      current.push(field);
      field = "";
      pushRecord(records, current);
      current = [];
      continue;
    }

    if (ch === "\n") {
      current.push(field);
      field = "";
      pushRecord(records, current);
      current = [];
      continue;
    }

    field += ch;
  }

  // Final field
  if (field.length > 0 || current.length > 0) {
    current.push(field);
    pushRecord(records, current);
  }

  if (records.length === 0) {
    return { headers: [], rows: [] };
  }

  const headers = records[0].map((h) => h.trim());
  const rows = records.slice(1).map((rec) => {
    const obj: Record<string, string> = {};
    headers.forEach((h, idx) => {
      obj[h] = (rec[idx] ?? "").trim();
    });
    return obj;
  });

  return { headers, rows };
}

function pushRecord(records: string[][], rec: string[]): void {
  // Skip entirely empty lines
  if (rec.length === 1 && rec[0] === "") return;
  records.push(rec);
}

/** Parse a CSV number field — returns `null` for empty or invalid values. */
export function parseCsvNumber(value: string | undefined): number | null {
  if (!value || value === "___") return null;
  const n = Number(value);
  return Number.isFinite(n) ? n : null;
}

/**
 * Parse a MIMIC datetime like "2180-05-06 22:23:00" or "5/6/2180 21:19".
 * Returns ISO string or null if unparseable.
 */
export function parseCsvDate(value: string | undefined): string | null {
  if (!value) return null;
  // JS Date handles both "2180-05-06 22:23:00" and "5/6/2180 21:19"
  const d = new Date(value.replace(" ", "T"));
  if (!Number.isNaN(d.getTime())) return d.toISOString();
  // Try MDY format like "5/6/2180 21:19"
  const mdy = value.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})\s+(\d{1,2}):(\d{2})/);
  if (mdy) {
    const [, m, day, y, hh, mm] = mdy;
    const d2 = new Date(
      Number(y),
      Number(m) - 1,
      Number(day),
      Number(hh),
      Number(mm),
    );
    if (!Number.isNaN(d2.getTime())) return d2.toISOString();
  }
  return null;
}
