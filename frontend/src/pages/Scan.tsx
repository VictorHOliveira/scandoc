import { useState } from "react";
import { Link } from "react-router-dom";
import { api, ApiError, type ScanResult } from "../api";
import UploadZone from "../components/UploadZone";
import ScoreGauge from "../components/ScoreGauge";
import FindingsList from "../components/FindingsList";
import HiddenTextViewer from "../components/HiddenTextViewer";
import DocumentPreview from "../components/DocumentPreview";
import { useAuth } from "../context/AuthContext";

type Tab = "findings" | "preview" | "hidden" | "injection";

export default function Scan() {
  const { me, refresh } = useAuth();
  const [result, setResult] = useState<ScanResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [tab, setTab] = useState<Tab>("findings");
  const [quotaExceeded, setQuotaExceeded] = useState(false);

  const scan = async (file: File) => {
    setError("");
    setQuotaExceeded(false);
    setResult(null);
    setBusy(true);
    setTab("findings");
    try {
      const form = new FormData();
      form.append("file", file);
      const res = await api<ScanResult>("/scan", { method: "POST", body: form });
      setResult(res);
      await refresh();
    } catch (e) {
      if (e instanceof ApiError && e.status === 429) {
        setQuotaExceeded(true);
      } else {
        setError(e instanceof Error ? e.message : "Erro ao analisar o documento");
      }
    } finally {
      setBusy(false);
    }
  };

  const tabs: { id: Tab; label: string; disabled?: boolean }[] = [
    { id: "findings", label: "Achados" },
    { id: "preview", label: "Documento anotado", disabled: !result?.annotated_image },
    { id: "hidden", label: "Texto oculto" },
    { id: "injection", label: "Instruções para IA", disabled: (result?.injection_matches.length ?? 0) === 0 },
  ];

  return (
    <div className="scan-page">
      <div className="scan-head">
        <h2>Analisar documento</h2>
        {me && (
          <p className="muted">
            Cota: {me.quota.limit === null ? "ilimitada" : `${me.quota.remaining} de ${me.quota.limit} restante(s) na janela de ${me.quota.window_hours}h`}
          </p>
        )}
      </div>

      <UploadZone onScan={scan} busy={busy} />

      {error && (
        <div className="error-box">
          {error}
          {quotaExceeded && (
            <span>
              {" "}
              <Link to="/planos">Assine um plano para analisar mais.</Link>
            </span>
          )}
        </div>
      )}

      {busy && <p className="muted">Processando... documentos grandes podem demorar um pouco.</p>}

      {result && !busy && (
        <div className="results">
          <div className="result-head card">
            <div>
              <h3>{result.filename}</h3>
              <p className="muted">
                Formato: {result.format.toUpperCase()} · {result.findings.length} achado(s)
              </p>
            </div>
            <ScoreGauge score={result.score} />
          </div>

          <div className="tabs">
            {tabs.map((t) => (
              <button
                key={t.id}
                className={`tab${tab === t.id ? " active" : ""}`}
                disabled={t.disabled}
                onClick={() => setTab(t.id)}
              >
                {t.label}
              </button>
            ))}
          </div>

          <div className="tab-content card">
            {tab === "findings" && <FindingsList findings={result.findings} />}
            {tab === "preview" && <DocumentPreview image={result.annotated_image} />}
            {tab === "hidden" && <HiddenTextViewer text={result.hidden_text} />}
            {tab === "injection" && (
              <ul className="findings-list">
                {result.injection_matches.map((m, i) => (
                  <li key={i} className="finding finding-critical">
                    <div className="finding-head">
                      <span className="badge badge-soft">Crítico</span>
                      <strong>Frase de manipulação de IA</strong>
                    </div>
                    <pre className="finding-snippet">{m}</pre>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
