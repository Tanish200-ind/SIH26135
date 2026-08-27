import { Link } from "../router.jsx";
import { clearSession, getEmail } from "../auth.js";

// Distinctive dark government-navy sidebar with grouped navigation.
// Role-aware: only the sections a role may see are offered.
const NAV = {
  admin: [
    { group: "Intelligence", items: [
      { path: "/", label: "Government dashboard", icon: "◧" },
      { path: "/employment", label: "Employment outcomes", icon: "⬤" },
      { path: "/skill-gaps", label: "Skill gaps", icon: "▤" },
      { path: "/program-impact", label: "Programme impact", icon: "⧉" },
    ] },
  ],
  provider: [
    { group: "Provider", items: [
      { path: "/overview", label: "Overview", icon: "◧" },
    ] },
  ],
  trainee: [
    { group: "My account", items: [
      { path: "/my-profile", label: "My profile", icon: "◧" },
    ] },
  ],
};

export default function Sidebar({ role, onNavigate }) {
  const email = getEmail();
  const sections = NAV[role] || [];

  // Decide active item from the current hash.
  const activePath = (window.location.hash.replace(/^#/, "") || "/").split("?")[0];

  function signOut() {
    clearSession();
    window.location.hash = "/";
    if (onNavigate) onNavigate();
  }

  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark">SA</div>
        <div className="brand-text">
          <span className="brand-name">StatAvishkar</span>
          <span className="brand-sub">Skilling intelligence</span>
        </div>
      </div>

      <nav className="sidebar-nav">
        {sections.map((group) => (
          <div className="nav-group" key={group.group}>
            <div className="nav-group-title">{group.group}</div>
            {group.items.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`nav-link ${activePath === item.path ? "active" : ""}`}
              >
                <span className="nav-icon">{item.icon}</span>
                <span>{item.label}</span>
              </Link>
            ))}
          </div>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="sidebar-user">{email || "Signed in"}</div>
        <button className="btn-ghost btn-signout" onClick={signOut}>
          Sign out
        </button>
      </div>
    </aside>
  );
}