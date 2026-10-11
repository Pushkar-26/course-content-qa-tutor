
import { useState } from "react";
import {
  Copy,
  RefreshCw,
  Send,
  ThumbsDown,
  ThumbsUp,
} from "lucide-react";
import { sendChatMessage } from "../../services/chatApi";
import "./ChatWindow.css";

function ChatWindow({
  onSourcesChange,
  onCitationClick,
  initialConversation = null,
  onConversationSaved,
}) {
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState(() =>
    (initialConversation?.messages || []).map((message) => ({
      id: message.id,
      role: message.role,
      content: message.content,
      sources: message.sources || [],
    }))
  );
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState(
    initialConversation?.id || null
  );
  const [mode, setMode] = useState("course");

  function renderAnswer(content, messageSources = []) {
    return content.split(/(\[\d+\])/g).map((part, index) => {
      const match = part.match(/^\[(\d+)\]$/);

      if (!match) {
        return <span key={index}>{part}</span>;
      }

      const sourceId = Number(match[1]);

      return (
        <button
          key={index}
          type="button"
          className="citation-chip"
          onClick={() =>
            onCitationClick?.(sourceId, messageSources)
          }
          title={`View source ${sourceId}`}
        >
          {part}
        </button>
      );
    });
  }

  async function handleSend() {
    const trimmedQuery = query.trim();

    if (!trimmedQuery || loading) {
      return;
    }

    const previousUserMessage = [...messages]
      .reverse()
      .find((message) => message.role === "user");

    const history = messages
      .map((message) => message.content)
      .slice(-10);

    const userMessage = {
      id: `${Date.now()}-user`,
      role: "user",
      content: trimmedQuery,
      sources: [],
    };

    setMessages((current) => [...current, userMessage]);
    setQuery("");
    setLoading(true);

    try {
      const data = await sendChatMessage(
        trimmedQuery,
        conversationId,
        previousUserMessage?.content || null,
        history,
        mode
      );

      if (data.conversation_id) {
        setConversationId(data.conversation_id);
        await onConversationSaved?.(data.conversation_id);
      }

      const assistantMessage = {
        id: `${Date.now()}-assistant`,
        role: "assistant",
        content: data.answer,
        sources: data.sources || [],
      };

      setMessages((current) => [
        ...current,
        assistantMessage,
      ]);

      onSourcesChange?.(data.sources || []);
    } catch (error) {
      console.error("Chat request failed:", error);

      const errorMessage = {
        id: `${Date.now()}-error`,
        role: "assistant",
        content:
          error.response?.data?.detail ||
          "Sorry, something went wrong while processing your question.",
        sources: [],
      };

      setMessages((current) => [
        ...current,
        errorMessage,
      ]);

      onSourcesChange?.([]);
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSend();
    }
  }

  async function copyAnswer(content) {
    try {
      await navigator.clipboard.writeText(content);
    } catch (error) {
      console.error("Could not copy answer:", error);
    }
  }

  return (
    <section className="chat-window">
      <div className="messages">
        {messages.length === 0 && (
          <div className="empty-chat">
            <h1>What would you like to learn?</h1>
            <p>
              Ask a question about your uploaded course material.
            </p>
          </div>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            className={`message ${
              message.role === "user"
                ? "user-message"
                : "assistant-message"
            }`}
          >
            <div className="message-label">
              {message.role === "user" ? "You" : "CourseQ AI"}
            </div>

            <div
              className={
                message.role === "user"
                  ? "message-bubble user-bubble"
                  : "assistant-content"
              }
            >
              {message.role === "assistant"
                ? renderAnswer(message.content, message.sources)
                : message.content}
            </div>

            {message.role === "assistant" && (
              <div className="message-actions">
                <button
                  type="button"
                  title="Copy"
                  onClick={() => copyAnswer(message.content)}
                >
                  <Copy size={16} />
                </button>

                <button type="button" title="Helpful">
                  <ThumbsUp size={16} />
                </button>

                <button type="button" title="Not helpful">
                  <ThumbsDown size={16} />
                </button>

                <button type="button" title="Regenerate">
                  <RefreshCw size={16} />
                </button>
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="message assistant-message">
            <div className="message-label">CourseQ AI</div>
            <div className="assistant-content loading-message">
              {mode === "course"
                ? "Searching your course material..."
                : "Thinking of an answer..."}
            </div>
          </div>
        )}
      </div>

      <div className="composer-area">
        <div className="answer-mode-control">
          <label htmlFor="answer-mode">Answer mode</label>

          <select
            id="answer-mode"
            value={mode}
            onChange={(event) => setMode(event.target.value)}
            disabled={loading}
          >
            <option value="course">Course Materials</option>
            <option value="general">General AI</option>
          </select>
        </div>

        <div className="composer">
          <textarea
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question about your course..."
            rows={1}
          />

          <button
            type="button"
            className="send-btn"
            title="Send"
            onClick={handleSend}
            disabled={loading || !query.trim()}
          >
            <Send size={18} />
          </button>
        </div>

        <div className="composer-hint">
          {mode === "course"
            ? "Answers are grounded in your course material."
            : "Answers use general AI knowledge, not your uploaded documents."}
        </div>
      </div>
    </section>
  );
}

export default ChatWindow;
