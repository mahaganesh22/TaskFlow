import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";

import useUserWebSocket from "../hooks/useUserWebSocket";
import { useAuth } from "../context/AuthContext";
import { formatDetail } from "../api/client";
import { listMyJoinRequests, respondToJoinRequest } from "../api/members";
import { RequestCard } from "../pages/JoinRequestsPage";

export default function AppLayout() {
  const { user, logout, deleteAccount, getAccessToken, refreshAccessToken } = useAuth();
  const [liveTick, setLiveTick] = useState(0);
  const [liveNotice, setLiveNotice] = useState("");
  const [accountError, setAccountError] = useState("");
  const [deletingAccount, setDeletingAccount] = useState(false);
  const [joinRequests, setJoinRequests] = useState([]);
  const [selectedRequest, setSelectedRequest] = useState(null);
  const [requestError, setRequestError] = useState("");
  const [responding, setResponding] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    let active = true;
    listMyJoinRequests().then((items) => {
      if (!active) return;
      setJoinRequests(items);
      if (items.length) setSelectedRequest(items[0]);
    }).catch(() => {});
    return () => { active = false; };
  }, [user?.id]);

  async function refreshJoinRequests(openRequestId) {
    try {
      const items = await listMyJoinRequests();
      setJoinRequests(items);
      if (openRequestId) {
        setSelectedRequest(items.find((item) => item.id === openRequestId) || items[0] || null);
      }
    } catch {
      // The inbox page presents the detailed error if the request list cannot load.
    }
  }

  async function handleJoinRequestResponse(request, action) {
    setResponding(true);
    setRequestError("");
    try {
      await respondToJoinRequest(request.id, action);
      const remaining = joinRequests.filter((item) => item.id !== request.id);
      setJoinRequests(remaining);
      setSelectedRequest(remaining[0] || null);
      if (action === "ACCEPT") navigate(`/projects/${request.project_id}`);
    } catch (err) {
      setRequestError(formatDetail(err.detail) || "Could not respond to this request");
    } finally {
      setResponding(false);
    }
  }

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
      } else if (message.type === "PROJECT_JOIN_REQUESTED") {
        setLiveNotice("A project owner invited you to join their team");
        refreshJoinRequests(message.request_id);
      } else if (message.type === "PROJECT_JOIN_REQUEST_RESPONDED") {
        refreshJoinRequests();
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
          <NavLink to="/join-requests">Requests{joinRequests.length ? ` (${joinRequests.length})` : ""}</NavLink>
          <NavLink to="/profile">My profile</NavLink>
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
        <div className="live-banner" role="status">
          <span>{liveNotice}</span>
          <Link to="/join-requests" onClick={() => setLiveNotice("")}>View notifications</Link>
          <button type="button" onClick={() => setLiveNotice("")}>
            Dismiss
          </button>
        </div>
      )}

      <main className="app-main">
        <Outlet context={{ liveTick }} />
      </main>

      {selectedRequest && (
        <div className="modal-backdrop" role="presentation">
          <section className="modal join-request-modal" role="dialog" aria-modal="true" aria-labelledby="join-request-title">
            <div className="modal-header">
              <h2 id="join-request-title">Project invitation</h2>
              <button type="button" className="btn btn-ghost" onClick={() => setSelectedRequest(null)}>Close</button>
            </div>
            {requestError && <div className="alert" role="alert">{requestError}</div>}
            <RequestCard request={selectedRequest} busy={responding} onRespond={handleJoinRequestResponse} />
            {joinRequests.length > 1 && <button type="button" className="btn" onClick={() => setSelectedRequest(joinRequests[(joinRequests.findIndex((item) => item.id === selectedRequest.id) + 1) % joinRequests.length])}>Next request ({joinRequests.length - 1} more)</button>}
          </section>
        </div>
      )}
    </div>
  );
}
