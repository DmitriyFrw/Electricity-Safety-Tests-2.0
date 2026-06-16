export const SAFETY_GROUPS = [
  { id: "I", label: "I группа" },
  { id: "II", label: "II группа" },
  { id: "III", label: "III группа" },
  { id: "IV", label: "IV группа" },
] as const;

export function safetyGroupLabel(id: string): string {
  return SAFETY_GROUPS.find((g) => g.id === id)?.label ?? `${id} группа`;
}
