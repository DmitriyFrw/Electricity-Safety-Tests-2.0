import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import { api } from "../api/client";
import { axiosErrorMessage } from "../api/getReact";
import RichHtml from "../components/RichHtml";
import TopNavLayout from "../layout/TopNavLayout";
import type { ExamResult, QuestionResult } from "../types/api";
import { labelsForCount, optionFieldsForQuestion } from "../utils/questionOptions";

export default function TrainingQuestionReviewPage() {
  const { testId, attemptId, questionId } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const stateResult = location.state?.result as ExamResult | undefined;
  const tid = Number(testId);
  const aid = Number(attemptId);
  const qid = Number(questionId);
  const isExam = location.pathname.includes("/exam/");
  const hasTrainingIds = Number.isFinite(tid) && Number.isFinite(aid);
  const resultPath = isExam
    ? `/exam/${testId}/result`
    : hasTrainingIds
      ? `/training/${tid}/result/${aid}`
      : `/training/${testId}/result`;

  const [result, setResult] = useState<ExamResult | undefined>(stateResult);
  const [loadError, setLoadError] = useState("");
  const [loading, setLoading] = useState(!stateResult && !isExam && hasTrainingIds);

  useEffect(() => {
    if (stateResult || isExam) {
      setResult(stateResult);
      setLoading(false);
      return;
    }
    if (!hasTrainingIds) {
      setLoading(false);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setLoadError("");
    void api
      .getTrainingResult(tid, aid)
      .then((data) => {
        if (!cancelled) setResult(data);
      })
      .catch((err) => {
        if (!cancelled) setLoadError(axiosErrorMessage(err));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [stateResult, isExam, hasTrainingIds, tid, aid]);

  if (loading) {
    return (
      <TopNavLayout active="results">
        <p className="dash-card-note">Загрузка…</p>
      </TopNavLayout>
    );
  }

  if (loadError) {
    return (
      <TopNavLayout active="results">
        <p className="auth-error">{loadError}</p>
        <Link to={resultPath}>К результатам</Link>
      </TopNavLayout>
    );
  }

  if (!result || !Number.isFinite(qid)) {
    return (
      <TopNavLayout active="results">
        <p className="dash-card-note">Нет данных для просмотра.</p>
        <Link to={resultPath}>К результатам</Link>
      </TopNavLayout>
    );
  }

  const question = result.question_results?.find((q) => q.question_id === qid);
  if (!question) {
    return (
      <TopNavLayout active="results">
        <p className="dash-card-note">Вопрос не найден.</p>
        <Link to={resultPath} state={{ result }}>
          К результатам
        </Link>
      </TopNavLayout>
    );
  }

  return (
    <TopNavLayout active="results">
      <button
        type="button"
        className="dash-link-btn test-review-back"
        onClick={() => navigate(resultPath, { state: { result } })}
      >
        ← К результатам
      </button>
      <QuestionReviewCard question={question} />
    </TopNavLayout>
  );
}

function questionCorrectIndices(question: QuestionResult): number[] {
  if (question.correct_indexes?.length) return question.correct_indexes;
  return [question.correct_index];
}

function questionSelectedIndices(question: QuestionResult): number[] {
  if (question.selected_indexes?.length) return question.selected_indexes;
  if (question.selected_index != null) return [question.selected_index];
  return [];
}

function QuestionReviewCard({ question }: { question: QuestionResult }) {
  const ticketTitle = question.ticket_title?.trim() || `Билет ${question.ticket_position}`;
  const fields = optionFieldsForQuestion(question, question.option_count);
  const labels = labelsForCount(question.option_count);
  const correctSet = new Set(questionCorrectIndices(question));
  const correctLabels = questionCorrectIndices(question)
    .map((i) => labels[i])
    .filter(Boolean)
    .join(", ");
  const selectedSet = new Set(questionSelectedIndices(question));
  const selectedLabels = questionSelectedIndices(question)
    .map((i) => labels[i])
    .filter(Boolean)
    .join(", ");

  return (
    <div className="dash-page-card test-question-card">
      <p className="test-flow-progress">
        {ticketTitle} · вопрос {question.question_position}
      </p>
      <p>
        <strong>Вопрос {question.question_position}.</strong>{" "}
        <RichHtml html={question.question_text} />
      </p>
      <div className="dash-radio-line">
        {fields.map(({ label, field }, i) => {
          const isCorrect = correctSet.has(i);
          const isSelected = selectedSet.has(i);
          let optionClass = "test-answer-option test-answer-option-neutral";
          if (isCorrect) optionClass = "test-answer-option test-answer-option-correct";
          else if (isSelected) optionClass = "test-answer-option test-answer-option-wrong";

          return (
            <div key={label} className={optionClass}>
              <RichHtml html={question[field]} />
            </div>
          );
        })}
      </div>
      <p className="dash-card-note" style={{ marginTop: "var(--spacing-3)" }}>
        Ваш ответ: {selectedLabels || "не выбран"}
        {" · "}
        Правильные: {correctLabels || "—"}
      </p>
    </div>
  );
}
