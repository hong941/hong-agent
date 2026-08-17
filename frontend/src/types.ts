export interface User {
  access_token: string;
  role: string;
  name: string;
  user_id: number;
}

export interface Department {
  id: number;
  name: string;
  code: string;
  description: string;
  avg_wait_minutes: number;
  load: number;
  capacity: number;
}

export interface TriageStartResponse {
  patient_id: number;
  conversation_id: number;
  message: string;
}

export interface TriageAnswerResponse {
  message: string;
  can_complete: boolean;
  user_message_count: number;
}

export interface TriageResult {
  patient_id: number;
  tier: string;
  score: number;
  department: string;
  department_id: number;
  confidence: number;
  reasons: string[];
  recommendation: string;
  next_steps: string[];
  disclaimer: string;
}

export interface Appointment {
  id: number;
  patient_id: number;
  doctor_id: number | null;
  department_id: number;
  scheduled_time: string;
  status: string;
  notes: string;
  doctor_name: string | null;
  department_name: string | null;
  patient_name: string | null;
}

export interface Patient {
  id: number;
  name: string;
  age: number;
  gender: string;
  phone: string;
  chief_complaint: string;
  symptoms: string[];
  allergies: string;
  medications: string;
  medical_history: string;
  risk_level: string;
  risk_score: number;
  triage_reason: string;
  department_id: number | null;
  status: string;
  created_at: string;
  department_name: string | null;
}

export interface KnowledgeHit {
  id: number;
  title: string;
  category: string;
  content: string;
  source: string;
  score: number;
}

export interface Citation {
  title: string;
  source: string;
  category: string;
  score: number;
}

export interface Summary {
  patient_id: number;
  summary: string;
  citations: Citation[];
  disclaimer: string;
}

export interface SOAP {
  patient_id: number;
  subjective: string;
  objective: string;
  assessment: string;
  plan: string;
  citations: Citation[];
  disclaimer: string;
}

export interface Followup {
  patient_id: number;
  plan: string;
  citations: Citation[];
  disclaimer: string;
}

export interface Audit {
  id: number;
  actor: string;
  action: string;
  target_type: string;
  target_id: number | null;
  detail: Record<string, unknown>;
  created_at: string;
}

export interface Dashboard {
  waiting_count: number;
  triage_count: number;
  scheduled_count: number;
  red_alert_count: number;
  risk_distribution: { tier: string; count: number }[];
  department_status: {
    id: number;
    name: string;
    load: number;
    avg_wait_minutes: number;
    waiting_count: number;
  }[];
  queue: Patient[];
  alerts: {
    patient_id: number;
    patient_name: string;
    age: number;
    chief_complaint: string;
    risk_level: string;
    status: string;
    department_name: string | null;
  }[];
  recent_audit: Audit[];
}

export interface KnowledgeItem {
  id: number;
  title: string;
  category: string;
  content: string;
  source: string;
  tags: string[];
  created_at: string;
}

export interface SystemStatus {
  provider_mode: string;
  model_name: string;
  database_url: string;
  api_base_url: string;
  knowledge_count: number;
  patient_count: number;
}
