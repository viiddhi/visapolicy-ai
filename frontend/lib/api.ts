const BASE = "/api/v1";

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function token(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("vp_token");
}

function extractMessage(err: unknown, fallback: string): string {
  const detail = (err as { detail?: unknown })?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail.length > 0) {
    return detail
      .map((d) => (d && typeof d === "object" && "msg" in d ? String((d as { msg: unknown }).msg) : String(d)))
      .join("; ");
  }
  return fallback;
}

async function request<T>(path: string, opts: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(opts.headers as Record<string, string>),
  };
  const t = token();
  if (t) headers["Authorization"] = `Bearer ${t}`;

  const res = await fetch(`${BASE}${path}`, { ...opts, headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(extractMessage(err, "Request failed"), res.status);
  }
  return res.json();
}

// ---- auth ----
export const register = (email: string, password: string, name: string) =>
  request<{ access_token: string }>("/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password, name }),
  });

export const login = (email: string, password: string) =>
  request<{ access_token: string }>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });

export const getMe = () => request<Profile>("/auth/me");

export const forgotPassword = (email: string) =>
  request<{ message: string }>("/auth/forgot-password", {
    method: "POST",
    body: JSON.stringify({ email }),
  });

export const resetPassword = (token: string, newPassword: string) =>
  request<{ message: string }>("/auth/reset-password", {
    method: "POST",
    body: JSON.stringify({ token, new_password: newPassword }),
  });

// ---- profile ----
export const getProfile = () => request<Profile>("/profile");

export const updateProfile = (data: Partial<Profile>) =>
  request<Profile>("/profile", { method: "PATCH", body: JSON.stringify(data) });

// ---- dashboard ----
export const getDashboard = () => request<DashboardResponse>("/dashboard");

// ---- changes ----
export const getChanges = (params?: { impact?: string; visa?: string }) => {
  const qs = new URLSearchParams(params as Record<string, string>).toString();
  return request<RuleChange[]>(`/changes${qs ? "?" + qs : ""}`);
};

export const getChange = (id: string) => request<RuleChange>(`/changes/${id}`);

// ---- types ----
export interface Profile {
  id: string;
  email: string;
  name?: string;
  primary_visa_type?: string;
  visa_status?: string;
  authorized_until?: string;
  gc_stage?: string;
  priority_date?: string;
  preference_category?: string;
  country_of_birth?: string;
  employer_type?: string;
  placement_type?: string;
  degree_field?: string;
  job_title?: string;
  on_opt?: boolean;
  opt_type?: string;
  opt_expiry?: string;
  dependent_visa_types?: string[];
  alert_frequency?: string;
  min_impact_level?: string;
  onboarding_completed: boolean;
}

export interface RuleChange {
  id: string;
  document_id: string;
  document_title?: string;
  document_source_url?: string;
  section?: string;
  topic: string;
  old_rule: string;
  new_rule: string;
  plain_english_summary: string;
  impact_level: "low" | "medium" | "high";
  action_required: boolean;
  action_description?: string;
  visa_categories_affected?: string[];
  who_is_affected?: string[];
  tags?: string[];
  published_at?: string;
  effective_at?: string;
  created_at: string;
}

export interface FeedItem {
  relevance_score: number;
  relevance_reasons: string[];
  change: RuleChange;
}

export interface DashboardResponse {
  feed: FeedItem[];
  stats: { total_relevant: number; high_impact: number; action_required: number };
}
