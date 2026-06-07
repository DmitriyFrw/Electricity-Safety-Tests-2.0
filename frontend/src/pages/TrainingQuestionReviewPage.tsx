import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import RichHtml from "../components/RichHtml";
import DashboardLayout from "../layout/DashboardLayout";
import type { ExamResult, QuestionResult } from "../types/api";
import { labelsForCount, optionFieldsForQuestion } from "../utils/questionOptions";

export default function TrainingQuestionReviewPage() {
  const { testId, questionId } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const result = location.state?.result as ExamResult | undefined;
  const qid = Number(questionId);
  const isExam = location.pathname.includes("/exam/");
  const active = isExam ? "exam" : "training";
  const resultPath = isExam ? `/exam/${testId}/result` : `/training/${testId}/result`;

  if (!result || !Number.isFinite(qid)) {
    return (
      <DashboardLayout active={active}>
        <p className="dash-card-note">Нет данных для просмотра.</p>
        <Link to={resultPath}>К результатам</Link>
      </DashboardLayout>
    );
  }

  const question = result.question_results?.find((q) => q.question_id === qid);
  if (!question) {
    return (
      <DashboardLayout active={active}>
        <p className="dash-card-note">Вопрос не найден.</p>
        <Link to={resultPath} state={{ result }}>
          К результатам
        </Link>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout active={active}>
      <button
        type="button"
        className="dash-link-btn test-review-back"
        onClick={() => navigate(resultPath, { state: { result } })}
      >
        ← К результатам
      </button>
      <QuestionReviewCard question={question} />
    </DashboardLayout>
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
              <span>
                {label} — <RichHtml html={question[field]} />
              </span>
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
