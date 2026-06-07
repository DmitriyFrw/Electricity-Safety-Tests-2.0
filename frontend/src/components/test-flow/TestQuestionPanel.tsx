import RichHtml from "../RichHtml";
import type { TicketExam } from "../../types/api";
import {
  hasSelectedValue,
  labelsForCount,
  optionFieldsForQuestion,
  parseSelectedValue,
  toggleSelectedValue,
} from "../../utils/questionOptions";

type Props = {
  ticket: TicketExam;
  questionIndex: number;
  selectedValue: string | undefined;
  onSelect: (questionId: number, value: string) => void;
  disabled?: boolean;
  review?: {
    correctIndices: number[];
    selectedIndices: number[];
  };
};

export default function TestQuestionPanel({
  ticket,
  questionIndex,
  selectedValue,
  onSelect,
  disabled = false,
  review,
}: Props) {
  const q = ticket.questions[questionIndex];
  if (!q) return null;

  const fields = optionFieldsForQuestion(q, ticket.option_count);
  const labels = labelsForCount(q.option_count ?? ticket.option_count);
  const multipleChoice = Boolean(q.multiple_choice);
  const selectedSet = new Set(parseSelectedValue(selectedValue));

  return (
    <div className="test-question-card dash-no-copy test-flow-question-card">
      <p className="test-flow-progress">
        Вопрос {questionIndex + 1} из {ticket.questions.length}
        {multipleChoice && !review ? " · выберите все верные варианты" : ""}
      </p>
      <div className="dash-question">
        <p>
          <strong>Вопрос {q.position}.</strong> <RichHtml html={q.text} />
        </p>
        <div className="dash-radio-line">
          {fields.map(({ label, field }, i) => {
            const value = labels[i];
            const isSelected = review
              ? review.selectedIndices.includes(i)
              : selectedSet.has(value);
            const isCorrect = review ? review.correctIndices.includes(i) : false;
            let optionClass = "test-answer-option";
            if (review) {
              if (isCorrect) optionClass += " test-answer-option-correct";
              else if (isSelected) optionClass += " test-answer-option-wrong";
              else optionClass += " test-answer-option-neutral";
            }

            if (review) {
              return (
                <div key={label} className={optionClass}>
                  <span>
                    {label} — <RichHtml html={q[field]} />
                  </span>
                </div>
              );
            }

            if (multipleChoice) {
              return (
                <label key={label} className="test-answer-checkbox">
                  <input
                    type="checkbox"
                    name={`q_${q.id}_${value}`}
                    value={value}
                    checked={selectedSet.has(value)}
                    disabled={disabled}
                    onChange={() => onSelect(q.id, toggleSelectedValue(selectedValue, value))}
                  />
                  {label} — <RichHtml html={q[field]} />
                </label>
              );
            }

            return (
              <label key={label}>
                <input
                  type="radio"
                  name={`q_${q.id}`}
                  value={value}
                  checked={selectedValue === value}
                  disabled={disabled}
                  onChange={() => onSelect(q.id, value)}
                />
                {label} — <RichHtml html={q[field]} />
              </label>
            );
          })}
        </div>
      </div>
    </div>
  );
}

export { hasSelectedValue };
