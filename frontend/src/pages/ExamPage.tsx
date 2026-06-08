import { Link } from "react-router-dom";
import DashboardLayout from "../layout/DashboardLayout";
import {
  examErrorsAllowanceText,
  examPassThresholdText,
  examTimeLimitText,
} from "../content/examRules";
import { useGetReact } from "../hooks/useGetReact";
import type { TestListItem } from "../types/api";

export default function ExamPage() {
  const { data, error, loading } = useGetReact<{ items: TestListItem[] }>("/tests");
  const tests = data?.items ?? [];
  const firstReady = tests.find((t) => t.ready);

  return (
    <DashboardLayout active="exam">
      <div className="exam-intro-page">
        <div className="exam-intro-card">
          <h1>Экзамен</h1>
          <div className="exam-intro-text">
            <p>
              Экзамен сдается в присутствии контролирующего лица. На прохождение экзамена —{" "}
              {examTimeLimitText()}. Для успешной сдачи экзамена необходимо набрать{" "}
              {examPassThresholdText()}. У вас есть {examErrorsAllowanceText()}.
            </p>
            <p>
              Экзамен завершается при сдаче билета, истечении времени на билет, а также при
              обновлении или закрытии страницы — в этих случаях попытка считается не сданной.
            </p>
            <p>Не спешите и у вас все получится.</p>
            <p>Ежекот желает вам удачи!</p>
          </div>
          <img
            src="/razvivaisia/assets/images/ezhkot-exam.png"
            alt="Ежекот"
            className="exam-intro-mascot"
            width={200}
            height={200}
          />
          {error && <p className="auth-error">{error}</p>}
          {loading && <p className="dash-card-note">Загрузка…</p>}
          {!loading && firstReady && (
            <Link to={`/exam/${firstReady.id}`} className="btn btn-primary btn-lg exam-intro-btn">
              Поехали!
            </Link>
          )}
          {!loading && !error && !firstReady && (
            <p className="dash-card-note">Нет доступных тестов для экзамена.</p>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}
