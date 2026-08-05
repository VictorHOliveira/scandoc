import { useEffect } from "react";
import { NavLink, Route, Routes, useNavigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Scan from "./pages/Scan";
import Pricing from "./pages/Pricing";
import Account from "./pages/Account";

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { me, loading } = useAuth();
  const navigate = useNavigate();
  useEffect(() => {
    if (!loading && !me) navigate("/login");
  }, [loading, me, navigate]);
  if (loading || !me) return <p className="muted" style={{ textAlign: "center", marginTop: 80 }}>Carregando...</p>;
  return <>{children}</>;
}

function SetupNotice() {
  return (
    <div className="card" style={{ maxWidth: 720, margin: "64px auto", padding: 28 }}>
      <h2>Firebase não configurado</h2>
      <p>
        Este app usa Firebase (Authentication + Firestore). Crie um projeto em{" "}
        <a href="https://console.firebase.google.com" target="_blank" rel="noreferrer">
          console.firebase.google.com
        </a>{" "}
        e preencha as variáveis no arquivo <code>frontend/.env</code>:
      </p>
      <pre>{`VITE_FIREBASE_API_KEY=
VITE_FIREBASE_AUTH_DOMAIN=
VITE_FIREBASE_PROJECT_ID=
VITE_FIREBASE_STORAGE_BUCKET=
VITE_FIREBASE_MESSAGING_SENDER_ID=
VITE_FIREBASE_APP_ID=`}</pre>
      <p className="muted">
        No console: ative o método de login E-mail/Senha (e Google, se quiser) em{" "}
        <em>Authentication → Sign-in method</em>. Depois reinicie o servidor de desenvolvimento.
      </p>
    </div>
  );
}

function Navbar() {
  const { me, logout, configured } = useAuth();
  return (
    <header className="navbar">
      <NavLink to="/" className="brand">
        🔍 ScanDoc
      </NavLink>
      <nav>
        <NavLink to="/" end>
          Analisar
        </NavLink>
        <NavLink to="/planos">Planos</NavLink>
        {me ? (
          <>
            <NavLink to="/conta">Conta</NavLink>
            <button className="btn btn-ghost" onClick={logout}>
              Sair
            </button>
          </>
        ) : (
          configured && (
            <>
              <NavLink to="/login">Entrar</NavLink>
              <NavLink to="/register" className="btn btn-primary btn-nav">
                Criar conta
              </NavLink>
            </>
          )
        )}
      </nav>
    </header>
  );
}

function AppRoutes() {
  const { configured } = useAuth();
  if (!configured) {
    return <SetupNotice />;
  }
  return (
    <Routes>
      <Route
        path="/"
        element={
          <RequireAuth>
            <Scan />
          </RequireAuth>
        }
      />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/planos" element={<Pricing />} />
      <Route
        path="/conta"
        element={
          <RequireAuth>
            <Account />
          </RequireAuth>
        }
      />
    </Routes>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <Navbar />
      <main className="container">
        <AppRoutes />
      </main>
      <footer className="footer">
        ScanDoc detecta texto oculto, microtexto e instruções escondidas para IA em documentos.
      </footer>
    </AuthProvider>
  );
}
