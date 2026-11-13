import { useEffect, useState } from "react";

import { getMyProfile, updateMyProfile } from "../api/users";
import { formatDetail } from "../api/client";

const FIELDS = [
  ["education", "Education", "Degree, school, or relevant coursework"],
  ["skills", "Skills", "Languages, tools, and areas of expertise"],
  ["projects", "Projects", "Projects you have worked on"],
  ["experience", "Experience", "Relevant work, volunteer, or team experience"]
];

export default function ProfilePage() {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    getMyProfile()
      .then(setProfile)
      .catch((err) => setError(formatDetail(err.detail) || "Could not load your profile"))
      .finally(() => setLoading(false));
  }, []);

  function updateField(field, value) {
    setProfile((current) => ({ ...current, [field]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setSaving(true);
    setError("");
    setSuccess("");
    try {
      const updated = await updateMyProfile(Object.fromEntries(
        FIELDS.map(([key]) => [key, profile[key]?.trim() || null])
      ));
      setProfile(updated);
      setSuccess("Your profile has been saved.");
    } catch (err) {
      setError(formatDetail(err.detail) || "Could not save your profile");
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <div className="page-status">Loading profile…</div>;
  if (!profile) return <div className="page-status error">{error || "Profile unavailable"}</div>;

  return (
    <div className="page">
      <div className="page-header">
        <div><p className="eyebrow">Account</p><h1>My profile</h1><p className="muted">Share your background with project owners considering you for their teams.</p></div>
      </div>
      <section className="panel profile-panel">
        <div className="profile-identity">
          <h2>{profile.name}</h2>
          <p className="muted">{profile.email}</p>
        </div>
        <form className="stack" onSubmit={handleSubmit}>
          {error && <div className="alert" role="alert">{error}</div>}
          {success && <div className="profile-success" role="status">{success}</div>}
          {FIELDS.map(([field, label, placeholder]) => (
            <label key={field}>
              {label} <span className="muted">(optional)</span>
              <textarea rows={3} maxLength={field === "education" || field === "skills" ? 4000 : 6000} value={profile[field] || ""} onChange={(event) => updateField(field, event.target.value)} placeholder={placeholder} />
            </label>
          ))}
          <button className="btn btn-primary" type="submit" disabled={saving}>{saving ? "Saving…" : "Save profile"}</button>
        </form>
      </section>
    </div>
  );
}
