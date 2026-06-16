import type { AdminGradeBucket, AdminMonthlyResult } from "../types/api";

const MONTH_LABELS = ["Янв", "Фев", "Мар", "Апр", "Май", "Июн", "Июл", "Авг", "Сен", "Окт", "Ноя", "Дек"];

const GRADE_COLORS: Record<string, string> = {
  отлично: "var(--mockup-purple)",
  хорошо: "#ffd700",
  удовлетворительно: "#a78bfa",
  неудовлетворительно: "#e5e7eb",
};

const GRADE_ORDER = ["отлично", "хорошо", "удовлетворительно", "неудовлетворительно"] as const;

const GRADE_LABELS: Record<string, string> = {
  отлично: "Отлично",
  хорошо: "Хорошо",
  удовлетворительно: "Удовлетворительно",
  неудовлетворительно: "Неудовлетворительно",
};

export function monthLabel(month: number): string {
  return MONTH_LABELS[month - 1] ?? String(month);
}

export function donutGradient(buckets: AdminGradeBucket[]): string {
  let acc = 0;
  const stops: string[] = [];
  for (const grade of GRADE_ORDER) {
    const bucket = buckets.find((b) => b.grade === grade);
    if (!bucket || bucket.percent <= 0) continue;
    const next = acc + bucket.percent;
    stops.push(`${GRADE_COLORS[grade]} ${acc}% ${next}%`);
    acc = next;
  }
  if (!stops.length) return "conic-gradient(#e5e7eb 0 100%)";
  return `conic-gradient(${stops.join(", ")})`;
}

export function gradeLegend(buckets: AdminGradeBucket[]) {
  return GRADE_ORDER.map((grade) => {
    const bucket = buckets.find((b) => b.grade === grade);
    return {
      grade,
      label: GRADE_LABELS[grade] ?? grade,
      percent: bucket?.percent ?? 0,
      count: bucket?.count ?? 0,
      color: GRADE_COLORS[grade],
    };
  }).filter((item) => item.count > 0 || item.percent > 0);
}

export function barHeightPercent(value: number, max = 100): number {
  if (max <= 0) return 0;
  return Math.max(4, Math.round((value / max) * 100));
}

export function monthlyChartMax(months: AdminMonthlyResult[]): number {
  const peak = Math.max(...months.map((m) => m.average_percent), 0);
  return peak > 0 ? peak : 100;
}
