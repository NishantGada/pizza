import { Navigate, Outlet } from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import { Spinner } from "./ui";

export default function ProtectedRoute() {
  const { token, initializing } = useAuth();
  if (!token) return <Navigate to="/login" replace />;
  if (initializing) return <Spinner />;
  return <Outlet />;
}
