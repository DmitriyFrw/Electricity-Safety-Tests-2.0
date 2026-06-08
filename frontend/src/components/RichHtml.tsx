/** HTML санитизируется на backend (bleach); здесь только отображение доверенной разметки. */
export default function RichHtml({ html, className }: { html: string; className?: string }) {
  if (!html?.trim()) return null;
  return (
    <span
      className={className ?? "rich-html"}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}
