import type { Finding } from "../api";

const SEV_ORDER: Record<string, number> = {
  critical: 0,
  high: 1,
  medium: 2,
  low: 3,
  info: 4,
};

const SEV_LABEL: Record<string, string> = {
  critical: "Crítico",
  high: "Alto",
  medium: "Médio",
  low: "Baixo",
  info: "Info",
};

export default function FindingsList({ findings }: { findings: Finding[] }) {
  if (findings.length === 0) {
    return <p className="empty-state">Nenhum achado suspeito neste documento.</p>;
  }
  const sorted = [...findings].sort(
    (a, b) => (SEV_ORDER[a.severity] ?? 5) - (SEV_ORDER[b.severity] ?? 5)
  );
  return (
    <ul className="findings-list">
      {sorted.map((f, i) => (
        <li key={i} className={`finding finding-${f.severity}`}>
          <div className="finding-head">
            <span className="badge badge-soft">{SEV_LABEL[f.severity] ?? f.severity}</span>
            <strong>{f.title}</strong>
          </div>
          <p className="finding-desc">{f.description}</p>
          {f.location && <p className="finding-loc">📍 {f.location}</p>}
          {f.snippet && (
            <pre className="finding-snippet">{f.snippet}</pre>
          )}
        </li>
      ))}
    </ul>
  );
}
