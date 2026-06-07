import { clampCorrectLetters, normalizeOptionCount, parseCorrectLetters } from "./questionOptions";

export type QuestionDraft = {
  position: number;
  text: string;
  option_count: number;
  option_a: string;
  option_b: string;
  option_c: string;
  option_d: string;
  correct: string[];
};

const MAX_QUESTIONS = 10;

export type ParsedQuestionRow = {
  text: string;
  option_a: string;
  option_b: string;
  option_c: string;
  option_d: string;
  correct: string[];
  option_count: number;
};

function stripHtml(value: string): string {
  return value.replace(/<[^>]+>/g, "").trim();
}

function inferOptionCount(row: {
  option_a: string;
  option_b: string;
  option_c: string;
  option_d: string;
}): number {
  const opts = [row.option_a, row.option_b, row.option_c, row.option_d].map(stripHtml);
  let last = 2;
  opts.forEach((value, index) => {
    if (value) last = index + 1;
  });
  return normalizeOptionCount(Math.max(2, last));
}

function normalizeCorrect(raw: string, optionCount: number): string[] {
  return parseCorrectLetters(raw, optionCount);
}

function rowFromCells(cells: string[], defaultOptionCount: number): ParsedQuestionRow | null {
  const text = (cells[0] ?? "").trim();
  if (!text) return null;
  const explicitCount = Number((cells[6] ?? "").trim());
  const row = {
    text,
    option_a: (cells[1] ?? "").trim(),
    option_b: (cells[2] ?? "").trim(),
    option_c: (cells[3] ?? "").trim(),
    option_d: (cells[4] ?? "").trim(),
    correct: normalizeCorrect(cells[5] ?? "A", defaultOptionCount),
    option_count: 0,
  };
  row.option_count = Number.isFinite(explicitCount) && explicitCount >= 2 && explicitCount <= 4
    ? normalizeOptionCount(explicitCount)
    : inferOptionCount(row);
  row.correct = normalizeCorrect(cells[5] ?? "A", row.option_count);
  return row;
}

function isHeaderRow(cells: string[]): boolean {
  const joined = cells.join(" ").toLowerCase();
  return (
    joined.includes("формулиров") ||
    joined.includes("вопрос") ||
    joined.includes("вариант") ||
    joined.includes("ответ") ||
    joined.includes("количество")
  );
}

function parseDelimitedText(text: string, delimiter: string, defaultOptionCount: number): ParsedQuestionRow[] {
  const lines = text.split(/\r?\n/).map((l) => l.trim()).filter(Boolean);
  const rows: ParsedQuestionRow[] = [];
  for (let i = 0; i < lines.length && rows.length < MAX_QUESTIONS; i++) {
    const cells = lines[i].split(delimiter).map((c) => c.trim().replace(/^"|"$/g, ""));
    if (i === 0 && isHeaderRow(cells)) continue;
    const row = rowFromCells(cells, defaultOptionCount);
    if (row) rows.push(row);
  }
  return rows;
}

function parsePlainBlocks(text: string, defaultOptionCount: number): ParsedQuestionRow[] {
  const blocks = text.split(/\n\s*\n/).map((b) => b.trim()).filter(Boolean);
  const rows: ParsedQuestionRow[] = [];
  for (const block of blocks) {
    if (rows.length >= MAX_QUESTIONS) break;
    const lines = block.split(/\r?\n/).map((l) => l.trim()).filter(Boolean);
    if (lines.length === 0) continue;
    if (lines.length === 1) {
      rows.push({
        text: lines[0],
        option_a: "",
        option_b: "",
        option_c: "",
        option_d: "",
        correct: ["A"],
        option_count: defaultOptionCount,
      });
      continue;
    }
    const cells = lines.flatMap((line) => line.split("\t").map((c) => c.trim()));
    const row = rowFromCells(cells, defaultOptionCount);
    if (row) rows.push(row);
  }
  return rows;
}

async function parseExcel(file: File, defaultOptionCount: number): Promise<ParsedQuestionRow[]> {
  const XLSX = await import("xlsx");
  const buffer = await file.arrayBuffer();
  const workbook = XLSX.read(buffer, { type: "array" });
  const sheet = workbook.Sheets[workbook.SheetNames[0]];
  if (!sheet) return [];
  const matrix = XLSX.utils.sheet_to_json<(string | number)[]>(sheet, {
    header: 1,
    defval: "",
    raw: false,
  }) as (string | number)[][];
  const rows: ParsedQuestionRow[] = [];
  for (let i = 0; i < matrix.length && rows.length < MAX_QUESTIONS; i++) {
    const cells = matrix[i].map((c) => String(c ?? "").trim());
    if (i === 0 && isHeaderRow(cells)) continue;
    const row = rowFromCells(cells, defaultOptionCount);
    if (row) rows.push(row);
  }
  return rows;
}

export async function parseQuestionsFromFile(
  file: File,
  defaultOptionCount: number
): Promise<ParsedQuestionRow[]> {
  const name = file.name.toLowerCase();
  if (name.endsWith(".xlsx") || name.endsWith(".xls")) {
    return parseExcel(file, defaultOptionCount);
  }
  const text = await file.text();
  if (name.endsWith(".csv") || name.endsWith(".tsv")) {
    return parseDelimitedText(text, name.endsWith(".tsv") ? "\t" : ",", defaultOptionCount);
  }
  if (text.includes("\t") && text.includes("\n")) {
    const fromTsv = parseDelimitedText(text, "\t", defaultOptionCount);
    if (fromTsv.length > 0) return fromTsv;
  }
  if (text.includes(",") && text.includes("\n")) {
    const fromCsv = parseDelimitedText(text, ",", defaultOptionCount);
    if (fromCsv.length > 0) return fromCsv;
  }
  return parsePlainBlocks(text, defaultOptionCount);
}

export function importedRowsToDrafts(rows: ParsedQuestionRow[]): QuestionDraft[] {
  return rows.slice(0, MAX_QUESTIONS).map((row, idx) => ({
    position: idx + 1,
    text: row.text,
    option_count: row.option_count,
    option_a: row.option_a,
    option_b: row.option_b,
    option_c: row.option_c,
    option_d: row.option_d,
    correct: clampCorrectLetters(row.correct, row.option_count),
  }));
}

export const TICKET_IMPORT_ACCEPT =
  ".txt,.csv,.tsv,.xlsx,.xls,text/plain,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel";
