import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

function firebaseMessage(err: unknown): string {
  const code = (err as { code?: string })?.code ?? "";
  const map: Record<string, string> = {
    "auth/email-already-in-use": "Este e-mail já está cadastrado.",
    "auth/weak-password": "Senha muito fraca. Use pelo menos 6 caracteres.",
    "auth/invalid-email": "E-mail inválido.",
  };
  return map[code] ?? "Erro ao cadastrar";
}

export default function Register() {
  const { register, loginGoogle } = useAuth();
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await register(name, email, password);
      navigate("/");
    } catch (err) {
      setError(firebaseMessage(err));
    } finally {
      setBusy(false);
    }
  };

  const withGoogle = async () => {
    setError("");
    setBusy(true);
    try {
      await loginGoogle();
      navigate("/");
    } catch (err) {
      setError(firebaseMessage(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="auth-page">
      <form className="card auth-card" onSubmit={submit}>
        <h2>Criar conta</h2>
        <p className="muted">O plano gratuito permite 1 análise por dia.</p>
        {error && <p className="error-box">{error}</p>}
        <label>
          Nome
          <input value={name} onChange={(e) => setName(e.target.value)} required />
        </label>
        <label>
          E-mail
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </label>
        <label>
          Senha (mín. 6 caracteres)
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={6}
          />
        </label>
        <button type="submit" className="btn btn-primary" disabled={busy}>
          {busy ? "Criando..." : "Criar conta"}
        </button>
        <button type="button" className="btn" onClick={withGoogle} disabled={busy}>
          Continuar com Google
        </button>
        <p className="auth-alt">
          Já tem conta? <Link to="/login">Entrar</Link>
        </p>
      </form>
    </div>
  );
}
