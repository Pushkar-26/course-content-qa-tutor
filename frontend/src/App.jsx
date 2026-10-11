
import { useEffect, useState } from "react";
import AuthPage from "./pages/AuthPage";
import ChatPage from "./pages/ChatPage";
import { getCurrentUser } from "./services/authApi";

function App() {
  const [user, setUser] = useState(null);
  const [checkingAuth, setCheckingAuth] = useState(true);

  const [isDark, setIsDark] = useState(
    () => localStorage.getItem("courseq-theme") === "dark"
  );

  useEffect(() => {
    const theme = isDark ? "dark" : "light";
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("courseq-theme", theme);
  }, [isDark]);

  useEffect(() => {
    const token = sessionStorage.getItem("access_token");

    if (!token) {
      setCheckingAuth(false);
      return;
    }

    getCurrentUser(token)
      .then(setUser)
      .catch(() => {
        sessionStorage.removeItem("access_token");
      })
      .finally(() => setCheckingAuth(false));
  }, []);

  function handleAuthenticated(data) {
    sessionStorage.setItem("access_token", data.access_token);
    setUser(data.user);
  }

  function handleToggleTheme() {
    setIsDark((current) => !current);
  }

  function handleLogout() {
    sessionStorage.removeItem("access_token");
    setUser(null);
  }

  if (checkingAuth) {
    return <p>Checking session...</p>;
  }

  if (!user) {
    return <AuthPage onAuthenticated={handleAuthenticated} />;
  }

  return (
    <ChatPage
      isDark={isDark}
      onToggleTheme={handleToggleTheme}
      onLogout={handleLogout}
    />
  );
}

export default App;
