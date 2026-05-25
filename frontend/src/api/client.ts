import { API_BASE_URL } from "../config";

export type UserRole = "student" | "instructor" | "reviewer" | "admin";
export type AttemptStatus = "active" | "submitted" | "expired" | "voided";
export type EventSeverity = "info" | "low" | "medium" | "high" | "critical";
export type ReviewOutcome = "clear" | "needs_follow_up" | "violation_confirmed" | "void_attempt";

export interface UserPublic {
  id: number;
  email: string;
  username: string;
  role: UserRole;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: UserPublic;
}

export interface ExamSummary {
  id: number;
  title: string;
  description?: string | null;
  duration_seconds: number;
}

export interface OptionPublic {
  id: number;
  body: string;
}

export interface QuestionPublic {
  id: number;
  prompt: string;
  order_index: number;
  points: number;
  options: OptionPublic[];
}

export interface ExamDetail extends ExamSummary {
  questions: QuestionPublic[];
}

export interface OptionCreate {
  body: string;
  is_correct: boolean;
}

export interface QuestionCreate {
  prompt: string;
  order_index: number;
  points: number;
  options: OptionCreate[];
}

export interface ExamCreate {
  title: string;
  description?: string;
  duration_seconds: number;
  questions: QuestionCreate[];
}

export interface AttemptPublic {
  id: number;
  exam_id: number;
  status: AttemptStatus;
  started_at: string;
  due_at: string;
  submitted_at?: string | null;
  score?: number | null;
  proctoring_session_id?: number | null;
}

export interface SubmitResult {
  attempt_id: number;
  status: AttemptStatus;
  score: number;
  submitted_at: string;
}

export interface ProctoringEventPublic {
  id: number;
  event_type: string;
  severity: EventSeverity;
  confidence?: number | null;
  occurred_at: string;
  received_at: string;
  payload: Record<string, unknown>;
  evidence_asset_id?: number | null;
}

export interface EvidenceAssetPublic {
  id: number;
  storage_key: string;
  content_type: string;
  byte_size: number;
  sha256: string;
  created_at: string;
}

export interface FrameAnalysisResponse {
  frame_id: string;
  signals: Record<string, unknown>;
  events: ProctoringEventPublic[];
  evidence_asset?: EvidenceAssetPublic | null;
}

export interface ReviewAttemptSummary {
  attempt_id: number;
  exam_id: number;
  exam_title: string;
  candidate_email: string;
  candidate_username: string;
  status: AttemptStatus;
  score?: number | null;
  started_at: string;
  due_at: string;
  submitted_at?: string | null;
  event_count: number;
  latest_event_type?: string | null;
}

export interface ReviewDecisionPublic {
  id: number;
  attempt_id: number;
  reviewer_id: number;
  outcome: ReviewOutcome;
  notes?: string | null;
  created_at: string;
}

export interface AttemptTimeline {
  attempt: AttemptPublic;
  events: ProctoringEventPublic[];
  evidence_assets: EvidenceAssetPublic[];
  review_decisions: ReviewDecisionPublic[];
}

interface RequestOptions extends RequestInit {
  token?: string | null;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers = new Headers(options.headers);
  if (options.token) {
    headers.set("Authorization", `Bearer ${options.token}`);
  }
  if (options.body && !(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers
  });

  if (!response.ok) {
    let message = `${response.status} ${response.statusText}`;
    try {
      const body = await response.json();
      message = body.detail ?? message;
    } catch {
      // Keep the HTTP status as the fallback error.
    }
    throw new Error(message);
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

export const api = {
  signup: (payload: { email: string; username: string; password: string }) =>
    request<TokenResponse>("/auth/signup", { method: "POST", body: JSON.stringify(payload) }),
  login: (payload: { email: string; password: string }) =>
    request<TokenResponse>("/auth/login", { method: "POST", body: JSON.stringify(payload) }),
  listExams: (token: string) => request<ExamSummary[]>("/exams", { token }),
  getExam: (token: string, examId: number) => request<ExamDetail>(`/exams/${examId}`, { token }),
  createExam: (token: string, payload: ExamCreate) =>
    request<ExamDetail>("/exams", { method: "POST", token, body: JSON.stringify(payload) }),
  createAttempt: (token: string, examId: number, clientFingerprint: string) =>
    request<AttemptPublic>("/attempts", {
      method: "POST",
      token,
      body: JSON.stringify({ exam_id: examId, client_fingerprint: clientFingerprint })
    }),
  getAttempt: (token: string, attemptId: number) => request<AttemptPublic>(`/attempts/${attemptId}`, { token }),
  getAttemptQuestions: (token: string, attemptId: number) =>
    request<ExamDetail>(`/attempts/${attemptId}/questions`, { token }),
  saveAnswer: (token: string, attemptId: number, questionId: number, selectedOptionId: number) =>
    request(`/attempts/${attemptId}/answers`, {
      method: "POST",
      token,
      body: JSON.stringify({ question_id: questionId, selected_option_id: selectedOptionId })
    }),
  submitAttempt: (token: string, attemptId: number) =>
    request<SubmitResult>(`/attempts/${attemptId}/submit`, { method: "POST", token }),
  sendProctoringEvent: (
    token: string,
    sessionId: number,
    payload: { event_type: string; confidence?: number; payload?: Record<string, unknown> }
  ) =>
    request<ProctoringEventPublic>(`/proctoring/sessions/${sessionId}/events`, {
      method: "POST",
      token,
      body: JSON.stringify(payload)
    }),
  analyzeFrame: (token: string, sessionId: number, blob: Blob) => {
    const form = new FormData();
    form.append("file", blob, `frame-${Date.now()}.jpg`);
    return request<FrameAnalysisResponse>(`/proctoring/sessions/${sessionId}/analyze-frame`, {
      method: "POST",
      token,
      body: form
    });
  },
  listReviewAttempts: (token: string) => request<ReviewAttemptSummary[]>("/review/attempts", { token }),
  getTimeline: (token: string, attemptId: number) =>
    request<AttemptTimeline>(`/review/attempts/${attemptId}/timeline`, { token }),
  createReviewDecision: (token: string, attemptId: number, outcome: ReviewOutcome, notes: string) =>
    request<ReviewDecisionPublic>(`/review/attempts/${attemptId}/decision`, {
      method: "POST",
      token,
      body: JSON.stringify({ outcome, notes })
    })
};
