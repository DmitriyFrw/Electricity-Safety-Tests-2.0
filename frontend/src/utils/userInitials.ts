export function userInitials(user: {
  display_name?: string;
  username: string;
  full_name?: string | null;
}): string {
  const name = (user.full_name || user.display_name || user.username).trim();
  const parts = name.split(/\s+/).filter(Boolean);
  if (parts.length >= 2) {
    return (parts[0][0] + parts[1][0]).toUpperCase();
  }
  return name.slice(0, 2).toUpperCase();
}
