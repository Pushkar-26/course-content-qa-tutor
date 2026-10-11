
import { useEffect, useState } from "react";
import Sidebar from "../components/layout/Sidebar";
import Topbar from "../components/layout/Topbar";
import ChatWindow from "../components/chat/ChatWindow";
import SourcePanel from "../components/sources/SourcePanel";
import DocumentLibrary from "./DocumentLibrary";
import {
  getConversations,
  getConversation,
} from "../services/chatApi";
import "./ChatPage.css";

function ChatPage({ isDark, onToggleTheme, onLogout }) {
  const [sources, setSources] = useState([]);
  const [selectedSource, setSelectedSource] = useState(null);
  const [chatVersion, setChatVersion] = useState(0);
  const [currentView, setCurrentView] = useState("chat");

  const [conversations, setConversations] = useState([]);
  const [activeConversationId, setActiveConversationId] = useState(null);
  const [openedConversation, setOpenedConversation] = useState(null);
  const [historyError, setHistoryError] = useState("");
  const [openingConversation, setOpeningConversation] = useState(false);

  async function loadConversations() {
    try {
      const data = await getConversations();
      setConversations(data);
      setHistoryError("");
    } catch (error) {
      console.error("Could not load conversations:", error);
      setHistoryError("Could not load chat history.");
    }
  }

  useEffect(() => {
    loadConversations();
  }, []);

  function handleSourcesChange(nextSources) {
    setSources(nextSources);
    setSelectedSource(null);
  }

  function handleCitationClick(sourceId, messageSources = sources) {
    const matchingSources = messageSources || [];
    setSources(matchingSources);

    const source = matchingSources.find(
      (item) => Number(item.id) === sourceId
    );

    setSelectedSource(source || null);
  }

  function handleNewChat() {
    setCurrentView("chat");
    setChatVersion((current) => current + 1);
    setOpenedConversation(null);
    setActiveConversationId(null);
    setSources([]);
    setSelectedSource(null);
  }

  function handleOpenChat() {
    setCurrentView("chat");
  }

  function handleOpenDocuments() {
    setCurrentView("documents");
  }

  async function handleSelectConversation(conversationId) {
    setOpeningConversation(true);
    setHistoryError("");

    try {
      const data = await getConversation(conversationId);

      setOpenedConversation(data);
      setActiveConversationId(data.id);
      setCurrentView("chat");

      const lastAssistantMessage = [...data.messages]
        .reverse()
        .find((message) => message.role === "assistant");

      setSources(lastAssistantMessage?.sources || []);
      setSelectedSource(null);
      setChatVersion((current) => current + 1);
    } catch (error) {
      console.error("Could not open conversation:", error);
      setHistoryError("Could not open this conversation.");
    } finally {
      setOpeningConversation(false);
    }
  }

  async function handleConversationSaved(conversationId) {
    setActiveConversationId(conversationId);
    await loadConversations();
  }

  return (
    <div className="chat-page">
      <Sidebar
        onNewChat={handleNewChat}
        onOpenChat={handleOpenChat}
        onOpenDocuments={handleOpenDocuments}
        conversations={conversations}
        activeConversationId={activeConversationId}
        onSelectConversation={handleSelectConversation}
      />

      <div className="chat-page-main">
        <Topbar
          isDark={isDark}
          onToggleTheme={onToggleTheme}
          onLogout={onLogout}
        />

        {historyError && (
          <p
            role="alert"
            style={{ padding: "8px 16px", color: "#b91c1c" }}
          >
            {historyError}
          </p>
        )}

        {openingConversation && (
          <p style={{ padding: "8px 16px", color: "#64748b" }}>
            Opening conversation...
          </p>
        )}

        <div className="chat-layout">
          <div
            style={{
              display: currentView === "chat" ? "contents" : "none",
            }}
          >
            <ChatWindow
              key={chatVersion}
              initialConversation={openedConversation}
              onConversationSaved={handleConversationSaved}
              onSourcesChange={handleSourcesChange}
              onCitationClick={handleCitationClick}
            />

            <SourcePanel
              sources={sources}
              selectedSource={selectedSource}
              onSelectSource={setSelectedSource}
            />
          </div>

          {currentView === "documents" && (
            <div style={{ gridColumn: "1 / -1", minWidth: 0 }}>
              <DocumentLibrary />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default ChatPage;
