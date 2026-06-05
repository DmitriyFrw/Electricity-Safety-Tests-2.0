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

export function clampCorrectLetter(letter: string, count: number): string {
  const idx = letterToIndex(letter);
  const max = normalizeOptionCount(count) - 1;
  return indexToLetter(Math.min(idx, max));
}

export function optionFieldsForQuestion(
  _q: { option_a: string; option_b: string; option_c: string; option_d: string },
  count: number
): { key: "a" | "b" | "c" | "d"; label: string; field: "option_a" | "option_b" | "option_c" | "option_d" }[] {
  const n = normalizeOptionCount(count);
  const defs = [
    { key: "a" as const, label: "A", field: "option_a" as const },
    { key: "b" as const, label: "B", field: "option_b" as const },
    { key: "c" as const, label: "C", field: "option_c" as const },
    { key: "d" as const, label: "D", field: "option_d" as const },
  ];
  return defs.slice(0, n);
}
