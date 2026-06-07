import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { getReact, postReact, axiosErrorMessage } from "../api/getReact";
import PaginatedTestFlow, { type AnswersMap } from "../components/test-flow/PaginatedTestFlow";
import DashboardLayout from "../layout/DashboardLayout";
import type { ExamResult, ExamSession, ExamTicketPaper } from "../types/api";

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export default function TakeExamPage() {
  const { testId } = useParams();
  const navigate = useNavigate();
  const id = Number(testId);
  const [session, setSession] = useState<ExamSession | null>(null);
  const [paper, setPaper] = useState<ExamTicketPaper | null>(null);
  const [secondsLeft, setSecondsLeft] = useState(0);
  const [loadError, setLoadError] = useState("");
  const [submitError, setSubmitError] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const expiredRef = useRef(false);

  const finishExam = useCallback(async () => {
    const result = await postReact<ExamResult>(`/tests/${id}/exam/finish`);
    navigate(`/exam/${id}/result`, { state: { result } });
  }, [id, navigate]);

  const loadTicket = useCallback(
    async (ticketId: number) => {
      const ticketPaper = await getReact<ExamTicketPaper>(`/tests/${id}/exam/tickets/${ticketId}`);
      setPaper(ticketPaper);
      setSecondsLeft(ticketPaper.seconds_remaining);
      expiredRef.current = false;
    },
    [id]
  );

  const advanceSession = useCallback(
    async (next: ExamSession) => {
      setSession(next);
      if (next.next_ticket_id) {
        await loadTicket(next.next_ticket_id);
      } else {
        await finishExam();
      }
    },
    [finishExam, loadTicket]
  );

  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    (async () => {
      setLoading(true);
      setLoadError("");
      try {
        let sess: ExamSession;
        try {
          sess = await getReact<ExamSession>(`/tests/${id}/exam/session`);
        } catch {
          sess = await postReact<ExamSession>(`/tests/${id}/exam/session`);
        }
        if (cancelled) return;
        setSession(sess);
        if (sess.next_ticket_id) {
          await loadTicket(sess.next_ticket_id);
        } else {
          await finishExam();
        }
      } catch (err) {
        if (!cancelled) setLoadError(axiosErrorMessage(err));
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [id, finishExam, loadTicket]);

  useEffect(() => {
    if (!paper || secondsLeft <= 0) return;
    const t = window.setInterval(() => {
      setSecondsLeft((s) => Math.max(0, s - 1));
    }, 1000);
    return () => window.clearInterval(t);
  }, [paper?.ticket.id, paper?.seconds_remaining]);

  const submitCurrentTicket = useCallback(
    async (answers: AnswersMap) => {
      if (!paper || !session) return;
      setSubmitting(true);
      setSubmitError("");
      const payload = Object.entries(answers).map(([question_id, value]) => ({
        question_id: Number(question_id),
        value,
      }));
      try {
        const next = await postReact<ExamSession>(
          `/tests/${id}/exam/tickets/${paper.ticket.id}`,
          { answers: payload }
        );
        await advanceSession(next);
      } catch (err) {
        const msg = axiosErrorMessage(err);
        setSubmitError(msg);
        if (msg.includes("истекло")) {
          try {
            const refreshed = await getReact<ExamSession>(`/tests/${id}/exam/session`);
            await advanceSession(refreshed);
          } catch {
            /* ignore */
          }
        }
      } finally {
        setSubmitting(false);
      }
    },
    [advanceSession, id, paper, session]
  );

  useEffect(() => {
    if (!paper || secondsLeft > 0 || expiredRef.current) return;
    expiredRef.current = true;
    void submitCurrentTicket({});
  }, [paper, secondsLeft, submitCurrentTicket]);

  if (loadError && !paper) {
    return (
      <DashboardLayout active="exam">
        <p className="auth-error">{loadError}</p>
        <Link to="/exam">← К экзамену</Link>
      </DashboardLayout>
    );
  }

  if (loading || !paper || !session) {
    return (
      <DashboardLayout active="exam">
        <p className="dash-card-note">Загрузка…</p>
      </DashboardLayout>
    );
  }

  const timedOut = secondsLeft <= 0;
  const finishLabel = "Завершить экзамен";

  return (
    <DashboardLayout active="exam">
      <div className="dash-page-card test-flow-header">
        <h1>{paper.test_title}</h1>
        <p className={`dash-exam-timer ${secondsLeft <= 60 ? "dash-exam-timer-warn" : ""}`}>
          Осталось: {formatTime(secondsLeft)}
        </p>
        <p className="dash-card-note">
          Билет {paper.ticket_index} из {paper.ticket_count} · лимит {paper.time_limit_seconds / 60} мин
        </p>
      </div>
      <PaginatedTestFlow
        key={paper.ticket.id}
        tickets={[paper.ticket]}
        testTitle=""
        cancelHref="/exam"
        onComplete={submitCurrentTicket}
        completing={submitting || timedOut}
        completeError={submitError}
        finishLabel={finishLabel}
        allowEarlyFinish={false}
      />
    </DashboardLayout>
  );
}
