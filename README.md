# 🛡️ CyberGaze — CORTEX DFIR Command Center

A **closed-loop Digital Forensics and Incident Response (DFIR)** prototype with three microservices working together:

| Service | Stack | Port |
|---------|-------|------|
| **AI & Mining Engine** | Python · FastAPI · LangChain · Ollama | `8000` |
| **Core Commander** | Java · Spring Boot | `8080` |
| **Dashboard** | React · Vite · Tailwind CSS | `5173` |

---

## 🗂️ Project Structure

```
CyberGaze/
├── ai-service/          # Python FastAPI — log ingestion, FP-Growth mining, RAG chat
│   ├── main.py
│   ├── mining_engine.py
│   ├── data_gen.py
│   ├── requirements.txt
│   └── .env
├── core-system/         # Java Spring Boot — Panic Button + NIST playbooks
│   ├── pom.xml
│   └── src/main/java/com/cybergaze/
│       ├── CyberGazeApplication.java
│       ├── controller/IncidentController.java
│       └── service/PlaybookService.java
├── dashboard/           # React + Vite — Dashboard UI
│   ├── src/
│   │   ├── App.jsx
│   │   └── components/
│   │       ├── ForensicChat.jsx
│   │       ├── IncidentTimeline.jsx
│   │       └── PanicButton.jsx
│   └── package.json
└── README.md
```

---

## 🚀 Quick Start (3 Terminals)

### Prerequisites
- **Python 3.11+** with pip
- **Java 17+** with Maven 3.9+
- **Node.js 20+** with npm
- **Ollama** (optional — app works without it using mock responses)
  - Install: https://ollama.com
  - Pull model: `ollama pull llama3`

---

### Terminal 1 — Python AI Service

```powershell
cd CyberGaze\ai-service

# Install dependencies
pip install -r requirements.txt

# Generate the forensic log dataset (creates forensic_logs.csv)
python data_gen.py

# Start the FastAPI server (auto-ingest happens on startup)
python main.py
```

> Server runs at **http://localhost:8000**  
> Docs available at **http://localhost:8000/docs**

---

### Terminal 2 — Java Core Commander

```powershell
cd CyberGaze\core-system

# Build and run with Maven
mvn spring-boot:run
```

> Server runs at **http://localhost:8080**  
> Health check: **http://localhost:8080/api/commander/health**

---

### Terminal 3 — React Dashboard

```powershell
cd CyberGaze\dashboard

# Install npm dependencies
npm install

# Start the Vite dev server
npm run dev
```

> Dashboard runs at **http://localhost:5173**

---

## 🔌 API Reference

### Python AI Service (`http://localhost:8000`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/health` | Service status |
| `GET`  | `/logs`   | Return all loaded log entries |
| `POST` | `/ingest` | Load `forensic_logs.csv` into FAISS vector store |
| `POST` | `/mine`   | Run FP-Growth pattern mining |
| `POST` | `/chat`   | RAG-based natural language Q&A |

**Example — Mine patterns:**
```bash
curl -X POST http://localhost:8000/mine \
  -H "Content-Type: application/json" \
  -d '{"min_support": 0.1, "min_confidence": 0.3}'
```

**Example — Chat:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me all failed logins"}'
```

### Java Core Commander (`http://localhost:8080`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/api/commander/health` | Service health |
| `POST` | `/api/commander/trigger-response` | Trigger NIST playbook |
| `GET`  | `/api/commander/threat-levels` | Threat level scale |

**Example — Trigger panic button:**
```bash
curl -X POST http://localhost:8080/api/commander/trigger-response \
  -H "Content-Type: application/json" \
  -d '{"threatLevel": 8, "description": "Ransomware on FINANCE-PC-001"}'
```

---

## 🧠 How It Works

### FP-Growth Pattern Mining
1. Logs grouped by `source_ip` → each IP forms a "transaction" of events it triggered
2. FP-Growth finds frequent itemsets (e.g., `{Failed Login, Port Scan}`)
3. Association rules generated: `IF [Failed Login:Fail] THEN [Brute Force:Fail]`
4. Rules labeled with MITRE ATT&CK-inspired threat categories

### RAG Chat Pipeline
1. Each log row is converted to a LangChain `Document`
2. FAISS vector index built from embeddings
3. User query → FAISS retrieves top-5 relevant log entries
4. Ollama (llama3) generates analyst-style answer from retrieved context

### NIST SP 800-61 Playbook
- Threat level 1–3 → **LOW** (monitoring, log review)
- Threat level 4–6 → **MEDIUM** (block ports, reset credentials)
- Threat level 7–9 → **HIGH** (isolate subnet, preserve forensics)
- Threat level 10 → **CRITICAL** (full emergency protocol, notify CISO)

---

## 🔧 Troubleshooting

| Issue | Fix |
|-------|-----|
| `forensic_logs.csv not found` | Run `python data_gen.py` in `ai-service/` |
| Ollama chat returns mock response | Start Ollama: `ollama serve` + `ollama pull llama3` |
| CORS error in browser | Ensure all 3 services are running |
| Java build fails | Ensure Java 17+ and Maven 3.9+ are installed |
| `faiss-cpu` install fails | Try `pip install faiss-cpu --no-cache-dir` |

---

## ⚙️ Configuration

Edit `ai-service/.env` to change defaults:
```env
OLLAMA_MODEL=llama3        # Change to llama2, mistral, etc.
MIN_SUPPORT=0.1            # FP-Growth sensitivity
PORT=8000
```

Edit `core-system/src/main/resources/application.properties` for Java:
```properties
server.port=8080
```
