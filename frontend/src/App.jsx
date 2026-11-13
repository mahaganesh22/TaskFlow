import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { AuthProvider } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import GuestRoute from "./components/GuestRoute";
import AppLayout from "./components/AppLayout";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import DashboardPage from "./pages/DashboardPage";
import AssignedPage from "./pages/AssignedPage";
import ProjectPage from "./pages/ProjectPage";
import CreateTaskPage from "./pages/CreateTaskPage";
import JoinRequestsPage from "./pages/JoinRequestsPage";
import ProfilePage from "./pages/ProfilePage";
import CreateProjectPage from "./pages/CreateProjectPage";

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route
            path="/login"
            element={
              <GuestRoute>
                <LoginPage />
              </GuestRoute>
            }
          />
          <Route
            path="/register"
            element={
              <GuestRoute>
                <RegisterPage />
              </GuestRoute>
            }
          />
          <Route
            element={
              <ProtectedRoute>
                <AppLayout />
              </ProtectedRoute>
            }
          >
            <Route path="/" element={<DashboardPage />} />
            <Route path="/assigned" element={<AssignedPage />} />
            <Route path="/join-requests" element={<JoinRequestsPage />} />
            <Route path="/profile" element={<ProfilePage />} />
            <Route path="/projects/new" element={<CreateProjectPage />} />
            <Route path="/projects/:projectId/tasks/new" element={<CreateTaskPage />} />
            <Route path="/projects/:projectId" element={<ProjectPage />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
