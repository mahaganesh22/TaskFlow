import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function GuestRoute({ children }) {
  const { user, ready } = useAuth();

  if (!ready) {
    return <div className="page-status">Loading session…</div>;
  }

  if (user) {
    return <Navigate to="/" replace />;
  }

  return children;
}
