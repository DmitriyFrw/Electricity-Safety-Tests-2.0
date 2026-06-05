export interface UserAdmin {
  id: number;
  username: string;
  display_name: string;
  role: string;
  role_label: string;
  created_at: string | null;
  profile_complete: boolean;
}

export interface User {
  id: number;
  username: string;
  display_name: string;
  role: "admin" | "ezh" | "kot" | string;
  role_label: string;
  can_create_tests: boolean;
  safety_group: string;
  safety_group_desc: string;
  full_name: string | null;
  birth_date: string | null;
  job_title: string | null;
  business_unit: string | null;
  profile_complete: boolean;
}

export interface Manual {
  id: string;
  title: string;
  filename: string;
}

export interface AttemptRow {
  attempt_id: number;
  test_id: number;
  test_title: string;
  finished_at: string;
  correct: number;
  total: number;
  percent: number;
  errors: number;
  grade: string;
  grade_class: string;
}

export interface CreatedTest {
  id: number;
  title: string;
  ticket_count: number;
  created_at: string;
}

export interface StaffProtocolExport {
  attempt_id: number;
  test_id: number;
  test_title: string;
  examinee_full_name: string;
  percent: number;
  profile_complete: boolean;
}

export interface AdminProtocolDraftUser {
  user_id: number;
  username: string;
  display_name: string;
  profile_complete: boolean;
}

export interface Dashboard {
  user: User;
  can_create_tests: boolean;
  tickets_count: number;
  exam_test_id: number | null;
  min_pass_percent: number;
  max_errors_allowed: number;
  materials_updated: string | null;
  last_percent: number | null;
  last_errors: number | null;
  last_grade: string | null;
  last_grade_class: string | null;
  last_test_title: string | null;
  last_test_date: string | null;
  next_check_date: string;
  signed_protocol: SignedProtocol | null;
  staff_protocol_exports: StaffProtocolExport[];
  admin_protocol_drafts: AdminProtocolDraftUser[];
  created_tests: CreatedTest[];
  attempts: AttemptRow[];
}

export interface TestListItem {
  id: number;
  title: string;
  description: string | null;
  author_id: number;
  author_username: string;
  ticket_count: number;
  ready: boolean;
  can_edit: boolean;
}

export interface QuestionExam {
  id: number;
  position: number;
  text: string;
  option_a: string;
  option_b: string;
  option_c: string;
  option_d: string;
}

export interface TicketExam {
  id: number;
  position: number;
  title: string | null;
  option_count: number;
  questions: QuestionExam[];
}

export interface ExamPaper {
  id: number;
  title: string;
  min_pass_percent: number;
  tickets: TicketExam[];
}

export interface ExamSession {
  attempt_id: number;
  test_id: number;
  test_title: string;
  ticket_count: number;
  completed_ticket_ids: number[];
  next_ticket_id: number | null;
  time_limit_seconds: number;
}

export interface ExamTicketPaper {
  test_id: number;
  test_title: string;
  attempt_id: number;
  ticket: TicketExam;
  ticket_index: number;
  ticket_count: number;
  min_pass_percent: number;
  time_limit_seconds: number;
  seconds_remaining: number;
  deadline_at: string;
}

export interface TicketResultRow {
  n: number;
  correct: number;
  total: number;
  percent: number;
  grade: string;
  grade_class: string;
}

export interface ExamResult {
  attempt_id: number;
  test_id: number;
  test_title: string;
  correct: number;
  total: number;
  percent: number;
  errors: number;
  grade: string;
  grade_class: string;
  passed_exam: boolean;
  protocol_signed: boolean;
  min_pass_percent: number;
  ticket_rows: TicketResultRow[];
}

export interface SignedProtocol {
  attempt_id: number;
  test_id: number;
  signer_id: number;
  signer_username: string;
  examinee_id: number;
  examinee_full_name: string;
  examinee_birth_date: string;
  examinee_job_title: string;
  test_title: string;
  result_percent: number;
  signed_at: string;
}

export interface QuestionEdit {
  id: number;
  position: number;
  text: string;
  correct_index: number;
  option_a: string;
  option_b: string;
  option_c: string;
  option_d: string;
}

export interface TicketEdit {
  id: number;
  position: number;
  title: string | null;
  option_count: number;
  complete: boolean;
  questions: QuestionEdit[];
}

export interface TestEdit {
  id: number;
  title: string;
  description: string | null;
  ready: boolean;
  max_tickets: number;
  questions_per_ticket: number;
  tickets: TicketEdit[];
}

export interface QuestionSave {
  position: number;
  text: string;
  option_a: string;
  option_b: string;
  option_c: string;
  option_d: string;
  correct: string;
}

export interface TicketSavePayload {
  title?: string | null;
  option_count: number;
  questions: QuestionSave[];
}
