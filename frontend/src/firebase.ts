import { initializeApp, type FirebaseApp } from "firebase/app";
import { connectAuthEmulator, getAuth, type Auth } from "firebase/auth";

const USE_EMULATOR = import.meta.env.VITE_USE_EMULATOR === "true";

const required = [
  "VITE_FIREBASE_API_KEY",
  "VITE_FIREBASE_AUTH_DOMAIN",
  "VITE_FIREBASE_PROJECT_ID",
  "VITE_FIREBASE_APP_ID",
];

const missing = required.filter((k) => !import.meta.env[k]);

export const firebaseConfigured = USE_EMULATOR || missing.length === 0;

export const app: FirebaseApp | null = firebaseConfigured
  ? initializeApp({
      apiKey: import.meta.env.VITE_FIREBASE_API_KEY || "demo-api-key",
      authDomain:
        import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || "demo-scandoc.firebaseapp.com",
      projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || "demo-scandoc",
      storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || undefined,
      messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || undefined,
      appId: import.meta.env.VITE_FIREBASE_APP_ID || "demo-app-id",
    })
  : null;

export const auth: Auth | null = app ? getAuth(app) : null;

if (USE_EMULATOR && auth) {
  connectAuthEmulator(auth, "http://localhost:9099", { disableWarnings: true });
}
