import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { api, createCheckout, type Plan } from "../api";

function limitLabel(limit: number | null): string {
  return limit === null ? "Ilimitado" : `${limit} por dia`;
}

export default function Pricing() {
  const { me, refresh } = useAuth();
  const [plans, setPlans] = useState<Plan[]>([]);
  const [message, setMessage] = useState("");
  const [busySlug, setBusySlug] = useState<string | null>(null);
  const [searchParams] = useSearchParams();

  useEffect(() => {
    const payment = searchParams.get("payment");
    if (payment === "success") {
      setMessage("Pagamento aprovado! Sua assinatura foi ativada.");
      refresh();
    } else if (payment === "pending") {
      setMessage("Pagamento pendente. Assim que confirmado, sua assinatura será ativada.");
    }
  }, [searchParams, refresh]);

  useEffect(() => {
    api<Plan[]>("/plans").then(setPlans).catch(() => setPlans([]));
  }, []);

  const subscribe = async (plan: Plan) => {
    setMessage("");
    setBusySlug(plan.slug);
    try {
      const checkout = await createCheckout(plan.slug);
      if (checkout.mock) {
        setMessage(`Plano "${plan.name}" ativado! (modo de teste)`);
        await refresh();
      } else if (checkout.checkout_url) {
        window.location.assign(checkout.checkout_url);
        return;
      } else {
        setMessage("Não foi possível iniciar o pagamento.");
      }
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
                  {busySlug === p.slug ? "Aguarde..." : "Assinar"}
                </button>
              )}
            </div>
          );
        })}
      </div>
      <p className="hint">
        Assinatura mensal cobrada via Mercado Pago. Cancele quando quiser na página da conta.
      </p>
    </div>
  );
}
