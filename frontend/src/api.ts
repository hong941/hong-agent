import type {
  Appointment,
  Dashboard,
  Department,
  Followup,
  KnowledgeHit,
  KnowledgeItem,
  Patient,
  SOAP,
  Summary,
  SystemStatus,
  TriageAnswerResponse,
  TriageResult,
  TriageStartResponse,
  User,
} from "./types";

const TOKEN_KEY = "ash_token";
const USER_KEY = "ash_user";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function getStoredUser(): User | null {
  const raw = localStorage.getItem(USER_KEY);
  return raw ? (JSON.parse(raw) as User) : null;
}

export function storeUser(user: User): void {
  localStorage.setItem(TOKEN_KEY, user.access_token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearUser(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  const token = getToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const response = await fetch(path, { ...options, headers });
  if (!response.ok) {
    const detail = await response.json().catch(() => ({}));
    throw new Error(detail.detail || `请求失败：${response.status}`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  login: (username: string, password: string) =>
    request<User>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    }),
  departments: () => request<Department[]>("/api/departments"),
  startTriage: (payload: {
    name: string;
    age: number;
    gender: string;
    chief_complaint: string;
    phone?: string;
  }) =>
    request<TriageStartResponse>("/api/triage/start", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  answerTriage: (conversation_id: number, message: string) =>
    request<TriageAnswerResponse>("/api/triage/answer", {
      method: "POST",
      body: JSON.stringify({ conversation_id, message }),
    }),
  completeTriage: (patient_id: number) =>
    request<TriageResult>("/api/triage/complete", {
      method: "POST",
      body: JSON.stringify({ patient_id }),
    }),
  bookAppointment: (patient_id: number, department_id: number) =>
    request<Appointment>("/api/appointments", {
      method: "POST",
      body: JSON.stringify({ patient_id, department_id }),
    }),
  patients: (status?: string) =>
    request<Patient[]>(`/api/patients${status ? `?status=${status}` : ""}`),
  patient: (id: number) => request<Patient>(`/api/patients/${id}`),
  summary: (id: number) => request<Summary>(`/api/patients/${id}/summary`),
  soap: (id: number) =>
    request<SOAP>(`/api/patients/${id}/soap`, { method: "POST" }),
  followup: (id: number) =>
    request<Followup>(`/api/patients/${id}/followup`),
  searchKnowledge: (q: string) =>
    request<KnowledgeHit[]>(`/api/knowledge/search?q=${encodeURIComponent(q)}`),
  dashboard: () => request<Dashboard>("/api/ops/dashboard"),
  handover: (patient_id: number) =>
    request<{ ok: boolean; message: string }>(`/api/ops/patients/${patient_id}/handover`, {
      method: "POST",
    }),
  adminKnowledge: () => request<KnowledgeItem[]>("/api/admin/knowledge"),
  createKnowledge: (payload: {
    title: string;
    category: string;
    content: string;
    source: string;
    tags: string[];
  }) =>
    request<KnowledgeItem>("/api/admin/knowledge", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  deleteKnowledge: (id: number) =>
    request<{ ok: boolean }>(`/api/admin/knowledge/${id}`, { method: "DELETE" }),
  adminAudit: () => request<import("./types").Audit[]>("/api/admin/audit"),
  systemStatus: () => request<SystemStatus>("/api/admin/system"),
};
