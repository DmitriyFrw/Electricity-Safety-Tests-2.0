/**
 * Единый источник пользовательских правил экзамена для UI.
 * Числовые пороги должны совпадать с backend (app/constants.py).
 */
/** Должно совпадать с app/constants.py (QUESTIONS_PER_TICKET). */
export const QUESTIONS_PER_TICKET = 10;

export const EXAM_RULES = {
  ticketMinutes: 20,
  minPassPercent: 75,
  maxErrorsAllowed: 3,
  questionsPerTicket: QUESTIONS_PER_TICKET,
} as const;

export function examPassThresholdText(): string {
  return `не менее ${EXAM_RULES.minPassPercent}% правильных ответов`;
}

function errorsCountWord(n: number): string {
  if (n === 1) return "ошибку";
  if (n < 5) return "ошибки";
  return "ошибок";
}

export function examErrorsAllowanceText(): string {
  const n = EXAM_RULES.maxErrorsAllowed;
  return `право на ${n} ${errorsCountWord(n)}`;
}

export function examTimeLimitText(): string {
  return `${EXAM_RULES.ticketMinutes} минут`;
}

export function examTicketTimeLabel(): string {
  return `${EXAM_RULES.ticketMinutes} минут`;
}

export function examQuestionsPerTicketLabel(): string {
  return String(EXAM_RULES.questionsPerTicket);
}

export function examPassThresholdLabel(): string {
  return `${EXAM_RULES.minPassPercent}%`;
}
