import Sidebar from "./Sidebar.jsx";
import TopBar from "./TopBar.jsx";

const TITLES = {
  admin: {
    "/": { title: "Government dashboard", kicker: "Skilling Intelligence Platform" },
    "/employment": { title: "Employment outcomes", kicker: "Where training leads" },
    "/skill-gaps": { title: "Skill gaps", kicker: "Where skills are missing" },
    "/program-impact": { title: "Programme impact", kicker: "What actually works" },
  },
  provider: { "/overview": { title: "Provider overview", kicker: "Your programmes" } },
  trainee: { "/my-profile": { title: "My profile", kicker: "Your record" } },
};

export default function Layout({ role, onAuthChange, children }) {
  const raw = (window.location.hash.replace(/^#/, "") || "/").split("?")[0];
  const meta = (TITLES[role] || {})[raw] || { title: "SIH26135", kicker: "" };

  return (
    <div className="layout">
      <Sidebar role={role} onNavigate={onAuthChange} />
      <div className="main">
        <TopBar title={meta.title} kicker={meta.kicker} />
        <div className="content">{children}</div>
        <footer className="footer">
          StatAvishkar — statutory demo dashboard · reads live from the seeded SIH26135 database.
        </footer>
      </div>
    </div>
  );
}