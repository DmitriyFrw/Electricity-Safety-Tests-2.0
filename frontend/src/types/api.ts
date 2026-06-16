export interface UserAdmin {
  id: number;
  username: string;
  display_name: string;
  role: string;
  role_label: string;
  safety_group: string | null;
  created_at: string | null;
  profile_complete: boolean;
}

export interface KotUser {
  id: number;
  username: string;
  display_name: string;
  safety_group: string;
  safety_group_desc: string;
  profile_complete: boolean;
}

export interface ExamScheduleRow {
  full_name: string;
  birth_date: string;
  job_title: string;
  business_unit: string;
  safety_group: string;
  role_label: string;
  last_exam_date: string;
  next_exam_date: string;
  exam_grade: string;
}

export interface User {
  id: number;
  username: string;
  display_name: string;
  role: "admin" | "ezh" | "kot" | string;
  role_label: string;
  can_create_tests: boolean;
  can_edit_wiki: boolean;
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

export interface WikiAttachment {
  id: number;
  filename: string;
  mime_type: string;
  size_bytes: number;
  url: string;
  is_image: boolean;
}

export interface WikiPageListItem {
  id: number;
  title: string;
  updated_at: string;
}

export interface WikiPage extends WikiPageListItem {
  content: string;
  attachments: WikiAttachment[];
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

export interface AdminGradeBucket {
  grade: string;
  count: number;
  percent: number;
}

export interface AdminMonthlyResult {
  year: number;
  month: number;
  average_percent: number;
  attempt_count: number;
}

export interface AdminActivity {
  user_display_name: string;
  test_title: string;
  percent: number;
  grade: string;
  finished_at: string;
}

export interface AdminStats {
  users_count: number;
  tests_count: number;
  exams_passed_count: number;
  average_percent: number;
  grade_distribution: AdminGradeBucket[];
  monthly_results: AdminMonthlyResult[];
  recent_activity: AdminActivity[];
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
  last_passed_exam_date: string | null;
  last_passed_exam_percent: number | null;
  last_passed_exam_grade: string | null;
  next_check_date: string;
  signed_protocol: SignedProtocol | null;
  staff_protocol_exports: StaffProtocolExport[];
  admin_protocol_drafts: AdminProtocolDraftUser[];
  created_tests: CreatedTest[];
  attempts: AttemptRow[];
  attempts_total: number;
}

export interface TestListItem {
  id: number;
  title: string;
  description: string | null;
  safety_group: string;
  author_id: number;
  author_username: string;
  ticket_count: number;
  published: boolean;
  content_complete: boolean;
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
  option_count?: number;
  multiple_choice?: boolean;
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
  random_ticket_order?: boolean;
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

export interface QuestionResult {
  question_id: number;
  ticket_id: number;
  ticket_position: number;
  ticket_title: string | null;
  question_position: number;
  question_text: string;
  option_a: string;
  option_b: string;
  option_c: string;
  option_d: string;
  option_count: number;
  correct_index: number;
  correct_indexes?: number[];
  selected_index: number | null;
  selected_indexes?: number[];
  is_correct: boolean;
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
  question_results?: QuestionResult[];
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
  correct_indexes?: number[];
  option_count?: number;
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
  safety_group: string;
  published: boolean;
  content_complete: boolean;
  ready: boolean;
  max_tickets: number;
  questions_per_ticket: number;
  random_ticket_order: boolean;
  random_option_order: boolean;
  tickets: TicketEdit[];
}

export interface QuestionSave {
  position: number;
  text: string;
  option_count: number;
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
