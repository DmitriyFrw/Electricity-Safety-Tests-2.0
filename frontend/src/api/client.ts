import type {
  Dashboard,
  ExamPaper,
  ExamResult,
  TestEdit,
  TestListItem,
  User,
} from "../types/api";
import type { QuestionSave } from "../types/api";

const API = "/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    credentials: "include",
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch {
      /* ignore */
    }
    throw new Error(typeof detail === "string" ? detail : "Ошибка запроса");
  }
  if (res.status === 204) {
    return undefined as T;
  }
  return res.json() as Promise<T>;
}

export const api = {
  me: () => request<User | null>("/auth/me"),

  login: (username: string, password: string) =>
    request<User>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    }),

  register: (username: string, password: string, password2: string) =>
    request<User>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ username, password, password2 }),
    }),

  logout: () =>
    request<{ message: string }>("/auth/logout", { method: "POST" }),

  dashboard: () => request<Dashboard>("/dashboard"),

  listTests: () =>
    request<{ items: TestListItem[] }>("/tests").then((r) => r.items),

  createTest: (title: string, description?: string) =>
    request<{ id: number; title: string }>("/tests", {
      method: "POST",
      body: JSON.stringify({ title, description: description || null }),
    }),

  getTestEdit: (testId: number) => request<TestEdit>(`/tests/${testId}`),

  getExamPaper: (testId: number) => request<ExamPaper>(`/tests/${testId}/exam`),

  submitExam: (testId: number, answers: { question_id: number; value: string }[]) =>
    request<ExamResult>(`/tests/${testId}/exam`, {
      method: "POST",
      body: JSON.stringify({ answers }),
    }),

  addTicket: (testId: number) =>
    request<TestEdit>(`/tests/${testId}/tickets`, { method: "POST" }),

  saveTicket: (testId: number, ticketId: number, questions: QuestionSave[]) =>
    request<TestEdit>(`/tests/${testId}/tickets/${ticketId}`, {
      method: "PUT",
      body: JSON.stringify({ questions }),
    }),

  deleteTicket: (testId: number, ticketId: number) =>
    request<TestEdit>(`/tests/${testId}/tickets/${ticketId}`, {
      method: "DELETE",
    }),
};
