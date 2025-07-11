import { format, formatDistanceToNowStrict } from "date-fns";
import { ar } from "date-fns/locale";

export function formatRelativeTime(date: string | Date): string {
  const dateObj = typeof date === "string" ? new Date(date) : date;
  const now = new Date();

  // Difference in milliseconds
  const diff = now.getTime() - dateObj.getTime();
  const oneDay = 24 * 60 * 60 * 1000;

  // If it's more than a day old, show the date. Otherwise, relative time.
  if (diff > oneDay) {
    return format(dateObj, "d MMM yyyy", { locale: ar });
  }

  return formatDistanceToNowStrict(dateObj, { addSuffix: true, locale: ar });
}
