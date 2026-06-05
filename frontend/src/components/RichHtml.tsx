/** Безопасный вывод HTML из конструктора билетов (теги задаёт backend). */
export default function RichHtml({ html, className }: { html: string; className?: string }) {
  if (!html?.trim()) return null;
  return (
    <span
      className={className ?? "rich-html"}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}
