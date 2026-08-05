import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

function firebaseMessage(err: unknown): string {
  const code = (err as { code?: string })?.code ?? "";
  const map: Record<string, string> = {
    "auth/user-not-found": "E-mail não cadastrado.",
    "auth/wrong-password": "Senha incorreta.",
    "auth/invalid-credential": "E-mail ou senha incorretos.",
    "auth/too-many-requests": "Muitas tentativas. Tente novamente em alguns minutos.",
    "auth/invalid-email": "E-mail inválido.",
  };
  return map[code] ?? "Erro ao entrar";
}

export default function Login() {
  const { login, loginGoogle } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await login(email, password);
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
        <h2>Entrar</h2>
        {error && <p className="error-box">{error}</p>}
        <label>
          E-mail
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoFocus
          />
        </label>
        <label>
          Senha
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </label>
        <button type="submit" className="btn btn-primary" disabled={busy}>
          {busy ? "Entrando..." : "Entrar"}
        </button>
        <button type="button" className="btn" onClick={withGoogle} disabled={busy}>
          Continuar com Google
        </button>
        <p className="auth-alt">
          Não tem conta? <Link to="/register">Cadastre-se</Link>
        </p>
      </form>
    </div>
  );
}
