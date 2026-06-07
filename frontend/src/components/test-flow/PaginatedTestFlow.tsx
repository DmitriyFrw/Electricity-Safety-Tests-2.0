import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import type { TicketExam } from "../../types/api";
import TestQuestionPanel, { hasSelectedValue } from "./TestQuestionPanel";

export type AnswersMap = Record<number, string>;

type Props = {
  tickets: TicketExam[];
  testTitle: string;
  subtitle?: string;
  cancelHref: string;
  onComplete: (answers: AnswersMap) => Promise<void>;
  completing?: boolean;
  completeError?: string;
  finishLabel?: string;
  allowEarlyFinish?: boolean;
};

export default function PaginatedTestFlow({
  tickets,
  testTitle,
  subtitle,
  cancelHref,
  onComplete,
  completing = false,
  completeError,
  finishLabel = "Завершить тест",
  allowEarlyFinish = true,
}: Props) {
  const [ticketIndex, setTicketIndex] = useState(0);
  const [questionIndex, setQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState<AnswersMap>({});

  const ticket = tickets[ticketIndex];
  const questions = ticket?.questions ?? [];
  const currentQuestion = questions[questionIndex];
  const selectedValue = currentQuestion ? answers[currentQuestion.id] : undefined;
  const hasAnswer = currentQuestion
    ? hasSelectedValue(selectedValue, Boolean(currentQuestion.multiple_choice))
    : false;

  const isLastQuestion = questionIndex >= questions.length - 1;
  const isLastTicket = ticketIndex >= tickets.length - 1;
  const isEndOfTicket = isLastQuestion && !isLastTicket;
  const isEndOfTest = isLastQuestion && isLastTicket;

  const ticketTitle = useMemo(
    () => ticket?.title?.trim() || `Билет ${ticketIndex + 1}`,
    [ticket?.title, ticketIndex]
  );

  if (!ticket || !currentQuestion) {
    return <p className="dash-card-note">В тесте нет вопросов.</p>;
  }

  const onSelect = (questionId: number, value: string) => {
    setAnswers((prev) => ({ ...prev, [questionId]: value }));
  };

  const goNextQuestion = () => {
    if (!hasAnswer || completing) return;
    setQuestionIndex((i) => i + 1);
  };

  const goNextTicket = () => {
    if (!hasAnswer || completing) return;
    setTicketIndex((i) => i + 1);
    setQuestionIndex(0);
  };

  const finish = () => {
    if (!hasAnswer || completing) return;
    void onComplete(answers);
  };

  return (
    <>
      {(testTitle || subtitle) && (
        <div className="dash-page-card test-flow-header">
          {testTitle && <h1>{testTitle}</h1>}
          {subtitle && <p className="dash-card-note">{subtitle}</p>}
          <p className="test-flow-progress">
            {ticketTitle} · билет {ticketIndex + 1} из {tickets.length}
          </p>
        </div>
      )}
      {!testTitle && !subtitle && (
        <p className="test-flow-progress" style={{ marginBottom: "var(--spacing-3)" }}>
          {ticketTitle} · билет {ticketIndex + 1} из {tickets.length}
        </p>
      )}

      <TestQuestionPanel
        ticket={ticket}
        questionIndex={questionIndex}
        selectedValue={selectedValue}
        onSelect={onSelect}
        disabled={completing}
      />

      {completeError && <p className="auth-error">{completeError}</p>}

      <div className="test-flow-actions">
        {!isLastQuestion && (
          <button
            type="button"
            className="dash-exam-btn"
            disabled={!hasAnswer || completing}
            onClick={goNextQuestion}
            style={{ border: "none", cursor: "pointer" }}
          >
            Далее
          </button>
        )}

        {isEndOfTicket && (
          <button
            type="button"
            className="dash-exam-btn"
            disabled={!hasAnswer || completing}
            onClick={goNextTicket}
            style={{ border: "none", cursor: "pointer" }}
          >
            Перейти к следующему билету
          </button>
        )}

        {(isEndOfTest || (isEndOfTicket && allowEarlyFinish)) && (
          <button
            type="button"
            className="btn btn-outline"
            disabled={!hasAnswer || completing}
            onClick={finish}
          >
            {completing ? "Отправка…" : finishLabel}
          </button>
        )}

        <Link to={cancelHref} className="dash-card-link">
          Отмена
        </Link>
      </div>
    </>
  );
}
