
import {
  ExternalLink,
  FileText,
  X,
} from "lucide-react";
import "./SourcePanel.css";
import api from "../../services/api";
function SourcePanel({
  sources,
  selectedSource,
  onSelectSource,
}) {

  function closeSource() {
    onSelectSource(null);
  }
  
async function openPdf() {
  if (!selectedSource?.document_id) {
    console.error("No document selected.");
    return;
  }

  const pdfWindow = window.open("about:blank", "_blank");

  if (!pdfWindow) {
    alert("Please allow pop-ups to open the source PDF.");
    return;
  }

  try {
    const page = selectedSource.page_start || 1;

    const response = await api.get(
      `/documents/${encodeURIComponent(selectedSource.document_id)}/file`,
      { responseType: "blob" }
    );

    const pdfUrl = URL.createObjectURL(response.data);

    pdfWindow.location.href = `${pdfUrl}#page=${page}`;

    window.setTimeout(() => {
      URL.revokeObjectURL(pdfUrl);
    }, 60000);
  } catch (error) {
    pdfWindow.close();
    console.error("Failed to open PDF:", error);

    alert(
      error.response?.status === 401
        ? "Your session has expired. Please sign in again."
        : error.response?.status === 404
          ? "Document unavailable or access denied."
          : "Unable to open the source PDF. Please try again."
    );
  }
}


  return (
    <aside className="source-panel">
      <div className="source-header">
        <h2>Sources</h2>
        <span>{sources.length}</span>
      </div>

      {selectedSource ? (
        <div className="source-details">
          <div className="source-details-header">
            <div>
              <div className="source-details-label">
                SOURCE {selectedSource.id}
              </div>

              <h3>{selectedSource.source}</h3>
            </div>

            <button
              className="source-close"
              onClick={closeSource}
              title="Close"
            >
              <X size={18} />
            </button>
          </div>

          <div className="source-meta">
            <span>
              Page {selectedSource.page_start}
              {selectedSource.page_end &&
              selectedSource.page_end !==
                selectedSource.page_start
                ? `-${selectedSource.page_end}`
                : ""}
            </span>

            {selectedSource.section && (
              <span>{selectedSource.section}</span>
            )}
          </div>

          <div className="source-preview">
            <div className="source-preview-title">
              Retrieved evidence
            </div>

            <p>{selectedSource.preview}</p>
          </div>

          <button
             className="open-source-btn"
             onClick={openPdf}
          >
            <FileText size={15} />
            Open PDF
            <ExternalLink size={14} />
          </button>
        </div>
      ) : (
        <div className="source-list">
          {sources.length === 0 ? (
            <div className="empty-sources">
              Sources will appear here after you ask a question.
            </div>
          ) : (
            sources.map((source) => (
              <button
                className="source-card"
                key={source.id}
                onClick={() =>
                  onSelectSource(source)
                }
              >
                <div className="source-top">
                  <div className="source-number">
                    {source.id}
                  </div>

                  <div>
                    <div className="source-name">
                      {source.source}
                    </div>

                    <div className="source-page">
                      Page {source.page_start}
                      {source.page_end &&
                      source.page_end !==
                        source.page_start
                        ? `-${source.page_end}`
                        : ""}
                      {source.section
                        ? ` · ${source.section}`
                        : ""}
                    </div>
                  </div>
                </div>

                <div className="source-action">
                  <FileText size={14} />
                  View source
                  <ExternalLink size={14} />
                </div>
              </button>
            ))
          )}
        </div>
      )}
    </aside>
  );
}

export default SourcePanel;