import { Navigate, Route, Routes } from "react-router-dom";
import type { ReactElement } from "react";
import { Layout } from "./components/Layout";
import { useAuth } from "./auth/AuthContext";
import { AdminExamBuilderPage } from "./pages/AdminExamBuilderPage";
import { AuthPage } from "./pages/AuthPage";
import { CandidateExamsPage } from "./pages/CandidateExamsPage";
import { ExamAttemptPage } from "./pages/ExamAttemptPage";
import { ReviewListPage } from "./pages/ReviewListPage";
import { ReviewTimelinePage } from "./pages/ReviewTimelinePage";

const adminRoles = new Set(["admin", "instructor", "reviewer"]);

function RequireAuth({ children }: { children: ReactElement }) {
  const { token } = useAuth();
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

function RequireAdmin({ children }: { children: ReactElement }) {
  const { user } = useAuth();
  if (!user || !adminRoles.has(user.role)) {
    return <Navigate to="/candidate/exams" replace />;
  }
  return children;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<AuthPage mode="login" />} />
      <Route path="/signup" element={<AuthPage mode="signup" />} />
      <Route
        path="/"
        element={
          <RequireAuth>
            <Layout />
          </RequireAuth>
        }
      >
        <Route index element={<Navigate to="/candidate/exams" replace />} />
        <Route path="candidate/exams" element={<CandidateExamsPage />} />
        <Route path="candidate/attempts/:attemptId" element={<ExamAttemptPage />} />
        <Route
          path="admin/exams/new"
          element={
            <RequireAdmin>
              <AdminExamBuilderPage />
            </RequireAdmin>
          }
        />
        <Route
          path="admin/review"
          element={
            <RequireAdmin>
              <ReviewListPage />
            </RequireAdmin>
          }
        />
        <Route
          path="admin/review/:attemptId"
          element={
            <RequireAdmin>
              <ReviewTimelinePage />
            </RequireAdmin>
          }
        />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
