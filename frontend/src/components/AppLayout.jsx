import { NavLink, Outlet } from "react-router-dom";
import { useState } from "react";

import useUserWebSocket from "../hooks/useUserWebSocket";
import { useAuth } from "../context/AuthContext";
import { formatDetail } from "../api/client";

export default function AppLayout() {
  const { user, logout, deleteAccount, getAccessToken, refreshAccessToken } = useAuth();
  const [liveTick, setLiveTick] = useState(0);
  const [liveNotice, setLiveNotice] = useState("");
  const [accountError, setAccountError] = useState("");
  const [deletingAccount, setDeletingAccount] = useState(false);

  async function handleDeleteAccount() {
    const confirmed = window.confirm(
      "Delete your TaskFlow account? You will be signed out immediately. If you own projects, transfer ownership or delete them first."
    );
    if (!confirmed) return;

    setAccountError("");
    setDeletingAccount(true);
    try {
      await deleteAccount();
    } catch (error) {
      setAccountError(formatDetail(error.detail) || "Could not delete your account.");
      setDeletingAccount(false);
    }
  }

  const { status } = useUserWebSocket({
    enabled: Boolean(user),
    getAccessToken,
    refreshAccessToken,
    onEvent: (message) => {
      setLiveTick((value) => value + 1);

      if (message.type === "ASSIGNED_TASKS_CHANGED") {
        setLiveNotice("Assigned to me was updated");
      } else if (message.type === "MEMBER_INVITED") {
        setLiveNotice("You were added to a project");
      } else if (message.type === "MEMBER_REMOVED") {
        setLiveNotice("A project membership changed");
      }
    }
  });

  return (
    <div className="app-shell">
      <header className="topbar">
        <NavLink to="/" className="brand">
          TaskFlow
        </NavLink>

        <nav className="top-nav">
          <NavLink to="/" end>
            Dashboard
          </NavLink>
          <NavLink to="/assigned">Assigned to me</NavLink>
        </nav>

        <div className="topbar-user">
          <span className={`ws-dot ${status}`} title={`Personal socket: ${status}`} />
          <span className="user-name">{user?.name}</span>
          <button
            type="button"
            className="btn btn-danger"
            onClick={handleDeleteAccount}
            disabled={deletingAccount}
          >
            {deletingAccount ? "Deleting…" : "Delete account"}
          </button>
          <button type="button" className="btn btn-ghost" onClick={logout}>
            Log out
          </button>
        </div>
      </header>

      {accountError && (
        <div className="live-banner" role="alert">
          {accountError}
          <button type="button" onClick={() => setAccountError("")}>
            Dismiss
          </button>
        </div>
      )}

      {liveNotice && (
        <div className="live-banner">
          {liveNotice}
          <button type="button" onClick={() => setLiveNotice("")}>
            Dismiss
          </button>
        </div>
      )}

      <main className="app-main">
        <Outlet context={{ liveTick }} />
      </main>
    </div>
  );
}
