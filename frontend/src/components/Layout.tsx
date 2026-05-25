import { BookOpenCheck, ClipboardList, FilePlus2, LogOut, ShieldCheck } from "lucide-react";
import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

const adminRoles = new Set(["admin", "instructor", "reviewer"]);

export function Layout() {
  const { user, logout } = useAuth();
  const isAdmin = user ? adminRoles.has(user.role) : false;

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <ShieldCheck size={28} />
          <div>
            <strong>ExamGuard</strong>
            <span>Proctoring Platform</span>
          </div>
        </div>

        <nav className="nav">
          <NavLink to="/candidate/exams">
            <BookOpenCheck size={18} /> Candidate Exams
          </NavLink>
          {isAdmin && (
            <>
              <NavLink to="/admin/exams/new">
                <FilePlus2 size={18} /> Create Exam
              </NavLink>
              <NavLink to="/admin/review">
                <ClipboardList size={18} /> Review Attempts
              </NavLink>
            </>
          )}
        </nav>

        <div className="identity">
          <span>{user?.username}</span>
          <small>{user?.email}</small>
          <button className="ghost-button" type="button" onClick={logout}>
            <LogOut size={16} /> Sign out
          </button>
        </div>
      </aside>
      <main className="content">
        <Outlet />
      </main>
    </div>
  );
}
