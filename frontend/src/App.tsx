import { Navigate, Route, Routes, useParams } from "react-router-dom";
import { AuthProvider, useAuth } from "./auth/AuthContext";
import CabinetPage from "./pages/CabinetPage";
import ExamPage from "./pages/ExamPage";
import ExamResultPage from "./pages/ExamResultPage";
import HomePage from "./pages/HomePage";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import TakeExamPage from "./pages/TakeExamPage";
import TakeTrainingPage from "./pages/TakeTrainingPage";
import TrainingResultPage from "./pages/TrainingResultPage";
import TrainingQuestionReviewPage from "./pages/TrainingQuestionReviewPage";
import ManualsPage from "./pages/ManualsPage";
import TestNewPage from "./pages/TestNewPage";
import TrainingPage from "./pages/TrainingPage";
import AdminUsersPage from "./pages/AdminUsersPage";
import KotSafetyGroupsPage from "./pages/KotSafetyGroupsPage";
import TicketConstructorPage from "./pages/TicketConstructorPage";
import WikiPage from "./pages/WikiPage";

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <p className="dash-card-note">Загрузка…</p>;
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function AdminRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <p className="dash-card-note">Загрузка…</p>;
  if (!user) return <Navigate to="/login" replace />;
  if (user.role !== "admin") return <Navigate to="/cabinet" replace />;
  return <>{children}</>;
}

function RedirectTestEditToConstructor() {
  const { testId } = useParams();
  return <Navigate to={`/constructor/${testId ?? ""}`} replace />;
}

function StaffRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <p className="dash-card-note">Загрузка…</p>;
  if (!user) return <Navigate to="/login" replace />;
  if (user.role !== "admin" && user.role !== "ezh") return <Navigate to="/cabinet" replace />;
  return <>{children}</>;
}

function EditorRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <p className="dash-card-note">Загрузка…</p>;
  if (!user) return <Navigate to="/login" replace />;
  if (!user.can_create_tests) return <Navigate to="/cabinet" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route
          path="/cabinet"
          element={
            <PrivateRoute>
              <CabinetPage />
            </PrivateRoute>
          }
        />
        <Route
          path="/wiki"
          element={
            <PrivateRoute>
              <WikiPage />
            </PrivateRoute>
          }
        />
        <Route
          path="/manuals"
          element={
            <PrivateRoute>
              <ManualsPage />
            </PrivateRoute>
          }
        />
        <Route
          path="/training"
          element={
            <PrivateRoute>
              <TrainingPage />
            </PrivateRoute>
          }
        />
        <Route
          path="/exam"
          element={
            <PrivateRoute>
              <ExamPage />
            </PrivateRoute>
          }
        />
        <Route
          path="/training/:testId"
          element={
            <PrivateRoute>
              <TakeTrainingPage />
            </PrivateRoute>
          }
        />
        <Route
          path="/training/:testId/result"
          element={
            <PrivateRoute>
              <TrainingResultPage />
            </PrivateRoute>
          }
        />
        <Route
          path="/training/:testId/result/q/:questionId"
          element={
            <PrivateRoute>
              <TrainingQuestionReviewPage />
            </PrivateRoute>
          }
        />
        <Route
          path="/exam/:testId"
          element={
            <PrivateRoute>
              <TakeExamPage />
            </PrivateRoute>
          }
        />
        <Route
          path="/exam/:testId/result/:attemptId"
          element={
            <PrivateRoute>
              <ExamResultPage />
            </PrivateRoute>
          }
        />
        <Route
          path="/exam/:testId/result"
          element={
            <PrivateRoute>
              <ExamResultPage />
            </PrivateRoute>
          }
        />
        <Route
          path="/exam/:testId/result/q/:questionId"
          element={
            <PrivateRoute>
              <TrainingQuestionReviewPage />
            </PrivateRoute>
          }
        />
        <Route
          path="/admin/users"
          element={
            <AdminRoute>
              <AdminUsersPage />
            </AdminRoute>
          }
        />
        <Route
          path="/staff/safety-groups"
          element={
            <StaffRoute>
              <KotSafetyGroupsPage />
            </StaffRoute>
          }
        />
        <Route
          path="/constructor"
          element={
            <EditorRoute>
              <TicketConstructorPage />
            </EditorRoute>
          }
        />
        <Route
          path="/constructor/:testId"
          element={
            <EditorRoute>
              <TicketConstructorPage />
            </EditorRoute>
          }
        />
        <Route
          path="/constructor/:testId/tickets/:ticketId"
          element={
            <EditorRoute>
              <TicketConstructorPage />
            </EditorRoute>
          }
        />
        <Route
          path="/tests/new"
          element={
            <EditorRoute>
              <TestNewPage />
            </EditorRoute>
          }
        />
        <Route
          path="/tests/:testId/edit"
          element={
            <EditorRoute>
              <RedirectTestEditToConstructor />
            </EditorRoute>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  );
}
