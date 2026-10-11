import {
  ChevronDown,
  Moon,
  Sun,
  User,
  LogOut,
} from "lucide-react";
import "./Topbar.css";

function Topbar({ isDark, onToggleTheme, onLogout }) {
  return (
    <header className="topbar">
      <div className="scope-selector">
        <span className="scope-label">Scope:</span>
        <button type="button" className="scope-btn">
          All documents
          <ChevronDown size={16} />
        </button>
      </div>

      <div className="topbar-actions">
        <button
          type="button"
          className="icon-btn"
          title={isDark ? "Switch to light mode" : "Switch to dark mode"}
          aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
          onClick={onToggleTheme}
        >
          {isDark ? <Sun size={18} /> : <Moon size={18} />}
        </button>

        <button type="button" className="profile-btn">
          <User size={18} />
          <span>Student</span>
          <ChevronDown size={16} />
        </button>

        <button
          type="button"
          className="icon-btn logout-btn"
          title="Logout"
          aria-label="Logout"
          onClick={onLogout}
        >
          <LogOut size={18} />
        </button>
      </div>
    </header>
  );
}

export default Topbar;