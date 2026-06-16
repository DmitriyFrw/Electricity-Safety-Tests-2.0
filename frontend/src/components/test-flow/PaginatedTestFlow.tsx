import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import type { TicketExam } from "../../types/api";
import TestQuestionPanel, { hasSelectedValue } from "./TestQuestionPanel";

export type AnswersMap = Record<number, string>;

type Props = {
  tickets: TicketExam[];
  testTitle: string;
  subtitle?: string;
  ticketMeta?: string;
  timerText?: string;
  timerWarn?: boolean;
  cancelHref: string;
  onComplete: (answers: AnswersMap) => Promise<void>;
  completing?: boolean;
  completeError?: string;
  finishLabel?: string;
  allowEarlyFinish?: boolean;
  allowBack?: boolean;
  showCancel?: boolean;
};

export default function PaginatedTestFlow({
  tickets,
  testTitle,
  subtitle,
  ticketMeta,
  timerText,
  timerWarn = false,
  cancelHref,
  onComplete,
  completing = false,
  completeError,
  finishLabel = "Завершить тест",
  allowEarlyFinish = true,
  allowBack = false,
  showCancel = true,
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

  const isFirstQuestion = questionIndex <= 0;
  const isLastQuestion = questionIndex >= questions.length - 1;
  const isFirstTicket = ticketIndex <= 0;
  const isLastTicket = ticketIndex >= tickets.length - 1;
  const isEndOfTicket = isLastQuestion && !isLastTicket;
  const isEndOfTest = isLastQuestion && isLastTicket;
  const canGoBack = allowBack && (!isFirstQuestion || !isFirstTicket);

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

  const goBack = () => {
    if (!canGoBack || completing) return;
    if (questionIndex > 0) {
      setQuestionIndex((i) => i - 1);
      return;
    }
    const prevTicket = tickets[ticketIndex - 1];
    const prevQuestionCount = prevTicket?.questions.length ?? 0;
    setTicketIndex((i) => i - 1);
    setQuestionIndex(Math.max(prevQuestionCount - 1, 0));
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

  const progressLine =
    ticketMeta ??
    `${ticketTitle} · билет ${ticketIndex + 1} из ${tickets.length}`;

  const showHeader = Boolean(testTitle || subtitle || timerText || ticketMeta);

  return (
    <div className="mockup-ticket test-flow-shell">
      {showHeader && (
        <header className="mockup-ticket__card mockup-ticket__header">
          {testTitle && <h1 className="mockup-ticket__title">{testTitle}</h1>}
          {timerText && (
            <p className={`mockup-ticket__timer ${timerWarn ? "mockup-ticket__timer--warn" : ""}`}>
              {timerText}
            </p>
          )}
          {subtitle && <p className="mockup-ticket__subtitle">{subtitle}</p>}
          <p className="mockup-ticket__meta">{progressLine}</p>
        </header>
      )}

      <section className="mockup-ticket__card mockup-ticket__body">
        <TestQuestionPanel
          ticket={ticket}
          questionIndex={questionIndex}
          selectedValue={selectedValue}
          onSelect={onSelect}
          disabled={completing}
        />
      </section>

      {completeError && <p className="auth-error mockup-ticket__error">{completeError}</p>}

      <footer className="mockup-ticket__actions">
        {canGoBack && (
          <button
            type="button"
            className="mockup-btn mockup-btn--outline mockup-ticket__btn"
            disabled={completing}
            onClick={goBack}
          >
            Назад
          </button>
        )}

        {!isLastQuestion && (
          <button
            type="button"
            className="mockup-btn mockup-btn--primary mockup-ticket__btn"
            disabled={!hasAnswer || completing}
            onClick={goNextQuestion}
          >
            Далее
          </button>
        )}

        {isEndOfTicket && (
          <button
            type="button"
            className="mockup-btn mockup-btn--primary mockup-ticket__btn"
            disabled={!hasAnswer || completing}
            onClick={goNextTicket}
          >
            Перейти к следующему билету
          </button>
        )}

        {(isEndOfTest || (isEndOfTicket && allowEarlyFinish)) && (
          <button
            type="button"
            className="mockup-btn mockup-btn--primary mockup-ticket__btn"
            disabled={!hasAnswer || completing}
            onClick={finish}
          >
            {completing ? "Отправка…" : finishLabel}
          </button>
        )}

        {showCancel && (
          <Link to={cancelHref} className="mockup-link mockup-ticket__cancel">
            Отмена
          </Link>
        )}
      </footer>
    </div>
  );
}
