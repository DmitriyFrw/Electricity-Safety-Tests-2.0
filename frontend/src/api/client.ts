import type {
  Dashboard,
  Manual,
  SignedProtocol,
  TestEdit,
  TestListItem,
  User,
} from "../types/api";
import type { QuestionSave } from "../types/api";
import { deleteReact, getReact, postReact, putReact } from "./getReact";

/** API-слой: все вызовы через getReact / postReact (axios → JSON). */
export const api = {
  me: () => getReact<User | null>("/auth/me"),

  login: (username: string, password: string) =>
    postReact<User>("/auth/login", { username, password }),

  register: (username: string, password: string, password2: string) =>
    postReact<User>("/auth/register", { username, password, password2 }),

  logout: () => postReact<{ message: string }>("/auth/logout"),

  dashboard: () => getReact<Dashboard>("/dashboard"),

  listTests: () =>
    getReact<{ items: TestListItem[] }>("/tests").then((r) => r.items),

  createTest: (title: string, description?: string) =>
    postReact<{ id: number; title: string }>("/tests", {
      title,
      description: description || null,
    }),

  getTestEdit: (testId: number) => getReact<TestEdit>(`/tests/${testId}`),

  addTicket: (testId: number) => postReact<TestEdit>(`/tests/${testId}/tickets`),

  saveTicket: (testId: number, ticketId: number, questions: QuestionSave[]) =>
    putReact<TestEdit>(`/tests/${testId}/tickets/${ticketId}`, { questions }),

  deleteTicket: (testId: number, ticketId: number) =>
    deleteReact<TestEdit>(`/tests/${testId}/tickets/${ticketId}`),

  updateProfile: (body: { full_name: string; birth_date: string; job_title: string }) =>
    putReact<User>("/profile", body),

  listManuals: () => getReact<Manual[]>("/manuals"),

  /** Черновик протокола из данных профиля (роль Кот). */
  profileProtocolPdfUrl: () => "/api/profile/protocol.pdf",

  /** Подписанный протокол сданного экзамена. */
  signedProtocolPdfUrl: (testId: number, attemptId: number) =>
    `/api/tests/${testId}/exam/attempts/${attemptId}/protocol.pdf`,

  getSignedProtocol: (testId: number, attemptId: number) =>
    getReact<SignedProtocol>(`/tests/${testId}/exam/attempts/${attemptId}/protocol`),

  signProtocol: (testId: number, attemptId: number) =>
    postReact<SignedProtocol>(`/tests/${testId}/exam/attempts/${attemptId}/protocol/sign`),
};
