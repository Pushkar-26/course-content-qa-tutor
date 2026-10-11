import api from "./api";

export async function sendChatMessage(
  query,
  conversationId = null,
  previousQuery = null,
  history = [],
  mode = "course"
) {
  const response = await api.post("/chat", {
    query,
    conversation_id: conversationId,
    previous_query: previousQuery,
    history,
    mode,
  });

  return response.data;
}

export async function getConversations() {
  const response = await api.get("/chat/conversations");
  return response.data.conversations || [];
}

export async function getConversation(conversationId) {
  const response = await api.get(
    `/chat/conversations/${encodeURIComponent(conversationId)}`
  );
  return response.data;
}
