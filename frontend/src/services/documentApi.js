import api from "./api";

export async function getDocuments() {
  const response = await api.get("/documents");
  return response.data.documents || [];
}

export async function uploadDocument(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await api.post("/documents/upload", formData);
  return response.data;
}
export async function deleteDocument(documentId) {
  const response = await api.delete(
    `/documents/${encodeURIComponent(documentId)}`
  );

  return response.data;
}