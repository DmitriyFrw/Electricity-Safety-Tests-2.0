import type {
  Dashboard,
  Manual,
  SignedProtocol,
  TestEdit,
  TestListItem,
  User,
  UserAdmin,
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

  deleteTest: (testId: number) => deleteReact<void>(`/tests/${testId}`),

  addTicket: (testId: number) => postReact<TestEdit>(`/tests/${testId}/tickets`),

  saveTicket: (testId: number, ticketId: number, questions: QuestionSave[]) =>
    putReact<TestEdit>(`/tests/${testId}/tickets/${ticketId}`, { questions }),

  deleteTicket: (testId: number, ticketId: number) =>
    deleteReact<TestEdit>(`/tests/${testId}/tickets/${ticketId}`),

  updateProfile: (body: {
    full_name: string;
    birth_date: string;
    job_title: string;
    business_unit: string;
  }) => putReact<User>("/profile", body),

  listManuals: () => getReact<Manual[]>("/manuals"),

  listAdminUsers: () => getReact<UserAdmin[]>("/admin/users"),

  updateUserRole: (userId: number, role: string) =>
    putReact<UserAdmin>(`/admin/users/${userId}/role`, { role }),

  /** Черновик протокола из профиля пользователя (только admin). */
  adminUserProtocolDraftPdfUrl: (userId: number) =>
    `/api/admin/users/${userId}/protocol-draft.pdf`,

  /** Черновик протокола из данных профиля (роль Кот). */
  profileProtocolPdfUrl: () => "/api/profile/protocol.pdf",

  /** Черновик из профиля экзаменуемого (admin / Еж). */
  attemptProtocolDraftPdfUrl: (testId: number, attemptId: number) =>
    `/api/tests/${testId}/exam/attempts/${attemptId}/protocol-draft.pdf`,

  /** Форма протокола по попытке (admin / Еж, после успешной сдачи). */
  attemptProtocolFormPdfUrl: (testId: number, attemptId: number) =>
    `/api/tests/${testId}/exam/attempts/${attemptId}/protocol-form.pdf`,

  /** Подписанный протокол сданного экзамена. */
  signedProtocolPdfUrl: (testId: number, attemptId: number) =>
    `/api/tests/${testId}/exam/attempts/${attemptId}/protocol.pdf`,

  getSignedProtocol: (testId: number, attemptId: number) =>
    getReact<SignedProtocol>(`/tests/${testId}/exam/attempts/${attemptId}/protocol`),

  signProtocol: (testId: number, attemptId: number) =>
    postReact<SignedProtocol>(`/tests/${testId}/exam/attempts/${attemptId}/protocol/sign`),
};
