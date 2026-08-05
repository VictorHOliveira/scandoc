import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { api, type Plan } from "../api";

function limitLabel(limit: number | null): string {
  return limit === null ? "Ilimitado" : `${limit} por dia`;
}

export default function Pricing() {
  const { me, refresh } = useAuth();
  const [plans, setPlans] = useState<Plan[]>([]);
  const [message, setMessage] = useState("");
  const [busySlug, setBusySlug] = useState<string | null>(null);

  useEffect(() => {
    api<Plan[]>("/plans").then(setPlans).catch(() => setPlans([]));
  }, []);

  const subscribe = async (plan: Plan) => {
    setMessage("");
    setBusySlug(plan.slug);
    try {
      await api("/subscribe", {
        method: "POST",
        body: JSON.stringify({ plan_slug: plan.slug }),
      });
      setMessage(`Plano "${plan.name}" ativado!`);
      await refresh();
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Erro ao assinar");
    } finally {
      setBusySlug(null);
    }
  };

  return (
    <div className="pricing-page">
      <h2>Planos</h2>
      <p className="muted">
        Cada análise processa um documento. A cota reset a cada 24 horas.
      </p>
      {message && <p className="success-box">{message}</p>}
      <div className="plan-grid">
        {plans.map((p) => {
          const current = me?.plan.slug === p.slug;
          const featured = p.slug === "profissional";
          return (
            <div key={p.slug} className={`plan-card card${featured ? " featured" : ""}`}>
              <h3>{p.name}</h3>
              <p className="plan-limit">{limitLabel(p.daily_limit)}</p>
              <p className="plan-price">
                {Number(p.price_brl) === 0 ? "Grátis" : `R$ ${p.price_brl}`}
                {Number(p.price_brl) > 0 && <span className="plan-per">/mês</span>}
              </p>
              {p.description && <p className="plan-desc">{p.description}</p>}
              {current ? (
                <button className="btn" disabled>
                  Plano atual
                </button>
              ) : p.slug === "free" ? (
                <button className="btn" disabled>
                  Sempre disponível
                </button>
              ) : (
                <button
                  className="btn btn-primary"
                  disabled={busySlug === p.slug}
                  onClick={() => subscribe(p)}
                >
                  {busySlug === p.slug ? "Ativando..." : "Assinar"}
                </button>
              )}
            </div>
          );
        })}
      </div>
      <p className="hint">
        Pagamento simulado por enquanto — a assinatura é ativada imediatamente.
      </p>
    </div>
  );
}
