import { useEffect, useState } from "react";
import {
  getDocuments,
  uploadDocument,
  deleteDocument,
} from "../services/documentApi";
import "./DocumentLibrary.css";

function DocumentLibrary() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [deletingId, setDeletingId] = useState(null);

  async function loadDocuments() {
    setLoading(true);
    setError("");

    try {
      const data = await getDocuments();
      setDocuments(data);
    } catch (err) {
      setError(
        err.response?.data?.detail || "Could not load documents."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDocuments();
  }, []);

  async function handleDelete(doc) {
    const confirmed = window.confirm(
      `Delete "${doc.filename}"? This action cannot be undone.`
    );

    if (!confirmed) return;

    setDeletingId(doc.document_id);
    setError("");
    setMessage("");

    try {
      await deleteDocument(doc.document_id);
      setMessage(`"${doc.filename}" deleted successfully.`);
      await loadDocuments();
    } catch (err) {
      setError(
        err.response?.data?.detail || "Could not delete this document."
      );
    } finally {
      setDeletingId(null);
    }
  }

  async function handleUpload(event) {
    const file = event.target.files?.[0];
    event.target.value = "";

    if (!file) return;

    const allowed = [".pdf", ".pptx", ".docx", ".txt"];
    const extension = file.name
      .slice(file.name.lastIndexOf("."))
      .toLowerCase();

    if (!allowed.includes(extension)) {
      setError("Please select a PDF, PPTX, DOCX, or TXT file.");
      return;
    }

    setUploading(true);
    setError("");
    setMessage("");

    try {
      await uploadDocument(file);
      setMessage("Document uploaded successfully.");
      await loadDocuments();
    } catch (err) {
      setError(
        err.response?.data?.detail || "Document upload failed."
      );
    } finally {
      setUploading(false);
    }
  }

  return (
    <main className="document-library">
      <header className="library-header">
        <div>
          <p className="library-eyebrow">YOUR STUDY MATERIAL</p>
          <h1>Document Library</h1>
          <p className="library-description">
            Upload and manage the documents you study with CourseQ.
          </p>
        </div>

        <label className="upload-button">
          {uploading ? "Uploading..." : "＋ Upload document"}
          <input
            type="file"
            accept=".pdf,.pptx,.docx,.txt"
            onChange={handleUpload}
            disabled={uploading}
            hidden
          />
        </label>
      </header>

      {error && (
        <p className="library-error" role="alert">
          {error}
        </p>
      )}

      {message && (
        <p className="library-success" role="status">
          {message}
        </p>
      )}

      <section className="document-list">
        <div className="document-list-header">
          <h2>Your documents</h2>
          <span>{documents.length} files</span>
        </div>

        {loading ? (
          <p className="library-empty">Loading documents...</p>
        ) : documents.length === 0 ? (
          <div className="library-empty">
            <h3>No documents yet</h3>
            <p>
              Upload your course material to start asking questions.
            </p>
          </div>
        ) : (
          documents.map((doc) => (
            <article
              className="document-card"
              key={doc.document_id}
            >
              <div className="document-icon">
                {doc.file_type === ".pdf" ? "PDF" : "DOC"}
              </div>

              <div className="document-info">
                <h3>{doc.filename}</h3>
                <p>
                  {doc.file_type?.toUpperCase().replace(".", "") || "FILE"}
                  {" · "}
                  {doc.page_count != null
                    ? `${doc.page_count} pages`
                    : "Page count unavailable"}
                </p>
              </div>

              <span className={`document-status status-${doc.status}`}>
                {doc.status}
              </span>

              <button
                type="button"
                className="delete-document-btn"
                disabled={deletingId === doc.document_id}
                onClick={() => handleDelete(doc)}
              >
                {deletingId === doc.document_id
                  ? "Deleting..."
                  : "Delete"}
              </button>
            </article>
          ))
        )}
      </section>
    </main>
  );
}

export default DocumentLibrary;