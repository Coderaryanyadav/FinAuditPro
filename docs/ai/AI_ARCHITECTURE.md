# FinAuditPro — Local AI Copilot Architecture

## 1. Offline Execution Architecture
FinAuditPro connects to local LLMs running via LM Studio or Ollama on `127.0.0.1:1234` with zero cloud egress.

```
[PyQt6 UI Assistant Drawer]
             │
             ▼
[Prompt Defense & AST Sanitizer]
             │
             ▼
[Local RAG Engine (FTS5 Store of ICAI SAs, CARO 2020, Form 3CD)]
             │
             ▼
[Localhost LM Studio (127.0.0.1:1234)]
             │
             ▼
[Streamed Markdown Citation & Guidance]
```
