import { useEffect, useReducer } from "react";
import { Router, useLocation } from "./router.jsx";
import { clearSession, getRole, isAuthed } from "./auth.js";
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
  const { path } = useLocation();

  const authed = isAuthed();
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

  const allowed = authed && role ? routes.filter((r) => r.roles.includes(role)) : [];
  const defaultPath = allowed.length ? allowed[0].path : "/";
  const allowedPaths = allowed.map((r) => r.path);

  // Landing guard: the "not available for your role" page must never be a
  // transient landing state. If the current hash is not one of this role's
  // views (fresh login lands on "#/", or a hash left over from a previous
  // session of another role), go straight to the role's home view instead.
  useEffect(() => {
    if (!authed) return undefined;
    if (!role) {
      // Token without a role means a broken/partial session: force re-login.
      clearSession();
      bump();
      return undefined;
    }
    if (!allowedPaths.includes(path)) {
      window.location.hash = defaultPath;
    }
    return undefined;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [authed, role, path]);

  if (!authed || !role) return <LoginPage onAuthChange={bump} />;

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