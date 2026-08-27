import { getRole, getEmail } from "../auth.js";

const ROLE_LABEL = { admin: "Government / Admin", provider: "Training Provider", trainee: "Trainee" };

export default function TopBar({ title, kicker }) {
  const role = getRole();
  const email = getEmail();
  return (
    <header className="topbar">
      <div className="topbar-title">
        {kicker && <span className="topbar-kicker">{kicker}</span>}
        <h1>{title}</h1>
      </div>
      <div className="topbar-meta">
        <span className="role-pill">{ROLE_LABEL[role] || role}</span>
        <span className="topbar-email">{email}</span>
      </div>
    </header>
  );
}