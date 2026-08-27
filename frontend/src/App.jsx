import { useReducer } from "react";
import { Router } from "./router.jsx";
import { isAuthed, getRole } from "./auth.js";
import Layout from "./components/Layout.jsx";
import LoginPage from "./pages/LoginPage.jsx";
import DashboardPage from "./pages/DashboardPage.jsx";
import EmploymentPage from "./pages/EmploymentPage.jsx";
import SkillGapPage from "./pages/SkillGapPage.jsx";
import ProgramImpactPage from "./pages/ProgramImpactPage.jsx";
import ProviderOverview from "./pages/ProviderViews.jsx";
import TraineeViews from "./pages/TraineeViews.jsx";

export default function App() {
  const [, bump] = useReducer((x) => x + 1, 0);

  if (!isAuthed()) return <LoginPage onAuthChange={bump} />;

  const role = getRole();

  // Each route carries: path, element, and the roles allowed to see it.
  const routes = [
    { path: "/", element: <DashboardPage />, roles: ["admin"] },
    { path: "/employment", element: <EmploymentPage />, roles: ["admin"] },
    { path: "/skill-gaps", element: <SkillGapPage />, roles: ["admin"] },
    { path: "/program-impact", element: <ProgramImpactPage />, roles: ["admin"] },
    { path: "/overview", element: <ProviderOverview />, roles: ["provider"] },
    { path: "/my-profile", element: <TraineeViews />, roles: ["trainee"] },
  ];

  const allowed = routes.filter((r) => r.roles.includes(role));
  const defaultPath = allowed.length ? allowed[0].path : "/";

  return (
    <Layout role={role} onAuthChange={bump}>
      <Router
        routes={allowed}
        fallback={
          <div className="page-note">
            <h2>Page not found</h2>
            <p>That view is not available for your role.</p>
            <button className="btn" onClick={() => (window.location.hash = defaultPath)}>
              Back to home
            </button>
          </div>
        }
      />
    </Layout>
  );
}