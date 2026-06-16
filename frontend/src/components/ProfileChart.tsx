import type { ChartPoint } from "../utils/profileStats";

export default function ProfileChart({ points }: { points: ChartPoint[] }) {
  const width = 400;
  const height = 160;
  const padX = 36;
  const padY = 24;
  const plotW = width - padX * 2;
  const plotH = height - padY * 2;

  const coords = points.map((p, i) => {
    const x = padX + (points.length <= 1 ? plotW / 2 : (i / (points.length - 1)) * plotW);
    const y = padY + plotH - (p.percent / 100) * plotH;
    return { x, y, ...p };
  });

  const line = coords.map((c) => `${c.x},${c.y}`).join(" ");

  return (
    <svg className="profile-chart__svg" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Динамика результатов">
      {[0, 25, 50, 75, 100].map((tick) => {
        const y = padY + plotH - (tick / 100) * plotH;
        return (
          <g key={tick}>
            <line x1={padX} y1={y} x2={width - padX} y2={y} stroke="#ececf1" strokeWidth="1" />
            <text x={padX - 8} y={y + 4} textAnchor="end" fontSize="10" fill="#6b6b73">
              {tick}%
            </text>
          </g>
        );
      })}
      {coords.some((c) => c.percent > 0) && (
        <>
          <polyline
            fill="none"
            stroke="#7b61ff"
            strokeWidth="2.5"
            strokeLinejoin="round"
            strokeLinecap="round"
            points={line}
          />
          {coords.map((c) =>
            c.percent > 0 ? (
              <circle key={c.label} cx={c.x} cy={c.y} r="4" fill="#7b61ff" />
            ) : null
          )}
        </>
      )}
      {coords.map((c) => (
        <text key={`${c.label}-x`} x={c.x} y={height - 4} textAnchor="middle" fontSize="10" fill="#6b6b73">
          {c.label}
        </text>
      ))}
    </svg>
  );
}
