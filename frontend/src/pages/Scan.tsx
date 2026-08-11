import { useState } from "react";
import { Link } from "react-router-dom";
import { api, ApiError, createShare, type ScanJobStatus, type ScanResult } from "../api";
import UploadZone from "../components/UploadZone";
import ScoreGauge from "../components/ScoreGauge";
import FindingsList from "../components/FindingsList";
import HiddenTextViewer from "../components/HiddenTextViewer";
import DocumentPreview from "../components/DocumentPreview";
import ScanProgress from "../components/ScanProgress";
import { useAuth } from "../context/AuthContext";

type Tab = "findings" | "preview" | "hidden" | "injection";

const POLL_INTERVAL_MS = 800;
const POLL_MAX_ATTEMPTS = 600;

export default function Scan() {
  const { me, refresh } = useAuth();
  const [result, setResult] = useState<ScanResult | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [tab, setTab] = useState<Tab>("findings");
  const [quotaExceeded, setQuotaExceeded] = useState(false);
  const [progress, setProgress] = useState({ percent: 0, stage: "Enviando documento..." });
  const [shareLink, setShareLink] = useState<string | null>(null);
  const [shareBusy, setShareBusy] = useState(false);
  const [shareError, setShareError] = useState("");

  const pollJob = async (jobId: string) => {
    for (let attempt = 0; attempt < POLL_MAX_ATTEMPTS; attempt++) {
      await new Promise((resolve) => setTimeout(resolve, POLL_INTERVAL_MS));
      const status = await api<ScanJobStatus>(`/scan/${jobId}`);
      setProgress(status.progress);
      if (status.status === "done" && status.result) {
        setResult(status.result);
        return;
      }
      if (status.status === "error") {
        throw new Error(status.error ?? "Erro ao analisar o documento");
      }
    }
    throw new Error("O tempo limite da análise foi excedido. Tente novamente.");
  };

  const scan = async (file: File) => {
    setError("");
    setQuotaExceeded(false);
    setResult(null);
    setJobId(null);
    setShareLink(null);
    setShareError("");
    setBusy(true);
    setProgress({ percent: 0, stage: "Enviando documento..." });
    setTab("findings");
    try {
      const form = new FormData();
      form.append("file", file);
      const started = await api<{ job_id: string }>("/scan", { method: "POST", body: form });
      setJobId(started.job_id);
      await pollJob(started.job_id);
      await refresh();
    } catch (e) {
      if (e instanceof ApiError && e.status === 429 && e.quota) {
        setQuotaExceeded(true);
      } else {
        setError(e instanceof Error ? e.message : "Erro ao analisar o documento");
      }
    } finally {
      setBusy(false);
    }
  };

  const share = async () => {
    if (!jobId) return;
    setShareBusy(true);
    setShareError("");
    try {
      const { share_id } = await createShare(jobId);
      const link = `${window.location.origin}/compartilhado/${share_id}`;
      try {
        await navigator.clipboard.writeText(link);
      } catch {
        /* clipboard indisponível: o link é exibido na tela */
      }
      setShareLink(link);
    } catch (e) {
      setShareError(e instanceof Error ? e.message : "Erro ao gerar o link");
    } finally {
      setShareBusy(false);
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

      {error && !quotaExceeded && (
        <div className="error-box">
          {error}
        </div>
      )}

      {quotaExceeded && (
        <div className="card upgrade-cta">
          <h3>Limite diário de análises atingido</h3>
          <p className="muted">
            O plano gratuito inclui <strong>1 análise por dia</strong>. O plano{" "}
            <strong>Básico</strong> libera <strong>5 análises por dia</strong> por apenas{" "}
            <strong>R$ 19,90/mês</strong> — e você pode cancelar quando quiser.
          </p>
          <div className="upgrade-cta-actions">
            <Link to="/planos" className="btn btn-primary">
              Ver planos
            </Link>
            <Link to="/planos?destaque=basico" className="btn">
              Assinar Básico
            </Link>
          </div>
        </div>
      )}

      {busy && <ScanProgress progress={progress} />}

      {result && !busy && (
        <div className="results">
          <div className="result-head card">
            <div>
              <h3>{result.filename}</h3>
              <p className="muted">
                Formato: {result.format.toUpperCase()} · {result.findings.length} achado(s)
              </p>
              <div className="share-row">
                <button className="btn" onClick={share} disabled={shareBusy}>
                  {shareBusy ? "Gerando link..." : "🔗 Compartilhar relatório"}
                </button>
                {shareError && <span className="error-inline">{shareError}</span>}
                {shareLink && (
                  <span className="success-inline">
                    Link copiado! Qualquer pessoa pode abrir:{" "}
                    <a href={shareLink} target="_blank" rel="noreferrer">
                      ver relatório
                    </a>
                  </span>
                )}
              </div>
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

          {me?.plan.slug === "free" && (
            <div className="card cta-strip">
              <div>
                <strong>Gostou da análise?</strong>
                <p className="muted">
                  Com o plano Básico você faz <strong>5 análises por dia</strong> por{" "}
                  <strong>R$ 19,90/mês</strong>.
                </p>
              </div>
              <Link to="/planos?destaque=basico" className="btn btn-primary">
                Desbloquear mais análises
              </Link>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
