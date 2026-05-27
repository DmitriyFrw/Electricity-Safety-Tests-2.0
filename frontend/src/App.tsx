import { Navigate, Route, Routes } from "react-router-dom";
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
import TestEditPage from "./pages/TestEditPage";
import TestNewPage from "./pages/TestNewPage";
import TrainingPage from "./pages/TrainingPage";

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <p className="dash-card-note">Загрузка…</p>;
  if (!user) return <Navigate to="/login" replace />;
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
          path="/exam/:testId"
          element={
            <PrivateRoute>
              <TakeExamPage />
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
          path="/tests/new"
          element={
            <PrivateRoute>
              <TestNewPage />
            </PrivateRoute>
          }
        />
        <Route
          path="/tests/:testId/edit"
          element={
            <PrivateRoute>
              <TestEditPage />
            </PrivateRoute>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  );
}
