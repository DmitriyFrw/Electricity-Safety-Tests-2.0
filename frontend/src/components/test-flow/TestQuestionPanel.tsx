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
    <div className="mockup-ticket__question dash-no-copy">
      <p className="mockup-ticket__question-progress">
        Вопрос {questionIndex + 1} из {ticket.questions.length}
        {multipleChoice && !review ? " · выберите все верные варианты" : ""}
      </p>
      <div className="mockup-ticket__question-text">
        <p>
          <strong>Вопрос {q.position}.</strong> <RichHtml html={q.text} />
        </p>
      </div>
      <div className="mockup-ticket__answers" role={multipleChoice && !review ? "group" : undefined}>
        {fields.map(({ label, field }, i) => {
          const value = labels[i];
          const isSelected = review
            ? review.selectedIndices.includes(i)
            : selectedSet.has(value);
          const isCorrect = review ? review.correctIndices.includes(i) : false;
          let optionClass = "mockup-ticket__option";
          if (review) {
            if (isCorrect) optionClass += " mockup-ticket__option--correct";
            else if (isSelected) optionClass += " mockup-ticket__option--wrong";
            else optionClass += " mockup-ticket__option--neutral";
          } else if (isSelected) {
            optionClass += " mockup-ticket__option--selected";
          }

          if (review) {
            return (
              <div key={label} className={optionClass}>
                <RichHtml html={q[field]} />
              </div>
            );
          }

          if (multipleChoice) {
            return (
              <label key={label} className={optionClass}>
                <input
                  type="checkbox"
                  className="mockup-ticket__option-input"
                  name={`q_${q.id}_${value}`}
                  value={value}
                  checked={selectedSet.has(value)}
                  disabled={disabled}
                  onChange={() => onSelect(q.id, toggleSelectedValue(selectedValue, value))}
                />
                <span className="mockup-ticket__option-text">
                  <RichHtml html={q[field]} />
                </span>
              </label>
            );
          }

          return (
            <label key={label} className={optionClass}>
              <input
                type="radio"
                className="mockup-ticket__option-input"
                name={`q_${q.id}`}
                value={value}
                checked={selectedValue === value}
                disabled={disabled}
                onChange={() => onSelect(q.id, value)}
              />
              <span className="mockup-ticket__option-text">
                <RichHtml html={q[field]} />
              </span>
            </label>
          );
        })}
      </div>
    </div>
  );
}

export { hasSelectedValue };
