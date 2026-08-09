import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import {
  createUserWithEmailAndPassword,
  GoogleAuthProvider,
  onAuthStateChanged,
  signInWithEmailAndPassword,
  signInWithPopup,
  signOut,
  updateProfile,
  type User as FirebaseUser,
} from "firebase/auth";
import { auth, firebaseConfigured } from "../firebase";
import { api, ApiError, type Me } from "../api";

interface AuthContextValue {
  me: Me | null;
  user: FirebaseUser | null;
  loading: boolean;
  configured: boolean;
  login: (email: string, password: string) => Promise<void>;
  loginGoogle: () => Promise<void>;
  register: (name: string, email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [me, setMe] = useState<Me | null>(null);
  const [user, setUser] = useState<FirebaseUser | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    if (!auth?.currentUser) {
      setMe(null);
      return;
    }
    try {
      setMe(await api<Me>("/auth/me"));
    } catch {
      setMe(null);
    }
  }, []);

  const fetchMe = useCallback(async (): Promise<Me | null> => {
    for (let attempt = 0; attempt < 3; attempt++) {
      try {
        return await api<Me>("/auth/me");
      } catch (err) {
        const retryable = err instanceof ApiError && (err.status === 0 || err.status === 401);
        if (!retryable || attempt === 2) return null;
        await new Promise((resolve) => setTimeout(resolve, 1500 * (attempt + 1)));
      }
    }
    return null;
  }, []);

  useEffect(() => {
    if (!auth) {
      setLoading(false);
      return;
    }
    const unsub = onAuthStateChanged(auth, (fbUser) => {
      setUser(fbUser);
      if (fbUser) {
        fetchMe()
          .then(setMe)
          .catch(() => setMe(null))
          .finally(() => setLoading(false));
      } else {
        setMe(null);
        setLoading(false);
      }
    });
    return () => unsub();
  }, [fetchMe]);

  const login = useCallback(async (email: string, password: string) => {
    if (!auth) throw new Error("Firebase não configurado");
    setLoading(true);
    try {
      await signInWithEmailAndPassword(auth, email, password);
    } catch (e) {
      setLoading(false);
      throw e;
    }
  }, []);

  const loginGoogle = useCallback(async () => {
    if (!auth) throw new Error("Firebase não configurado");
    setLoading(true);
    try {
      await signInWithPopup(auth, new GoogleAuthProvider());
    } catch (e) {
      setLoading(false);
      throw e;
    }
  }, []);

  const register = useCallback(
    async (name: string, email: string, password: string) => {
      if (!auth) throw new Error("Firebase não configurado");
      setLoading(true);
      try {
        const cred = await createUserWithEmailAndPassword(auth, email, password);
        if (name) {
          await updateProfile(cred.user, { displayName: name });
        }
      } catch (e) {
        setLoading(false);
        throw e;
      }
    },
    []
  );

  const logout = useCallback(async () => {
    if (auth) await signOut(auth);
    setMe(null);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{ me, user, loading, configured: firebaseConfigured, login, loginGoogle, register, logout, refresh }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth deve ser usado dentro de AuthProvider");
  return ctx;
}
