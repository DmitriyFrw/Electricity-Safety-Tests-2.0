import type { AttemptRow } from "../types/api";

export type ProfileStats = {
  testsPassed: number;
  averagePercent: number;
  bestPercent: number;
  currentStreak: number;
};

export type ChartPoint = {
  label: string;
  percent: number;
};

const MONTH_SHORT = ["янв", "фев", "мар", "апр", "май", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"];

export function computeProfileStats(
  attempts: AttemptRow[],
  total: number,
  minPassPercent: number
): ProfileStats {
  if (attempts.length === 0) {
    return { testsPassed: total, averagePercent: 0, bestPercent: 0, currentStreak: 0 };
  }
  const percents = attempts.map((a) => a.percent);
  const averagePercent = Math.round(percents.reduce((s, p) => s + p, 0) / percents.length);
  const bestPercent = Math.max(...percents);
  let currentStreak = 0;
  for (const a of attempts) {
    if (a.percent >= minPassPercent) currentStreak += 1;
    else break;
  }
  return {
    testsPassed: total,
    averagePercent,
    bestPercent,
    currentStreak,
  };
}

export function buildChartPoints(attempts: AttemptRow[], months = 6): ChartPoint[] {
  const now = new Date();
  const buckets = new Map<string, number[]>();

  for (let i = months - 1; i >= 0; i--) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
    const key = `${d.getFullYear()}-${d.getMonth()}`;
    buckets.set(key, []);
  }

  for (const a of attempts) {
    const d = new Date(a.finished_at);
    const key = `${d.getFullYear()}-${d.getMonth()}`;
    if (buckets.has(key)) buckets.get(key)!.push(a.percent);
  }

  return Array.from(buckets.entries()).map(([key, values]) => {
    const month = Number(key.split("-")[1]);
    const year = Number(key.split("-")[0]);
    const label = `${MONTH_SHORT[month]} '${String(year).slice(-2)}`;
    const percent =
      values.length > 0
        ? Math.round(values.reduce((s, v) => s + v, 0) / values.length)
        : 0;
    return { label, percent };
  });
}

export function daysUntil(isoDate: string): number {
  const target = new Date(`${isoDate}T12:00:00`);
  const today = new Date();
  today.setHours(12, 0, 0, 0);
  return Math.max(0, Math.ceil((target.getTime() - today.getTime()) / 86_400_000));
}

export function formatDateShort(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso.includes("T") ? iso : `${iso}T12:00:00`);
  return d.toLocaleDateString("ru-RU", { day: "2-digit", month: "2-digit", year: "numeric" });
}

export function attemptKind(attempt: AttemptRow, minPassPercent: number): "exam" | "training" {
  return attempt.percent >= minPassPercent ? "exam" : "training";
}
