/** Профиль готов к протоколу PDF (те же поля, что проверяет backend). */
export function isProfileFieldsComplete(user: {
  full_name: string | null;
  birth_date: string | null;
  job_title: string | null;
  business_unit: string | null;
}): boolean {
  return Boolean(
    user.full_name?.trim() &&
      user.birth_date &&
      user.job_title?.trim() &&
      user.business_unit?.trim()
  );
}

export function profileMissingLabels(user: {
  full_name: string | null;
  birth_date: string | null;
  job_title: string | null;
  business_unit: string | null;
}): string[] {
  const missing: string[] = [];
  if (!user.full_name?.trim()) missing.push("ФИО");
  if (!user.birth_date) missing.push("дата рождения");
  if (!user.job_title?.trim()) missing.push("должность");
  if (!user.business_unit?.trim()) missing.push("бизнес-юнит");
  return missing;
}
