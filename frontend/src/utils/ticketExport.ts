import type { QuestionDraft } from "./ticketImport";
import { normalizeOptionCount } from "./questionOptions";

export type TicketExportFormat = "txt" | "csv" | "tsv" | "xlsx" | "xls";

export const TICKET_EXPORT_FORMATS: { value: TicketExportFormat; label: string }[] = [
  { value: "txt", label: "TXT" },
  { value: "csv", label: "CSV" },
  { value: "tsv", label: "TSV" },
  { value: "xlsx", label: "Excel (.xlsx)" },
  { value: "xls", label: "Excel (.xls)" },
];

const HEADERS = [
  "Формулировка",
  "Вариант A",
  "Вариант B",
  "Вариант C",
  "Вариант D",
  "Верный ответ",
  "Кол-во вариантов",
] as const;

function plainText(html: string): string {
  if (!html) return "";
  if (typeof document !== "undefined") {
    const div = document.createElement("div");
    div.innerHTML = html;
    return (div.textContent ?? div.innerText ?? "").trim();
  }
  return html.replace(/<[^>]+>/g, "").trim();
}

function rowCells(q: QuestionDraft): string[] {
  const n = normalizeOptionCount(q.option_count);
  const options = [q.option_a, q.option_b, q.option_c, q.option_d].slice(0, n).map(plainText);
  while (options.length < 4) options.push("");
  const correct = q.correct.length ? q.correct.join(",") : "A";
  return [plainText(q.text), ...options, correct, String(n)];
}

function escapeCsvCell(value: string, delimiter: string): string {
  if (value.includes('"') || value.includes(delimiter) || value.includes("\n") || value.includes("\r")) {
    return `"${value.replace(/"/g, '""')}"`;
  }
  return value;
}

function toDelimitedText(rows: string[][], delimiter: string): string {
  return rows.map((row) => row.map((cell) => escapeCsvCell(cell, delimiter)).join(delimiter)).join("\n");
}

function toPlainBlocks(rows: string[][]): string {
  return rows
    .slice(1)
    .map((row) => {
      const [text, a, b, c, d, correct, count] = row;
      const lines = [`${text}`, `Кол-во вариантов: ${count}`, `A: ${a}`, `B: ${b}`];
      if (c) lines.push(`C: ${c}`);
      if (d) lines.push(`D: ${d}`);
      lines.push(`Верный ответ: ${correct}`);
      return lines.join("\n");
    })
    .join("\n\n");
}

function downloadBlob(filename: string, blob: Blob) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

function safeFilename(base: string): string {
  return base.replace(/[^\w\u0400-\u04FF.-]+/g, "_").replace(/_+/g, "_") || "ticket";
}

export async function exportTicketToFile(
  questions: QuestionDraft[],
  format: TicketExportFormat,
  ticketTitle: string
): Promise<void> {
  const rows = [[...HEADERS], ...questions.map((q) => rowCells(q))];
  const name = safeFilename(ticketTitle.trim() || "ticket");

  if (format === "csv") {
    downloadBlob(`${name}.csv`, new Blob(["\uFEFF" + toDelimitedText(rows, ",")], { type: "text/csv;charset=utf-8" }));
    return;
  }
  if (format === "tsv") {
    downloadBlob(`${name}.tsv`, new Blob(["\uFEFF" + toDelimitedText(rows, "\t")], { type: "text/tab-separated-values;charset=utf-8" }));
    return;
  }
  if (format === "txt") {
    downloadBlob(`${name}.txt`, new Blob([toPlainBlocks(rows)], { type: "text/plain;charset=utf-8" }));
    return;
  }

  const XLSX = await import("xlsx");
  const sheet = XLSX.utils.aoa_to_sheet(rows);
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, sheet, "Билет");
  const bookType = format === "xls" ? "xls" : "xlsx";
  const buffer = XLSX.write(workbook, { bookType, type: "array" });
  const mime =
    bookType === "xls"
      ? "application/vnd.ms-excel"
      : "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet";
  downloadBlob(`${name}.${bookType}`, new Blob([buffer], { type: mime }));
}
