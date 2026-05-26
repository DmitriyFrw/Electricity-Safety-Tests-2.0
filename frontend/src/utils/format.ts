const MONTHS = [
  "",
  "Января",
  "Февраля",
  "Марта",
  "Апреля",
  "Мая",
  "Июня",
  "Июля",
  "Августа",
  "Сентября",
  "Октября",
  "Ноября",
  "Декабря",
];

const WEEKDAYS = [
  "Воскресенье",
  "Понедельник",
  "Вторник",
  "Среда",
  "Четверг",
  "Пятница",
  "Суббота",
];

export function formatDateRu(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    year: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function parseNextCheck(isoDate: string) {
  const d = new Date(isoDate + "T12:00:00");
  return {
    day: d.getDate(),
    month: MONTHS[d.getMonth() + 1],
    weekday: WEEKDAYS[d.getDay()],
    short: d.toLocaleDateString("ru-RU"),
  };
}
