import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

function formatReset(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString("pt-BR");
}

export default function Account() {
  const { me } = useAuth();

  if (!me) return null;

  const { user, plan, quota } = me;
  const unlimited = quota.limit === null;

  return (
    <div className="account-page">
      <h2>Minha conta</h2>
      <div className="card account-card">
        <p>
          <strong>Nome:</strong> {user.name}
        </p>
        <p>
          <strong>E-mail:</strong> {user.email}
        </p>
      </div>

      <h3>Plano atual</h3>
      <div className="card account-card">
        <div className="account-plan-row">
          <div>
            <p className="plan-name">
              {plan.name}
              {plan.slug === "free" && <span className="badge badge-soft">gratuito</span>}
            </p>
            {plan.description && <p className="muted">{plan.description}</p>}
          </div>
          <Link to="/planos" className="btn btn-primary">
            Trocar de plano
          </Link>
        </div>
      </div>

      <h3>Cota de análises (janela de {quota.window_hours}h)</h3>
      <div className="card account-card">
        <div className="quota-row">
          <div className="quota-num">
            <span className="quota-used">{quota.used}</span>
            <span className="quota-sep">/</span>
            <span className="quota-limit">{unlimited ? "∞" : quota.limit}</span>
          </div>
          <div className="quota-bar">
            <div
              className="quota-fill"
              style={{
                width: unlimited
                  ? "0%"
                  : `${Math.min(100, (quota.used / Math.max(1, quota.limit!)) * 100)}%`,
              }}
            />
          </div>
        </div>
        {unlimited ? (
          <p className="muted">Plano ilimitado — analise quantos documentos quiser.</p>
        ) : (
          <p className="muted">
            {quota.remaining} análise(s) restante(s). Cota renova em {formatReset(quota.resets_at)}.
          </p>
        )}
      </div>
    </div>
  );
}
