/** Юридические лица (бизнес-юниты) — единый список с backend (app.constants.BUSINESS_UNITS). */
export const BUSINESS_UNITS = [
  "ДЦ MOZ",
  "ДЦ KLG",
  "ДЦ VLA",
  "ДЦ NRG",
  "ДЦ SAS",
] as const;

export type BusinessUnit = (typeof BUSINESS_UNITS)[number];

export function isBusinessUnit(value: string): value is BusinessUnit {
  return (BUSINESS_UNITS as readonly string[]).includes(value);
}
