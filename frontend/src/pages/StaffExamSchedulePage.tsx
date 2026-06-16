import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "../api/client";
import { axiosErrorMessage } from "../api/getReact";
import TopNavLayout from "../layout/TopNavLayout";
import type { ExamScheduleRow } from "../types/api";

const NOT_TAKEN = "не проходил экзамен";

type PlannedDateSort = "asc" | "desc" | null;

function parsePlannedDate(value: string): number | null {
  if (!value || value === NOT_TAKEN) return null;
  const match = /^(\d{2})\.(\d{2})\.(\d{4})$/.exec(value);
  if (!match) return null;
  const [, day, month, year] = match;
  return new Date(Number(year), Number(month) - 1, Number(day)).getTime();
}

function comparePlannedDates(a: ExamScheduleRow, b: ExamScheduleRow, direction: "asc" | "desc") {
  const ta = parsePlannedDate(a.next_exam_date);
  const tb = parsePlannedDate(b.next_exam_date);
  if (ta === null && tb === null) return 0;
  if (ta === null) return 1;
  if (tb === null) return -1;
  return direction === "asc" ? ta - tb : tb - ta;
}

function gradeClass(grade: string): string {
  if (grade === NOT_TAKEN) return "mockup-muted";
  if (grade === "отлично") return "grade-excellent";
  if (grade === "хорошо") return "grade-good";
  if (grade === "удовлетворительно") return "grade-satisfactory";
  return "";
}

export default function StaffExamSchedulePage() {
  const [rows, setRows] = useState<ExamScheduleRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState("");
  const [exportError, setExportError] = useState("");
  const [plannedDateSort, setPlannedDateSort] = useState<PlannedDateSort>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await api.listExamSchedule();
      setRows(data);
    } catch (err) {
      setError(axiosErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const sortedRows = useMemo(() => {
    if (!plannedDateSort) return rows;
    return [...rows].sort((a, b) => comparePlannedDates(a, b, plannedDateSort));
  }, [rows, plannedDateSort]);

  const onPlannedDateSort = () => {
    setPlannedDateSort((current) => {
      if (current === null) return "asc";
      if (current === "asc") return "desc";
      return null;
    });
  };

  const onDownload = async () => {
    setExporting(true);
    setExportError("");
    try {
      await api.downloadExamScheduleExport();
    } catch (err) {
      setExportError(axiosErrorMessage(err));
    } finally {
      setExporting(false);
    }
  };

  return (
    <TopNavLayout>
      <header className="mockup-page-header">
        <h1>График сдачи экзаменов</h1>
        <p>
          Таблица по всем пользователям портала: ФИО, дата рождения, должность,
          бизнес-юнит, группа по ЭБ, роль, последняя и планируемая дата сдачи экзамена, оценка.
        </p>
      </header>

      <div className="mockup-page-card" style={{ marginBottom: 20 }}>
        <p className="mockup-muted" style={{ marginBottom: 16 }}>
          Если пользователь не сдавал экзамен, в таблице будет указано «не проходил экзамен».
          Оценка выводится в формате: удовлетворительно, хорошо, отлично.
        </p>
        {exportError && <p className="auth-error">{exportError}</p>}
        <button
          type="button"
          className="mockup-btn mockup-btn--primary"
          disabled={exporting}
          onClick={() => void onDownload()}
        >
          {exporting ? "Формирование файла…" : "Скачать Excel"}
        </button>
      </div>

      {error && <p className="auth-error">{error}</p>}

      {loading ? (
        <p className="mockup-muted">Загрузка…</p>
      ) : rows.length === 0 ? (
        <div className="mockup-page-card">
          <p className="mockup-muted">Пользователей пока нет.</p>
        </div>
      ) : (
        <div className="results-table-wrap">
          <table className="results-table staff-table exam-schedule-table">
            <thead>
              <tr>
                <th>ФИО</th>
                <th>Дата рождения</th>
                <th>Должность</th>
                <th>Бизнес-юнит</th>
                <th>Группа по ЭБ</th>
                <th>Роль</th>
                <th>Последняя дата сдачи</th>
                <th>
                  <button
                    type="button"
                    className={`results-table__sort${
                      plannedDateSort ? " results-table__sort--active" : ""
                    }`}
                    onClick={onPlannedDateSort}
                    aria-sort={
                      plannedDateSort === "asc"
                        ? "ascending"
                        : plannedDateSort === "desc"
                          ? "descending"
                          : "none"
                    }
                  >
                    Планируемая дата
                    {plannedDateSort === "asc" && <span aria-hidden> ↑</span>}
                    {plannedDateSort === "desc" && <span aria-hidden> ↓</span>}
                  </button>
                </th>
                <th>Оценка</th>
              </tr>
            </thead>
            <tbody>
              {sortedRows.map((row, index) => {
                const notTaken = row.exam_grade === NOT_TAKEN;
                return (
                  <tr key={`${row.full_name}-${index}`}>
                    <td>{row.full_name}</td>
                    <td>{row.birth_date || "—"}</td>
                    <td>{row.job_title || "—"}</td>
                    <td>{row.business_unit || "—"}</td>
                    <td>{row.safety_group || "—"}</td>
                    <td>{row.role_label}</td>
                    <td className={notTaken ? "mockup-muted" : undefined}>{row.last_exam_date}</td>
                    <td className={notTaken ? "mockup-muted" : undefined}>{row.next_exam_date}</td>
                    <td className={gradeClass(row.exam_grade)}>{row.exam_grade}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </TopNavLayout>
  );
}
