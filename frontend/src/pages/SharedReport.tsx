import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getShare, type ScanResult } from "../api";
import ScoreGauge from "../components/ScoreGauge";
import FindingsList from "../components/FindingsList";
import HiddenTextViewer from "../components/HiddenTextViewer";
import DocumentPreview from "../components/DocumentPreview";

export default function SharedReport() {
  const { shareId = "" } = useParams();
  const [result, setResult] = useState<ScanResult | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getShare(shareId)
      .then((share) => setResult(share.result))
      .catch((e) => setError(e instanceof Error ? e.message : "Relatório não encontrado"));
  }, [shareId]);

  if (error) {
    return (
      <div className="card" style={{ maxWidth: 560, margin: "48px auto", padding: 24 }}>
        <h2>Relatório não encontrado</h2>
        <p className="muted">
          O link pode estar expirado (vale por 7 dias) ou incorreto. Gere um novo link a partir da
          sua conta.
        </p>
        <Link to="/login" className="btn btn-primary">
          Entrar e analisar
        </Link>
      </div>
    );
  }

  if (!result) {
    return (
      <p className="muted" style={{ textAlign: "center", marginTop: 80 }}>
        Carregando relatório...
      </p>
    );
  }

  return (
    <div className="scan-page">
      <div className="result-head card">
        <div>
          <h3>{result.filename}</h3>
          <p className="muted">
            Formato: {result.format.toUpperCase()} · {result.findings.length} achado(s) · relatório
            compartilhado
          </p>
        </div>
        <ScoreGauge score={result.score} />
      </div>

      <div className="tab-content card">
        <h3>Achados</h3>
        <FindingsList findings={result.findings} />
      </div>

      {result.annotated_image && (
        <div className="tab-content card">
          <h3>Documento anotado</h3>
          <DocumentPreview image={result.annotated_image} />
        </div>
      )}

      {(result.hidden_text || "").trim() && (
        <div className="tab-content card">
          <h3>Texto oculto</h3>
          <HiddenTextViewer text={result.hidden_text} />
        </div>
      )}

      {result.injection_matches.length > 0 && (
        <div className="tab-content card">
          <h3>Instruções para IA</h3>
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
        </div>
      )}

      <div className="card cta-strip">
        <div>
          <strong>Recebeu um documento e não confia nele?</strong>
          <p className="muted">
            Analise qualquer PDF, imagem ou texto agora — é grátis.
          </p>
        </div>
        <Link to="/register" className="btn btn-primary">
          Criar conta grátis
        </Link>
      </div>
    </div>
  );
}
