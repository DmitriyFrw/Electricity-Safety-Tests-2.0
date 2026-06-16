import type {
  ExamResult,
  Manual,
  SignedProtocol,
  TestEdit,
  TestListItem,
  ExamScheduleRow,
  KotUser,
  User,
  UserAdmin,
  WikiPage,
  WikiPageListItem,
  WikiAttachment,
} from "../types/api";
import {
  deleteReact,
  downloadReact,
  getReact,
  postFormReact,
  postReact,
  putReact,
} from "./getReact";

/** API-слой: все вызовы через getReact / postReact (axios → JSON). */
export const api = {
  login: (username: string, password: string) =>
    postReact<User>("/auth/login", { username, password }),

  register: (username: string, password: string, password2: string) =>
    postReact<User>("/auth/register", { username, password, password2 }),

  logout: () => postReact<{ message: string }>("/auth/logout"),

  listTests: () =>
    getReact<{ items: TestListItem[] }>("/tests").then((r) => r.items),

  createTest: (title: string, description?: string, safety_group = "II") =>
    postReact<{ id: number; title: string; safety_group: string }>("/tests", {
      title,
      description: description || null,
      safety_group,
    }),

  updateTestSettings: (
    testId: number,
    settings: { random_ticket_order: boolean; random_option_order: boolean }
  ) => putReact<TestEdit>(`/tests/${testId}/settings`, settings),

  publishTest: (testId: number) => postReact<TestEdit>(`/tests/${testId}/publish`),

  deleteTest: (testId: number) => deleteReact<void>(`/tests/${testId}`),

  getTrainingResult: (testId: number, attemptId: number) =>
    getReact<ExamResult>(`/tests/${testId}/training/attempts/${attemptId}/result`),

  updateProfile: (body: {
    full_name: string;
    birth_date: string;
    job_title: string;
    business_unit: string;
  }) => putReact<User>("/profile", body),

  listManuals: () => getReact<Manual[]>("/manuals"),

  listAdminUsers: () => getReact<UserAdmin[]>("/admin/users"),

  listKotUsers: () => getReact<KotUser[]>("/staff/kot-users"),

  updateKotSafetyGroup: (userId: number, safety_group: string) =>
    putReact<KotUser>(`/staff/kot-users/${userId}/safety-group`, { safety_group }),

  listExamSchedule: () => getReact<ExamScheduleRow[]>("/staff/exam-schedule"),

  downloadExamScheduleExport: () =>
    downloadReact("/staff/exam-schedule-export.xlsx", "grafik_ebkamena.xlsx"),

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

  getExamResult: (testId: number, attemptId: number) =>
    getReact<ExamResult>(`/tests/${testId}/exam/attempts/${attemptId}/result`),

  abandonExam: (testId: number) =>
    postReact<ExamResult>(`/tests/${testId}/exam/abandon`),

  listWikiPages: () => getReact<WikiPageListItem[]>("/wiki/pages"),

  getWikiPage: (pageId: number) => getReact<WikiPage>(`/wiki/pages/${pageId}`),

  createWikiPage: (title: string, content: string) =>
    postReact<WikiPage>("/wiki/pages", { title, content }),

  updateWikiPage: (pageId: number, title: string, content: string) =>
    putReact<WikiPage>(`/wiki/pages/${pageId}`, { title, content }),

  deleteWikiPage: (pageId: number) => deleteReact<void>(`/wiki/pages/${pageId}`),

  uploadWikiAttachment: (pageId: number, file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return postFormReact<WikiAttachment>(`/wiki/pages/${pageId}/attachments`, fd);
  },

  deleteWikiAttachment: (attachmentId: number) =>
    deleteReact<WikiPage>(`/wiki/attachments/${attachmentId}`),
};
