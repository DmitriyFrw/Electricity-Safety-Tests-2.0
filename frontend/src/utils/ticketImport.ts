import { clampCorrectLetter } from "./questionOptions";

export type QuestionDraft = {
  position: number;
  text: string;
  option_a: string;
  option_b: string;
  option_c: string;
  option_d: string;
  correct: string;
};

const MAX_QUESTIONS = 10;

export type ParsedQuestionRow = {
  text: string;
  option_a: string;
  option_b: string;
  option_c: string;
  option_d: string;
  correct: string;
};

function normalizeCorrect(raw: string, optionCount: number): string {
  const v = raw.trim().toUpperCase();
  if (!v) return "A";
  const letter = v[0];
  return clampCorrectLetter(letter, optionCount);
}

function rowFromCells(cells: string[], optionCount: number): ParsedQuestionRow | null {
  const text = (cells[0] ?? "").trim();
  if (!text) return null;
  return {
    text,
    option_a: (cells[1] ?? "").trim(),
    option_b: (cells[2] ?? "").trim(),
    option_c: (cells[3] ?? "").trim(),
    option_d: (cells[4] ?? "").trim(),
    correct: normalizeCorrect(cells[5] ?? "A", optionCount),
  };
}

function isHeaderRow(cells: string[]): boolean {
  const joined = cells.join(" ").toLowerCase();
  return (
    joined.includes("формулиров") ||
    joined.includes("вопрос") ||
    joined.includes("вариант") ||
    joined.includes("ответ")
  );
}

function parseDelimitedText(text: string, delimiter: string, optionCount: number): ParsedQuestionRow[] {
  const lines = text.split(/\r?\n/).map((l) => l.trim()).filter(Boolean);
  const rows: ParsedQuestionRow[] = [];
  for (let i = 0; i < lines.length && rows.length < MAX_QUESTIONS; i++) {
    const cells = lines[i].split(delimiter).map((c) => c.trim().replace(/^"|"$/g, ""));
    if (i === 0 && isHeaderRow(cells)) continue;
    const row = rowFromCells(cells, optionCount);
    if (row) rows.push(row);
  }
  return rows;
}

function parsePlainBlocks(text: string, optionCount: number): ParsedQuestionRow[] {
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
        correct: "A",
      });
      continue;
    }
    const cells = lines.flatMap((line) => line.split("\t").map((c) => c.trim()));
    const row = rowFromCells(cells, optionCount);
    if (row) rows.push(row);
  }
  return rows;
}

async function parseExcel(file: File, optionCount: number): Promise<ParsedQuestionRow[]> {
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
    const row = rowFromCells(cells, optionCount);
    if (row) rows.push(row);
  }
  return rows;
}

export async function parseQuestionsFromFile(
  file: File,
  optionCount: number
): Promise<ParsedQuestionRow[]> {
  const name = file.name.toLowerCase();
  if (name.endsWith(".xlsx") || name.endsWith(".xls")) {
    return parseExcel(file, optionCount);
  }
  const text = await file.text();
  if (name.endsWith(".csv") || name.endsWith(".tsv")) {
    return parseDelimitedText(text, name.endsWith(".tsv") ? "\t" : ",", optionCount);
  }
  if (text.includes("\t") && text.includes("\n")) {
    const fromTsv = parseDelimitedText(text, "\t", optionCount);
    if (fromTsv.length > 0) return fromTsv;
  }
  if (text.includes(",") && text.includes("\n")) {
    const fromCsv = parseDelimitedText(text, ",", optionCount);
    if (fromCsv.length > 0) return fromCsv;
  }
  return parsePlainBlocks(text, optionCount);
}

export function importedRowsToDrafts(
  rows: ParsedQuestionRow[],
  optionCount: number
): QuestionDraft[] {
  return rows.slice(0, MAX_QUESTIONS).map((row, idx) => ({
    position: idx + 1,
    text: row.text,
    option_a: row.option_a,
    option_b: row.option_b,
    option_c: row.option_c,
    option_d: row.option_d,
    correct: clampCorrectLetter(row.correct, optionCount),
  }));
}

export const TICKET_IMPORT_ACCEPT =
  ".txt,.csv,.tsv,.xlsx,.xls,text/plain,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel";
