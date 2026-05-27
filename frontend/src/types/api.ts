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
  test_id: number;
  test_title: string;
  correct: number;
  total: number;
  percent: number;
  errors: number;
  grade: string;
  grade_class: string;
  passed_exam: boolean;
  min_pass_percent: number;
  ticket_rows: TicketResultRow[];
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
