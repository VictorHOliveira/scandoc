import { auth } from "./firebase";

export interface Finding {
  severity: string;
  kind: string;
  title: string;
  description: string;
  location: string | null;
  snippet: string | null;
  bbox: number[] | null;
}

export interface ScanResult {
  filename: string;
  format: string;
  score: number;
  findings: Finding[];
  hidden_text: string;
  annotated_image: string | null;
  injection_matches: string[];
  summary: Record<string, unknown>;
}

export interface Plan {
  name: string;
  slug: string;
  description: string | null;
  daily_limit: number | null;
  price_brl: string;
  sort_order: number;
}

export interface Quota {
  used: number;
  limit: number | null;
  remaining: number | null;
  window_hours: number;
  resets_at: string;
}

export interface Me {
  user: { id: string; name: string; email: string };
  plan: Plan;
  quota: Quota;
}

export class ApiError extends Error {
  status: number;
  quota?: Quota;
  constructor(status: number, message: string, quota?: Quota) {
    super(message);
    this.status = status;
    this.quota = quota;
  }
}

const API_BASE = import.meta.env.VITE_API_URL ?? "";

async function bearerToken(): Promise<string | null> {
  if (!auth) return null;
  const user = auth.currentUser;
  if (!user) return null;
  try {
    return await user.getIdToken();
  } catch {
    return null;
  }
}

export async function api<T>(path: string, opts: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {};
  const token = await bearerToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (opts.body && !(opts.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }
  const res = await fetch(`${API_BASE}/api${path}`, { ...opts, headers });
  let data: unknown = null;
  try {
    data = await res.json();
  } catch {
    data = null;
  }
  if (!res.ok) {
    let message = "Erro inesperado";
    let quota: Quota | undefined;
    const d = data as { detail?: unknown; message?: string } | null;
    if (d) {
      const det = d.detail as { message?: string; quota?: Quota } | string | undefined;
      if (typeof det === "string") message = det;
      else if (det && typeof det === "object") {
        message = det.message ?? message;
        quota = det.quota;
      } else if (d.message) message = d.message;
    }
    throw new ApiError(res.status, message, quota);
  }
  return data as T;
}
