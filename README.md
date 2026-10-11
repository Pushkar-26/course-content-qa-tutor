<div align="center">

# CourseQ
### AI-Powered Course Content Q&A Tutor

**Ask questions. Learn from your own material. See exactly where answers come from.**

<p>
  <a href="https://github.com/Pushkar-26/course-content-qa-tutor"><img src="https://img.shields.io/badge/GitHub-Repository-181717?style=for-the-badge&logo=github" alt="GitHub repository"></a>
  <img src="https://img.shields.io/badge/Frontend-React%20%2B%20Vite-61DAFB?style=for-the-badge&logo=react&logoColor=20232A" alt="React and Vite">
  <img src="https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Database-PostgreSQL%20%2B%20pgvector-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL and pgvector">
</p>

</div>

---

## ✨ What is CourseQ?

CourseQ is a document-grounded AI study tutor. Upload course material, ask questions in natural language, and get answers supported by relevant document chunks, clickable citations, and page-level PDF access.

It combines a **Retrieval-Augmented Generation (RAG)** pipeline with a **General AI** mode:

- **Course Materials mode** searches the signed-in user's uploaded material and produces grounded answers with source citations.
- **General AI mode** sends the question directly to Gemini for a general-knowledge answer. It does not search uploaded documents or the live web, and it does not attach document citations.

> **Project goal:** Make course material easier to query while keeping answers traceable to their source.

## 🧭 Contents

- [Highlights](#-highlights)
- [Architecture](#-architecture)
- [Request flows](#-request-flows)
- [RAG pipeline](#-rag-pipeline)
- [Database design](#-database-design)
- [Technology stack](#-technology-stack)
- [Project structure](#-project-structure)
- [Run locally](#-run-locally)
- [API overview](#-api-overview)
- [Security and privacy](#-security-and-privacy)
- [Current scope and limitations](#-current-scope-and-limitations)

## 🚀 Highlights

| Feature | What it does |
|---|---|
| 🔐 **User authentication** | Signup and login, Argon2 password hashing, JWT-based protected endpoints. |
| 📚 **Document library** | Upload PDF, PPTX, DOCX, and TXT files; view the signed-in user's files and delete owned documents. |
| 🧠 **Hybrid retrieval** | Combines vector similarity search with PostgreSQL full-text search. |
| 🔀 **Rank fusion** | Reciprocal Rank Fusion (RRF) combines results from the retrieval channels. |
| 🎯 **Cross-encoder reranking** | Reorders retrieval candidates by query relevance before context construction. |
| 🧩 **Structure-aware chunking** | Uses document layout, headings, paragraphs, and sentence boundaries to preserve context. |
| 📌 **Grounded answers and citations** | Course mode validates citation IDs and applies a lightweight check for claim support against retrieved context. |
| 📄 **Source inspection** | Click an answer citation to inspect the source preview and open the original PDF at the cited page. |
| 💬 **Persistent chat history** | Conversations and messages are stored in PostgreSQL and can be reopened from the sidebar. |
| 🌐 **Two answer modes** | Choose Course Materials for document-grounded answers or General AI for questions outside uploaded material. |
| 🌙 **Dark mode** | Theme selection is remembered in browser local storage. |

## 🏗️ Architecture

The diagrams below are written in Mermaid, so GitHub renders them directly in the README. The layout follows an **Eraser-style architecture view**: clear layers, grouped components, labelled connections, and separate data/processing paths.

### System architecture

```mermaid
flowchart LR
    subgraph CLIENT["PRESENTATION LAYER · React + Vite"]
        UI["CourseQ Web UI"]
        AUTHUI["Login / Signup"]
        CHATUI["Chat Window<br/>Mode selector · Citations"]
        LIBRARY["Document Library<br/>Upload · List · Delete"]
        SOURCES["Source Panel<br/>Preview · Open cited PDF page"]
        UI --> AUTHUI
        UI --> CHATUI
        UI --> LIBRARY
        CHATUI --> SOURCES
    end

    subgraph API["APPLICATION LAYER · FastAPI"]
        AUTH["Auth API<br/>Signup · Login · Current user"]
        DOCAPI["Documents API<br/>Upload · List · Delete · File access"]
        CHATAPI["Chat API<br/>Conversation ownership · Mode dispatch"]
        JWT["JWT verification<br/>Current-user dependency"]
        AUTH --> JWT
        DOCAPI --> JWT
        CHATAPI --> JWT
    end

    subgraph INGEST["DOCUMENT INGESTION"]
        PARSE["Document parser<br/>PDF · PPTX · DOCX · TXT"]
        CLEAN["Text cleaning / normalization"]
        CHUNK["Structure-aware chunker<br/>Sections · Paragraphs · Sentences"]
        EMBED["Gemini embedding model<br/>gemini-embedding-001"]
        PARSE --> CLEAN --> CHUNK --> EMBED
    end

    subgraph RAG["COURSE MATERIALS · RAG PIPELINE"]
        Q["Query analysis and transformation"]
        VSEARCH["Semantic retrieval<br/>pgvector cosine distance"]
        FTS["Lexical retrieval<br/>PostgreSQL full-text search"]
        RRF["Reciprocal Rank Fusion<br/>RRF"]
        RERANK["Cross-encoder reranker<br/>MS MARCO MiniLM"]
        CONTEXT["Context builder<br/>Relevant chunks + bounded neighbours"]
        GROUNDED["Gemini answer generation<br/>Context-grounded prompt"]
        CITE["Citation ID validation<br/>Claim-support check · Formatting"]
        Q --> VSEARCH
        Q --> FTS
        VSEARCH --> RRF
        FTS --> RRF
        RRF --> RERANK --> CONTEXT --> GROUNDED --> CITE
    end

    subgraph GENERAL["GENERAL AI MODE"]
        GAI["Gemini general answer<br/>No document retrieval · No document citations"]
    end

    subgraph DATA["PERSISTENCE LAYER"]
        PG[("PostgreSQL")]
        USERS["users"]
        DOCS["documents"]
        CHUNKS["chunks + vector embeddings"]
        CONV["conversations"]
        MSG["messages + source references"]
        FILES[("Local uploaded files<br/>data/uploads/")]
        PG --- USERS
        PG --- DOCS
        PG --- CHUNKS
        PG --- CONV
        PG --- MSG
    end

    AUTHUI -->|REST / JSON| AUTH
    CHATUI -->|JWT-protected request| CHATAPI
    LIBRARY -->|JWT-protected request| DOCAPI
    DOCAPI --> PARSE
    EMBED --> CHUNKS
    DOCAPI --> DOCS
    DOCAPI --> FILES
    VSEARCH <--> CHUNKS
    FTS <--> CHUNKS
    CHATAPI --> Q
    CHATAPI -->|mode = general| GAI
    CITE -->|Answer + source metadata| CHATAPI
    GAI -->|Answer, empty source list| CHATAPI
    CHATAPI <--> CONV
    CHATAPI <--> MSG
    DOCAPI -->|Owner-scoped file check| FILES
    SOURCES -->|Authenticated PDF fetch| DOCAPI

    classDef client fill:#E9F2FF,stroke:#4B83C3,color:#18324F,stroke-width:1.5px;
    classDef api fill:#E9F8F2,stroke:#339879,color:#173F34,stroke-width:1.5px;
    classDef process fill:#FFF4DE,stroke:#D99A2B,color:#62420B,stroke-width:1.5px;
    classDef storage fill:#F1EAFE,stroke:#9066C6,color:#38245C,stroke-width:1.5px;
    class UI,AUTHUI,CHATUI,LIBRARY,SOURCES client;
    class AUTH,DOCAPI,CHATAPI,JWT api;
    class PARSE,CLEAN,CHUNK,EMBED,Q,VSEARCH,FTS,RRF,RERANK,CONTEXT,GROUNDED,CITE,GAI process;
    class PG,USERS,DOCS,CHUNKS,CONV,MSG,FILES storage;
```

### The two answer paths

```mermaid
flowchart TD
    START([User submits a question]) --> VERIFY[FastAPI validates JWT and identifies user]
    VERIFY --> MODE{Selected answer mode?}

    MODE -->|Course Materials| ANALYZE[Analyze and transform query]
    ANALYZE --> SEARCH1[Vector search over owned documents]
    ANALYZE --> SEARCH2[PostgreSQL full-text search over owned documents]
    SEARCH1 --> FUSE[Reciprocal Rank Fusion]
    SEARCH2 --> FUSE
    FUSE --> RERANK[Cross-encoder reranking]
    RERANK --> BUILD[Build context and expand bounded neighbours]
    BUILD --> ENOUGH{Relevant context available?}
    ENOUGH -->|No| INSUFFICIENT[Explain that course material is insufficient]
    ENOUGH -->|Yes| ANSWER[Generate grounded Gemini answer]
    ANSWER --> VALIDATE[Validate citation IDs and check claim support]
    VALIDATE --> COURSEOUT[Return answer, source metadata and conversation ID]

    MODE -->|General AI| GENERAL[Generate answer using Gemini general knowledge]
    GENERAL --> GENOUT[Return answer, empty document sources and conversation ID]

    INSUFFICIENT --> SAVE[(Save user question and assistant answer)]
    COURSEOUT --> SAVE
    GENOUT --> SAVE
    SAVE --> DONE([Display response in CourseQ])

    classDef decision fill:#FFF4DE,stroke:#D99A2B,color:#62420B,stroke-width:1.5px;
    classDef step fill:#E9F2FF,stroke:#4B83C3,color:#18324F,stroke-width:1.5px;
    classDef storage fill:#F1EAFE,stroke:#9066C6,color:#38245C,stroke-width:1.5px;
    class MODE,ENOUGH decision;
    class ANALYZE,SEARCH1,SEARCH2,FUSE,RERANK,BUILD,ANSWER,VALIDATE,GENERAL,INSUFFICIENT,COURSEOUT,GENOUT,VERIFY step;
    class SAVE storage;
```

## 🔄 Request flows

### 1. Document upload and ingestion

1. The signed-in user selects a PDF, PPTX, DOCX, or TXT file in Document Library.
2. The Documents API checks authentication and validates the file extension.
3. The original file is written to local storage under `data/uploads/` using a generated file name.
4. The parser extracts page/line/layout information where supported; text is cleaned and normalized.
5. The structure-aware chunker groups content around sections and paragraphs and avoids splitting sentences where possible.
6. Each chunk receives document/page/section metadata and an embedding from `gemini-embedding-001`.
7. Document metadata, chunks, and vector embeddings are persisted in PostgreSQL with `pgvector`.
8. The user can inspect the document in their library and ask questions about it.

### 2. Course Materials question

1. The frontend sends a question, selected mode, optional conversation ID, and conversational context to `POST /chat` with a JWT.
2. FastAPI identifies the current user and verifies ownership when an existing conversation ID is supplied.
3. Query analysis/transformation prepares the retrieval queries.
4. Semantic search ranks chunks using vector distance; lexical retrieval uses PostgreSQL full-text search with an OR fallback when the AND-style search yields no results.
5. RRF fuses ranked lists; the cross-encoder reranks candidates.
6. The context builder selects relevant chunks and a bounded set of neighbouring chunks.
7. Gemini generates an answer using the retrieved context. Citation IDs are validated and claim support is checked with the project's current lightweight validation logic.
8. The API returns the answer, numbered source metadata, retrieval query details, and conversation ID. The exchange is saved to PostgreSQL.
9. Clicking a citation selects its source in the UI; Open PDF fetches the file through the authenticated API and navigates to the cited page.

### 3. General AI question

1. The user selects **General AI** mode.
2. The backend calls Gemini directly without document retrieval.
3. The answer is returned without document citations or document sources.
4. The question and answer are saved to the current conversation in PostgreSQL.

**General AI is not live web search.** It uses the model's available knowledge and may not reflect very recent changes.

## 🧠 RAG pipeline

| Stage | Implementation | Purpose |
|---|---|---|
| Parse | PyMuPDF and format-specific parsers | Extract document content and structural signals. |
| Clean | Text normalization utilities | Standardize extracted text before chunking. |
| Chunk | Custom structure-aware chunker | Preserve section/page metadata and split at paragraph/sentence boundaries where possible. |
| Embed | `gemini-embedding-001` | Convert text and queries into vectors. Chunk vectors are stored with **1536 dimensions**. |
| Semantic search | PostgreSQL + `pgvector` cosine distance | Find semantically related chunks. |
| Lexical search | PostgreSQL full-text search | Match meaningful terms and rank matches. |
| Fusion | Reciprocal Rank Fusion (RRF) | Combine vector and lexical ranking signals. |
| Rerank | `cross-encoder/ms-marco-MiniLM-L-6-v2` | Score candidate passages against the query and refine ordering. |
| Context build | Custom context builder | Construct grounded context and include bounded neighbouring chunks. |
| Generate | `gemini-3.5-flash-lite` | Produce the answer from the selected context. |
| Validate | Citation validation + lightweight claim-support checks | Reject invalid citation IDs and flag claims not sufficiently supported by cited context. |
| Present | API source objects + React citation controls | Display source previews and open the cited PDF page. |

### Chunking configuration

- **Target maximum chunk size:** 1,500 characters.
- **Small-section merge threshold:** 150 characters.
- **Overlap:** one sentence when applicable.
- **Chunking style:** heading/section-aware, paragraph-aware, and sentence-preserving where possible.
- **Metadata retained:** document ID, source name, start/end page, section path, chunk ID, and chunk index.

These are character-based settings, not token counts. The 150-character value is used while merging tiny sections; it is not a hard minimum for every chunk.

## 🗃️ Database design

CourseQ uses PostgreSQL for application records and vector retrieval. Uploaded original documents are currently stored on the local filesystem; PostgreSQL stores their metadata and extracted chunks, not the original file bytes.

```mermaid
erDiagram
    USER ||--o{ CONVERSATION : owns
    CONVERSATION ||--o{ MESSAGE : contains
    USER ||--o{ DOCUMENT : owns
    DOCUMENT ||--o{ CHUNK : contains

    USER {
        varchar id PK
        varchar email UK
        varchar password_hash
        datetime created_at
    }

    CONVERSATION {
        varchar id PK
        varchar user_id FK
        varchar title
        datetime created_at
        datetime updated_at
    }

    MESSAGE {
        varchar id PK
        varchar conversation_id FK
        varchar role
        text content
        json sources
        datetime created_at
    }

    DOCUMENT {
        varchar id PK
        varchar owner_id FK
        varchar filename
        varchar file_path
        varchar file_type
        integer page_count
        varchar status
        datetime uploaded_at
    }

    CHUNK {
        varchar id PK
        varchar document_id FK
        varchar source
        integer page_number
        integer page_end
        varchar section
        text text
        integer chunk_index
        vector embedding
    }
```

### Main tables

- **`users`**: account ID, unique email, password hash, creation timestamp.
- **`documents`**: file metadata, owner ID, processing status, page count, and local path.
- **`chunks`**: extracted text, page/section metadata, chunk order, and vector embedding.
- **`conversations`**: conversation owner, title, creation and update timestamps.
- **`messages`**: message role/content, timestamp, and JSON source references for assistant answers.

The database is accessed using SQLAlchemy. `pgvector` stores embeddings and enables vector distance queries; PostgreSQL full-text search provides the lexical retrieval channel.

## 🧰 Technology stack

### Frontend

- React
- Vite
- Plain CSS (no Tailwind dependency)
- Axios for API requests
- Lucide React icons
- Browser `sessionStorage` for the current JWT and `localStorage` for the theme preference

### Backend and AI

- Python + FastAPI
- SQLAlchemy ORM
- Google Gen AI SDK
- `gemini-embedding-001` embeddings (1536 dimensions)
- `gemini-3.5-flash-lite` answer generation
- `cross-encoder/ms-marco-MiniLM-L-6-v2` reranking
- PyMuPDF, python-pptx, python-docx

### Data and authentication

- PostgreSQL
- `pgvector`
- PostgreSQL full-text search
- Argon2 password hashing via `pwdlib`
- JWT access tokens via PyJWT
- Local filesystem storage for uploaded source documents

## 📁 Project structure

```text
course-content-qa-tutor/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── auth.py
│   │   │   ├── chat.py
│   │   │   └── documents.py
│   │   ├── db/
│   │   │   ├── database.py
│   │   │   ├── init_db.py
│   │   │   └── models.py
│   │   ├── embeddings/
│   │   ├── generation/
│   │   ├── ingestion/
│   │   ├── retrieval/
│   │   ├── services/
│   │   ├── main.py
│   │   └── security.py
│   ├── requirements.txt
│   └── test_*.py
├── data/
│   └── uploads/              # Local uploads; ignored by Git
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── chat/
│   │   │   ├── layout/
│   │   │   └── sources/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── App.jsx
│   │   └── index.css
│   ├── package.json
│   └── vite.config.js
└── .gitignore
```

## 🏁 Run locally

### Prerequisites

- Python 3.12 recommended for the current development setup
- Node.js and npm
- PostgreSQL with the `pgvector` extension available
- A Google Gemini API key

### 1. Clone the repository

```bash
git clone https://github.com/Pushkar-26/course-content-qa-tutor.git
cd course-content-qa-tutor
```

### 2. Create a PostgreSQL database

Create a database for CourseQ using your preferred PostgreSQL client. Connect to that database and enable the vector extension:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Ensure the PostgreSQL user in your connection string has permission to connect and create/use the required tables and extension.

### 3. Configure the backend environment

Create `backend/.env` (do **not** commit this file):

```env
DATABASE_URL=postgresql+psycopg2://YOUR_DB_USER:YOUR_DB_PASSWORD@localhost:5432/YOUR_DATABASE
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
JWT_SECRET_KEY=REPLACE_WITH_A_RANDOM_SECRET
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
```

Generate a strong JWT secret locally:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Paste the generated value into `JWT_SECRET_KEY`. Never publish API keys, database passwords, or real JWT secrets.

### 4. Install backend dependencies and initialize tables

**Windows CMD:**

```cmd
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m app.db.init_db
```

If `pgvector` was not installed/enabled for your PostgreSQL instance, resolve that before initializing the database.

### 5. Start the backend

From the `backend` directory with the virtual environment activated:

```cmd
python -m uvicorn app.main:app --reload
```

- API root: <http://127.0.0.1:8000/>
- Interactive API docs: <http://127.0.0.1:8000/docs>

Keep the backend terminal open while using the application.

### 6. Configure and start the frontend

Open a second terminal:

```cmd
cd frontend
npm install
```

Create `frontend/.env`:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Then start Vite:

```cmd
npm run dev
```

Open <http://localhost:5173>.

> **Local development note:** The FastAPI CORS configuration currently allows the Vite origins `http://localhost:5173` and `http://127.0.0.1:5173`.

## 🔌 API overview

The interactive and authoritative request schemas are available at `/docs` after the backend starts.

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/auth/signup` | Create an account. |
| `POST` | `/auth/login` | Verify credentials and issue a JWT access token. |
| `GET` | `/auth/me` | Return the current authenticated user. |
| `POST` | `/documents/upload` | Upload and process a supported document. |
| `GET` | `/documents` | List the current user's documents. |
| `GET` | `/documents/{document_id}/file` | Fetch an owned source file. |
| `DELETE` | `/documents/{document_id}` | Delete an owned document and its stored chunks/file. |
| `POST` | `/chat` | Ask a question in `course` or `general` mode. |
| `GET` | `/chat/conversations` | List conversations owned by the current user. |
| `GET` | `/chat/conversations/{conversation_id}` | Fetch messages and stored source references for an owned conversation. |

Protected endpoints use a bearer JWT returned by `/auth/login`. In Swagger, use **Authorize** and supply the current token.

## 🔐 Security and privacy

- Passwords are hashed with Argon2; raw passwords are not stored.
- JWT-protected endpoints identify the current user from the verified token.
- Chat retrieval scopes vector and full-text search to documents owned by the authenticated user.
- Conversation fetch and update paths validate conversation ownership.
- Document file access and deletion validate document ownership.
- `.env`, Python virtual environments, Node dependencies, and uploaded documents are excluded by `.gitignore`.

**Important:** This is a portfolio/local MVP, not yet a hardened public production deployment. Before exposing it publicly, add operational safeguards such as request/file-size limits, rate limiting, stronger deployment secret management, automated security tests, monitoring, and a reviewed database migration strategy. Local disk storage also needs a persistent/shared storage plan for production hosting.

## ✅ Current scope and limitations

### Included in the MVP

- Signup, login, JWT-authenticated requests, and logout in the frontend.
- User-scoped document and conversation listing.
- Document upload, processing, source preview, PDF page opening, and deletion.
- Course Materials RAG mode and General AI mode.
- Hybrid retrieval, reranking, citation handling, persistent messages, and reopenable chat history.
- Light/dark theme switching.

### Intentionally not included yet

- Live web search in General AI mode.
- Password reset and email verification.
- Search, rename, pin/archive, and export for conversations.
- Functional answer feedback analytics or regeneration controls.
- Cloud/object storage, background job queue, admin dashboard, or production deployment pipeline.
- Persisting the selected answer mode with each conversation across reloads (current UI defaults to Course Materials when a conversation is reopened).

### Validation note

Citation IDs are validated and the app applies a lightweight claim-support check against retrieved context. This reduces some unsupported output, but it is not a formal proof that every sentence is entailed by its cited source. Users should verify high-stakes or critical information against the original material.

## 🧪 Tests

The backend includes focused tests for retrieval, reranking, chunking, citations, embedding, and end-to-end behavior. Run tests from the backend folder after configuring the required environment and services:

```cmd
python -m pytest
```

Some integration tests may need a reachable PostgreSQL instance, `pgvector`, valid Gemini credentials, and access to the configured test data.

## 🌱 Future improvements

- Automated multi-user authorization tests for documents, retrieval, and conversations.
- File-size/type/content validation and robust failed-ingestion recovery.
- Persist answer mode and other conversation metadata.
- Search and management tools for saved conversations.
- Production deployment with managed database and object storage.

---

<div align="center">

**Built to make course material searchable, explainable, and easier to learn from.**

[Repository](https://github.com/Pushkar-26/course-content-qa-tutor) · [API Docs](http://127.0.0.1:8000/docs) *(available when running locally)*

</div>
