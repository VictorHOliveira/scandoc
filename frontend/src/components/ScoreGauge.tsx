interface Props {
  score: number;
}

function colorFor(score: number): string {
  if (score < 15) return "#34D399";
  if (score < 40) return "#FBBF24";
  if (score < 70) return "#FB923C";
  return "#F87171";
}

function labelFor(score: number): string {
  if (score < 15) return "Baixo risco";
  if (score < 40) return "Risco moderado";
  if (score < 70) return "Risco alto";
  return "Risco crítico";
}

export default function ScoreGauge({ score }: Props) {
  const r = 70;
  const circ = 2 * Math.PI * r;
  const pct = Math.min(100, Math.max(0, score));
  const offset = circ * (1 - pct / 100);
  const color = colorFor(score);

  return (
    <div className="score-gauge">
      <svg width="170" height="170" viewBox="0 0 170 170">
        <circle cx="85" cy="85" r={r} fill="none" stroke="#334155" strokeWidth="12" />
        <circle
          cx="85"
          cy="85"
          r={r}
          fill="none"
          stroke={color}
          strokeWidth="12"
          strokeLinecap="round"
          strokeDasharray={circ}
          strokeDashoffset={offset}
          transform="rotate(-90 85 85)"
        />
        <text x="85" y="82" textAnchor="middle" className="gauge-score" fill={color}>
          {pct}
        </text>
        <text x="85" y="104" textAnchor="middle" className="gauge-max">
          / 100
        </text>
      </svg>
      <p className="gauge-label" style={{ color }}>
        {labelFor(score)}
      </p>
    </div>
  );
}
