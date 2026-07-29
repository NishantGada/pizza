import { Navigate, Route, Routes } from "react-router-dom";

import AppLayout from "./components/AppLayout";
import ProtectedRoute from "./components/ProtectedRoute";
import AuthPage from "./pages/AuthPage";
import CycleDetail from "./pages/CycleDetail";
import Dashboard from "./pages/Dashboard";
import Settings from "./pages/Settings";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<AuthPage mode="login" />} />
      <Route path="/register" element={<AuthPage mode="register" />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/cycles/:id" element={<CycleDetail />} />
          <Route path="/settings" element={<Settings />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
