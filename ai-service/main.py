"""
main.py - CyberGaze AI Service (FastAPI)
=========================================
Core API server for the DFIR AI & Mining Engine.

Endpoints:
    POST /ingest  - Load forensic logs CSV into FAISS vector store
    POST /mine    - Run FP-Growth pattern mining on loaded logs
    POST /chat    - Natural language Q&A via LangChain + Ollama RAG

CORS is enabled for all origins to allow the React dashboard (localhost:3000/5173)
to communicate with this service.
"""

import os
import pandas as pd

from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# LangChain components for RAG pipeline (LangChain 1.x compatible imports)
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import CharacterTextSplitter
from langchain_core.documents import Document
from langchain_groq import ChatGroq
from langchain_core.embeddings import Embeddings

# Local modules
from mining_engine import run_fpgrowth

# ─────────────────────────────────────────────
# Load environment variables from .env
# ─────────────────────────────────────────────
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL   = os.getenv("GROQ_MODEL", "llama3-8b-8192")
LOG_CSV_PATH = os.getenv("LOG_CSV_PATH", "./forensic_logs.csv")

# ─────────────────────────────────────────────
# Global state (in-memory store for prototype)
# ─────────────────────────────────────────────
app_state = {
    "df": None,           # Loaded log DataFrame
    "vectorstore": None,  # FAISS vector store
    "retriever": None,    # FAISS retriever for RAG
    "llm": None,          # Ollama LLM instance
}


# ─────────────────────────────────────────────
# Fake Embeddings (fallback when no GPU/model)
# ─────────────────────────────────────────────
class FakeEmbeddings(Embeddings):
    """
    Lightweight fake embeddings for development/testing.
    Uses character-count hashing to produce stable 384-dim vectors.
    In production, replace with HuggingFaceEmbeddings or OpenAIEmbeddings.
    """

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._hash_embed(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._hash_embed(text)

    def _hash_embed(self, text: str) -> list[float]:
        """Deterministic pseudo-embedding based on character frequencies."""
        import hashlib
        import struct
        dim = 384
        # sha256 produces 32 bytes → unpack as 32 unsigned bytes
        h = hashlib.sha256(text.encode()).digest()
        base = list(struct.unpack("32B", h))
        # Tile to required dimension and normalize to [0, 1]
        extended = (base * (dim // len(base) + 1))[:dim]
        return [x / 255.0 for x in extended]


# ─────────────────────────────────────────────
# FastAPI App with lifespan
# ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Auto-ingest logs on startup if CSV exists."""
    if os.path.exists(LOG_CSV_PATH):
        print(f"[CyberGaze] Auto-loading logs from {LOG_CSV_PATH} on startup...")
        _load_and_index(LOG_CSV_PATH)
    else:
        print(f"[CyberGaze] No CSV found at {LOG_CSV_PATH}. Use POST /ingest to load data.")
    yield
    print("[CyberGaze] Shutting down AI service.")


app = FastAPI(
    title="CyberGaze AI Service",
    description="DFIR AI Engine: Log Ingestion, FP-Growth Mining, and RAG Chat",
    version="1.0.0",
    lifespan=lifespan,
)

# ─────────────────────────────────────────────
# CORS Configuration
# ─────────────────────────────────────────────
# Allow React dashboard (Vite default: 5173, CRA default: 3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────
# Request/Response Models
# ─────────────────────────────────────────────
class IngestRequest(BaseModel):
    csv_path: Optional[str] = None  # Override default path if provided


class MineRequest(BaseModel):
    min_support: float = 0.1
    min_confidence: float = 0.5


class ChatRequest(BaseModel):
    query: str


class ChatResponse(BaseModel):
    query: str
    answer: str
    source_events: list[str] = []


# ─────────────────────────────────────────────
# Helper: Load CSV and Build FAISS Index
# ─────────────────────────────────────────────
def _load_and_index(csv_path: str) -> int:
    """
    Load forensic logs CSV into memory and build FAISS vector store.

    The RAG pipeline chunks each log row into a LangChain Document,
    so the LLM can retrieve relevant log entries to answer questions.

    Args:
        csv_path: Path to the forensic_logs.csv file

    Returns:
        Number of log rows loaded
    """
    df = pd.read_csv(csv_path)
    app_state["df"] = df

    # Convert each log row into a LangChain Document for retrieval
    documents = []
    for _, row in df.iterrows():
        content = (
            f"[{row['timestamp']}] IP={row['source_ip']} "
            f"Event={row['event_type']} Status={row['status']} "
            f"Detail: {row['description']}"
        )
        documents.append(Document(
            page_content=content,
            metadata={
                "source_ip": str(row["source_ip"]),
                "event_type": str(row["event_type"]),
                "status": str(row["status"]),
                "timestamp": str(row["timestamp"]),
            }
        ))

    # Split documents (in case descriptions are very long)
    splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    split_docs = splitter.split_documents(documents)

    # Build FAISS index with FakeEmbeddings (swap for real embeddings in prod)
    embeddings = FakeEmbeddings()
    vectorstore = FAISS.from_documents(split_docs, embeddings)
    app_state["vectorstore"] = vectorstore
    app_state["retriever"] = vectorstore.as_retriever(search_kwargs={"k": 5})

    # Build Groq LLM instance (Llama 3)
    if GROQ_API_KEY:
        try:
            llm = ChatGroq(api_key=GROQ_API_KEY, model_name=GROQ_MODEL, temperature=0.2)
            app_state["llm"] = llm
            print(f"[CyberGaze] Groq LLM ready: {GROQ_MODEL}")
        except Exception as e:
            print(f"[CyberGaze] WARNING: Groq init failed: {e}")
            app_state["llm"] = None
    else:
        print("[CyberGaze] No GROQ_API_KEY — chat will use mock responses.")
        app_state["llm"] = None

    return len(df)


# ─────────────────────────────────────────────
# Mock LLM fallback (when Ollama is unavailable)
# ─────────────────────────────────────────────
def _mock_chat(query: str, df: pd.DataFrame) -> str:
    """
    Rule-based fallback responder when Ollama is not running.
    Performs simple keyword matching against the loaded DataFrame.
    """
    q = query.lower()
    
    if "failed login" in q or "brute force" in q:
        failed = df[df["event_type"].isin(["Failed Login", "Brute Force"])]
        ips = failed["source_ip"].value_counts()
        return (
            f"Found {len(failed)} failed login / brute force events. "
            f"Top offending IPs: {ips.head(3).to_dict()}"
        )
    elif "exfiltrat" in q:
        exfil = df[df["event_type"] == "Data Exfiltration"]
        return f"Detected {len(exfil)} data exfiltration event(s) from IPs: {exfil['source_ip'].unique().tolist()}"
    elif "malware" in q:
        mal = df[df["event_type"] == "Malware Execution"]
        return f"Detected {len(mal)} malware execution event(s). Details: {mal['description'].tolist()}"
    elif "escalat" in q or "privilege" in q:
        priv = df[df["event_type"] == "Privilege Escalation"]
        return f"Found {len(priv)} privilege escalation attempt(s)."
    elif "scan" in q or "reconnaissance" in q:
        scan = df[df["event_type"] == "Port Scan"]
        return f"Found {len(scan)} port scan event(s) from: {scan['source_ip'].unique().tolist()}"
    elif "lateral" in q:
        lat = df[df["event_type"] == "Lateral Movement"]
        return f"Found {len(lat)} lateral movement event(s)."
    else:
        # General stats
        total = len(df)
        fails = len(df[df["status"] == "Fail"])
        return (
            f"[Mock LLM] Forensic dataset contains {total} events, "
            f"{fails} failures. Top event types: "
            f"{df['event_type'].value_counts().head(3).to_dict()}"
        )


# ─────────────────────────────────────────────
# API Endpoints
# ─────────────────────────────────────────────

@app.get("/health")
async def health_check():
    """Health check endpoint for the AI service."""
    return {
        "status": "online",
        "service": "CyberGaze AI Service",
        "logs_loaded": app_state["df"] is not None,
        "llm_available": app_state["llm"] is not None,
        "llm_backend": f"Groq / {GROQ_MODEL}" if app_state["llm"] else "mock",
    }


@app.get("/logs")
async def get_logs():
    """
    Return all loaded forensic logs as JSON.
    Used by the React IncidentTimeline component.
    """
    if app_state["df"] is None:
        raise HTTPException(status_code=404, detail="No logs loaded. Call POST /ingest first.")
    
    df = app_state["df"]
    return {
        "total": len(df),
        "logs": df.to_dict(orient="records"),
    }


@app.post("/ingest")
async def ingest_logs(request: IngestRequest = None):
    """
    POST /ingest - Load forensic logs CSV and build FAISS vector index.
    
    This is the entry point for log analysis. It:
    1. Reads the CSV file (from .env default or request override)
    2. Converts each log row to a LangChain Document
    3. Builds a FAISS semantic search index
    4. Initializes the Ollama LLM chain for RAG chat

    Returns:
        JSON with count of loaded events and sample entries
    """
    csv_path = (request.csv_path if request else None) or LOG_CSV_PATH

    if not os.path.exists(csv_path):
        raise HTTPException(
            status_code=404,
            detail=f"CSV not found at '{csv_path}'. Run 'python data_gen.py' first."
        )

    try:
        count = _load_and_index(csv_path)
        df = app_state["df"]
        return {
            "status": "success",
            "message": f"Ingested {count} forensic log entries.",
            "csv_path": csv_path,
            "event_types": df["event_type"].value_counts().to_dict(),
            "ip_count": df["source_ip"].nunique(),
            "sample": df.head(3).to_dict(orient="records"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@app.post("/mine")
async def mine_patterns(request: MineRequest = MineRequest()):
    """
    POST /mine - Run FP-Growth association rule mining on loaded logs.

    Discovers attack patterns like:
        "IF [Failed Login:Fail, Port Scan:Success] THEN [Brute Force:Fail]"

    Returns:
        JSON with frequent itemsets, association rules, and threat labels
    """
    if app_state["df"] is None:
        raise HTTPException(status_code=400, detail="No logs loaded. Call POST /ingest first.")

    try:
        result = run_fpgrowth(
            df=app_state["df"],
            min_support=request.min_support,
            min_confidence=request.min_confidence,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Mining failed: {str(e)}")


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    POST /chat - Natural language Q&A about forensic logs using RAG.
    
    Uses LangChain + FAISS to retrieve relevant log entries, then
    Ollama (llama3) to generate a forensic analyst-style answer.
    
    Falls back to mock responses if Ollama is unavailable.

    Example queries:
        - "Show me all failed logins"
        - "Which IP performed lateral movement?"
        - "Summarize the attack timeline"
        - "What data was exfiltrated?"
    """
    if app_state["df"] is None:
        raise HTTPException(status_code=400, detail="No logs loaded. Call POST /ingest first.")

    query = request.query.strip()
    source_events = []

    # Try LLM-based RAG via Groq (Llama 3)
    if app_state["llm"] is not None and app_state["retriever"] is not None:
        try:
            # Step 1: Retrieve relevant log documents from FAISS
            docs = app_state["retriever"].invoke(query)
            source_events = [doc.page_content[:120] for doc in docs[:3]]

            # Step 2: Build context from retrieved docs
            context = "\n".join([doc.page_content for doc in docs])

            # Step 3: Build prompt and invoke Groq Llama 3
            from langchain_core.messages import HumanMessage, SystemMessage
            messages = [
                SystemMessage(content=(
                    "You are an expert Digital Forensics and Incident Response (DFIR) analyst. "
                    "Answer questions based ONLY on the provided security log entries. "
                    "Be concise, precise, and cite specific IPs, timestamps, or event types."
                )),
                HumanMessage(content=f"LOG ENTRIES:\n{context}\n\nANALYST QUESTION: {query}"),
            ]
            response = app_state["llm"].invoke(messages)
            answer = response.content if hasattr(response, 'content') else str(response)

            return ChatResponse(
                query=query,
                answer=answer,
                source_events=source_events,
            )
        except Exception as e:
            print(f"[CyberGaze] LLM error, falling back to mock: {e}")

    # Fallback to rule-based mock response
    answer = _mock_chat(query, app_state["df"])
    return ChatResponse(
        query=query,
        answer=f"[Ollama Offline — Mock Response]\n{answer}",
        source_events=source_events,
    )


# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    print(f"[CyberGaze] Starting AI Service on http://{host}:{port}")
    uvicorn.run("main:app", host=host, port=port, reload=True)
