import { useEffect, useState } from "react";

import { getProjectUserProfile } from "../api/users";
import { formatDetail } from "../api/client";

const SECTIONS = [
  ["education", "Education"],
  ["skills", "Skills"],
  ["projects", "Projects"],
  ["experience", "Experience"]
];

export default function UserProfileModal({ projectId, userId, onClose }) {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, []);

  useEffect(() => {
    let active = true;
    getProjectUserProfile(projectId, userId)
      .then((data) => { if (active) setProfile(data); })
      .catch((err) => { if (active) setError(formatDetail(err.detail) || "Could not load this profile"); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [projectId, userId]);

  return (
    <div className="modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}>
      <section className="modal user-profile-modal" role="dialog" aria-modal="true" aria-labelledby="user-profile-title">
        <div className="modal-header">
          <h2 id="user-profile-title">Member profile</h2>
          <button type="button" className="btn btn-ghost" onClick={onClose}>Close</button>
        </div>
        {loading && <div className="page-status">Loading profile…</div>}
        {error && <div className="alert" role="alert">{error}</div>}
        {profile && (
          <div className="profile-details">
            <div className="profile-identity">
              <h3>{profile.name}</h3>
              <p className="muted">{profile.email}</p>
            </div>
            {SECTIONS.map(([field, label]) => (
              <section className="profile-detail-section" key={field}>
                <h4>{label}</h4>
                <p>{profile[field] || "Not provided"}</p>
              </section>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
