
import {
  FileText,
  History,
  MessageSquare,
  Plus,
  Settings,
  Search,
} from "lucide-react";
import "./Sidebar.css";

function Sidebar({
  onNewChat,
  onOpenChat,
  onOpenDocuments,
  conversations = [],
  activeConversationId = null,
  onSelectConversation,
}) {
  return (
    <aside className="sidebar">
      <div className="sidebar-top">
        <div className="brand">
          <div className="brand-mark">C</div>
          <span>CourseQ</span>
        </div>

        <button
          type="button"
          className="new-chat-btn"
          onClick={onNewChat}
        >
          <Plus size={18} />
          <span>New chat</span>
        </button>

        <div className="search-box">
          <Search size={16} />
          <input
            placeholder="Search chats..."
            aria-label="Search chats"
          />
        </div>
      </div>

      <div className="chat-history">
        <div className="history-label">Your conversations</div>

        {conversations.length === 0 ? (
          <p className="history-empty">
            No saved chats yet.
          </p>
        ) : (
          conversations.map((conversation) => (
            <button
              type="button"
              key={conversation.id}
              className={`history-item ${
                conversation.id === activeConversationId
                  ? "active"
                  : ""
              }`}
              onClick={() => {
                onSelectConversation?.(conversation.id);
              }}
              title={conversation.title}
            >
              <MessageSquare size={16} />
              <span>{conversation.title || "New Chat"}</span>
            </button>
          ))
        )}
      </div>

      <div className="sidebar-bottom">
        <button
          type="button"
          className="side-link"
          onClick={onOpenChat}
        >
          <MessageSquare size={18} />
          <span>Chat</span>
        </button>

        <button
          type="button"
          className="side-link"
          onClick={onOpenDocuments}
        >
          <FileText size={18} />
          <span>Documents</span>
        </button>

        <button type="button" className="side-link">
          <History size={18} />
          <span>History</span>
        </button>

        <button type="button" className="side-link">
          <Settings size={18} />
          <span>Settings</span>
        </button>
      </div>
    </aside>
  );
}

export default Sidebar;
