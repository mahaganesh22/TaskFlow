import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { listMyJoinRequests, respondToJoinRequest } from "../api/members";
import { formatDetail } from "../api/client";

export default function JoinRequestsPage() {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState("");
  const [error, setError] = useState("");

  async function loadRequests() {
    setLoading(true);
    try {
      setRequests(await listMyJoinRequests());
      setError("");
    } catch (err) {
      setError(formatDetail(err.detail) || "Could not load project requests");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { loadRequests(); }, []);

  async function respond(request, action) {
    setBusyId(request.id);
    setError("");
    try {
      await respondToJoinRequest(request.id, action);
      setRequests((current) => current.filter((item) => item.id !== request.id));
    } catch (err) {
      setError(formatDetail(err.detail) || "Could not respond to this request");
    } finally {
      setBusyId("");
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <div><p className="eyebrow">Team invitations</p><h1>Project requests</h1><p className="muted">Review requests from project owners to join their teams.</p></div>
      </div>
      {error && <div className="alert" role="alert">{error}</div>}
      {loading ? <div className="page-status">Loading requests…</div> : requests.length === 0 ? (
        <section className="panel"><p className="muted">You have no pending project requests.</p></section>
      ) : requests.map((request) => (
        <RequestCard key={request.id} request={request} busy={busyId === request.id} onRespond={respond} />
      ))}
    </div>
  );
}

export function RequestCard({ request, busy, onRespond }) {
  const { project } = request;
  return (
    <section className="panel join-request-card">
      <div>
        <p className="eyebrow">Project invitation</p>
        <h2>{project.name}</h2>
        <p>{project.description || "No project description was provided."}</p>
        <p className="muted">Requested by {project.owner.name} ({project.owner.email})</p>
        <p className="muted">Sent {new Date(request.created_at).toLocaleString()}</p>
      </div>
      <div className="form-actions">
        <button className="btn" type="button" disabled={busy} onClick={() => onRespond(request, "REJECT")}>{busy ? "Saving…" : "Reject"}</button>
        <button className="btn btn-primary" type="button" disabled={busy} onClick={() => onRespond(request, "ACCEPT")}>{busy ? "Saving…" : "Accept request"}</button>
      </div>
    </section>
  );
}
