export const OPTION_LABELS = ["A", "B", "C", "D"] as const;

export const MIN_OPTION_COUNT = 2;
export const MAX_OPTION_COUNT = 4;

export function normalizeOptionCount(n: number | undefined | null): number {
  if (n == null || Number.isNaN(n)) return MAX_OPTION_COUNT;
  return Math.max(MIN_OPTION_COUNT, Math.min(MAX_OPTION_COUNT, Math.round(n)));
}

export function labelsForCount(count: number): readonly string[] {
  return OPTION_LABELS.slice(0, normalizeOptionCount(count));
}

export function indexToLetter(index: number): string {
  return OPTION_LABELS[index] ?? "A";
}

export function letterToIndex(letter: string): number {
  const i = OPTION_LABELS.indexOf(letter.toUpperCase() as (typeof OPTION_LABELS)[number]);
  return i >= 0 ? i : 0;
}

export function parseCorrectLetters(raw: string, count: number): string[] {
  const n = normalizeOptionCount(count);
  const allowed = new Set(labelsForCount(n));
  const value = raw.trim().toUpperCase();
  if (!value) return ["A"];
  const parts = /[,;\s]/.test(value) ? value.split(/[,;\s]+/) : value.split("");
  const picked: string[] = [];
  for (const part of parts) {
    const token = part.trim();
    if (!token) continue;
    const letter = indexToLetter(letterToIndex(token[0]));
    if (allowed.has(letter) && !picked.includes(letter)) picked.push(letter);
  }
  return picked.length ? picked : ["A"];
}

export function formatCorrectLetters(letters: string[]): string {
  return letters.length ? letters.join(",") : "A";
}

export function clampCorrectLetters(letters: string[], count: number): string[] {
  const n = normalizeOptionCount(count);
  const allowed = labelsForCount(n);
  const picked = letters.filter((l) => allowed.includes(l));
  if (picked.length) return picked;
  return [allowed[0] ?? "A"];
}

export function toggleCorrectLetter(letters: string[], letter: string, count: number): string[] {
  const allowed = labelsForCount(normalizeOptionCount(count));
  if (!allowed.includes(letter)) return clampCorrectLetters(letters, count);
  if (letters.includes(letter)) {
    const next = letters.filter((l) => l !== letter);
    return next.length ? next : [letter];
  }
  return clampCorrectLetters([...letters, letter], count);
}

export function parseSelectedValue(value: string | undefined): string[] {
  if (!value?.trim()) return [];
  return value
    .split(",")
    .map((part) => part.trim().toUpperCase())
    .filter(Boolean);
}

export function formatSelectedValue(letters: string[]): string {
  return letters.join(",");
}

export function toggleSelectedValue(current: string | undefined, letter: string): string {
  const selected = new Set(parseSelectedValue(current));
  if (selected.has(letter)) selected.delete(letter);
  else selected.add(letter);
  return formatSelectedValue([...selected].sort());
}

export function hasSelectedValue(value: string | undefined, multipleChoice: boolean): boolean {
  const selected = parseSelectedValue(value);
  if (multipleChoice) return selected.length > 0;
  return selected.length === 1;
}

export function optionFieldsForQuestion(
  q: {
    option_a: string;
    option_b: string;
    option_c: string;
    option_d: string;
    option_count?: number;
  },
  fallbackCount?: number
): { key: "a" | "b" | "c" | "d"; label: string; field: "option_a" | "option_b" | "option_c" | "option_d" }[] {
  const n = normalizeOptionCount(q.option_count ?? fallbackCount ?? MAX_OPTION_COUNT);
  const defs = [
    { key: "a" as const, label: "A", field: "option_a" as const },
    { key: "b" as const, label: "B", field: "option_b" as const },
    { key: "c" as const, label: "C", field: "option_c" as const },
    { key: "d" as const, label: "D", field: "option_d" as const },
  ];
  return defs.slice(0, n);
}
