import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../api/client";
import { axiosErrorCode, axiosErrorMessage, getReact, postReact } from "../api/getReact";
import PaginatedTestFlow, { type AnswersMap } from "../components/test-flow/PaginatedTestFlow";
import TopNavLayout from "../layout/TopNavLayout";
import type { ExamResult, ExamSession, ExamTicketPaper } from "../types/api";
import {
  abandonExamKeepalive,
  clearExamPageGuard,
  isExamPageRefresh,
  markExamPageActive,
} from "../utils/examSession";

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
  const intentionalLeaveRef = useRef(false);
  const abandonSentRef = useRef(false);

  const goToResult = useCallback(
    (result: ExamResult) => {
      intentionalLeaveRef.current = true;
      clearExamPageGuard(id);
      navigate(`/exam/${id}/result/${result.attempt_id}`, { state: { result } });
    },
    [id, navigate]
  );

  const requestAbandon = useCallback(() => {
    if (!id || abandonSentRef.current || intentionalLeaveRef.current) return;
    abandonSentRef.current = true;
    abandonExamKeepalive(id);
  }, [id]);

  const finishExam = useCallback(async () => {
    const result = await postReact<ExamResult>(`/tests/${id}/exam/finish`);
    goToResult(result);
  }, [goToResult, id]);

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

    const onPageHide = () => requestAbandon();
    window.addEventListener("pagehide", onPageHide);

    return () => {
      window.removeEventListener("pagehide", onPageHide);
      if (!intentionalLeaveRef.current) {
        requestAbandon();
      }
      if (intentionalLeaveRef.current) {
        clearExamPageGuard(id);
      }
    };
  }, [id, requestAbandon]);

  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    (async () => {
      setLoading(true);
      setLoadError("");
      try {
        if (isExamPageRefresh(id)) {
          try {
            const result = await api.abandonExam(id);
            if (cancelled) return;
            goToResult(result);
          } catch {
            if (!cancelled) {
              intentionalLeaveRef.current = true;
              clearExamPageGuard(id);
              navigate("/exam", { replace: true });
            }
          }
          return;
        }

        markExamPageActive(id);
        const sess = await postReact<ExamSession>(`/tests/${id}/exam/session`);
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
  }, [id, finishExam, goToResult, loadTicket]);

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
        if (axiosErrorCode(err) === "exam_ticket_time_expired") {
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
      <TopNavLayout active="exam">
        <p className="auth-error">{loadError}</p>
        <Link to="/exam" className="mockup-link">
          ← К экзамену
        </Link>
      </TopNavLayout>
    );
  }

  if (loading || !paper || !session) {
    return (
      <TopNavLayout active="exam">
        <p className="mockup-page-header p">Загрузка…</p>
      </TopNavLayout>
    );
  }

  const timedOut = secondsLeft <= 0;
  const finishLabel = "Завершить экзамен";

  return (
    <TopNavLayout active="exam">
      <PaginatedTestFlow
        key={paper.ticket.id}
        tickets={[paper.ticket]}
        testTitle={paper.test_title}
        timerText={`Осталось: ${formatTime(secondsLeft)}`}
        timerWarn={secondsLeft <= 60}
        ticketMeta={`Билет ${paper.ticket_index} из ${paper.ticket_count} · лимит ${paper.time_limit_seconds / 60} мин`}
        cancelHref="/exam"
        onComplete={submitCurrentTicket}
        completing={submitting || timedOut}
        completeError={submitError}
        finishLabel={finishLabel}
        allowEarlyFinish={false}
        showCancel={false}
      />
    </TopNavLayout>
  );
}
