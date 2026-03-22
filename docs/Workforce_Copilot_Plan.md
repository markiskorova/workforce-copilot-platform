# Workforce Copilot Platform
## Project Plan for the Okta Senior Software Engineer, Applied AI (Fullstack) Role

## 1. Project Summary

**Project name:** Workforce Copilot Platform  
**Type:** Internal AI self-service portal + reusable AI component SDK  
**Primary use case:** Employee-facing assistant for IT and HR workflows, grounded in internal documents and operational data  

This project is designed to mirror the kind of applied AI systems described in the Okta job description: **user-facing GenAI applications**, **backend orchestration**, **internal RAG services**, **AI copilots**, and **AI-augmented self-service portals** used by internal teams. It also deliberately includes a **reusable frontend component layer** so the project is not just one application, but a mini internal AI platform.

The goal is to build a portfolio-quality system that gives direct experience with the technologies and engineering concerns named in the JD, while also extending the kinds of applied AI systems already present in Marc McAllister’s recent work.

---

## 2. Why This Project Fits the Role

The Okta role emphasizes:

- End-to-end GenAI applications with **web UIs**, **API services**, and **backend orchestration**
- **Python** backend development
- **React** and **TypeScript** frontend work
- **LLM integration** using frameworks such as **LangChain** and **LlamaIndex**
- **RAG pipelines** with **vector search** and embedding strategies
- **AWS**, **Docker**, **REST APIs**, and distributed/cloud services
- Operational excellence, including **SLOs**, **observability**, and incident readiness
- Security, privacy, and internal governance
- Reusable UI components and hooks that let other internal teams drop AI into their own apps

This project maps directly to those requirements by combining:

1. A real employee-facing AI portal
2. A Python orchestration backend
3. A RAG ingestion and retrieval system
4. A reusable React component library for AI UI patterns
5. Cloud deployment and monitoring foundations

---

## 3. Product Vision

Build an internal portal where employees can:

- Ask policy and workflow questions
- Receive grounded answers with citations
- Search and summarize internal documents
- Use guided actions such as drafting tickets or requests
- View answer provenance and supporting source snippets
- Submit feedback on answer quality
- Access the same AI capabilities through reusable UI widgets that could later be embedded into other enterprise applications

### Example user flows

#### IT Help Flow
An employee asks:
> “How do I request access to the finance sandbox?”

The system retrieves relevant internal docs, policy pages, and service articles, then produces a cited answer with next steps and a link to the appropriate request workflow.

#### HR Policy Flow
An employee asks:
> “What is the PTO carryover policy for California employees?”

The system returns a grounded response with citations, highlights the exact policy section, and shows the related document metadata.

#### Summarization Flow
An employee uploads or selects a long policy document and asks for:
- a summary
- key requirements
- decision points
- action checklist

#### Guided Action Flow
After answering a question, the assistant can generate:
- a draft help ticket
- a request summary
- a checklist of required steps

---

## 4. Core Design Principle

Do not build a generic chatbot.

Build a **trusted internal AI application platform** with:

- grounded answers
- explainable outputs
- reusable UI patterns
- security-minded service design
- measurable reliability
- clean engineering boundaries

That is much closer to what Okta is actually hiring for.

---

## 5. JD Technology Coverage Map

| JD Signal | How this project covers it |
|---|---|
| Python | FastAPI orchestration backend, ingestion service, evaluation service |
| React / TypeScript | Main portal UI plus reusable AI component library |
| REST APIs | Versioned backend endpoints for chat, documents, feedback, and health |
| AWS | ECS deployment, RDS, S3, CloudWatch, Secrets Manager |
| Docker | Containerized API, worker, and frontend services |
| LangChain | Tool routing, agent workflows, prompt orchestration |
| LlamaIndex | Document ingestion, indexing, retrieval pipeline assembly |
| OpenAI / Claude / Gemini | Provider abstraction layer for multi-model support |
| RAG | Chunking, embeddings, vector search, reranking, citations |
| Pinecone / FAISS / Qdrant | Local FAISS for dev, Qdrant for main system, optional Pinecone adapter |
| Distributed systems / microservices | API service, ingestion worker, retrieval service, evaluation worker |
| ECS / EKS | ECS first; EKS as stretch goal |
| Security / auth | JWT or OAuth, RBAC, audit logs, document access boundaries |
| Observability / SLOs | Metrics, dashboards, health checks, latency/error budgets |
| UI trust patterns | Citations, answer trace, source drawer, feedback controls |
| Reusable frontend hooks/components | `PromptBox`, `AnswerCard`, `CitationDrawer`, `useCopilotQuery`, `useFeedback` |
| AI evaluation tooling | Offline eval dataset, retrieval checks, answer grading workflows |
| Performance monitoring | Frontend and API latency instrumentation |

---

## 6. Recommended Technical Architecture

## 6.1 Frontend

**Stack:** React + TypeScript  
**Suggested UI approach:** minimal component system with accessible patterns, clean enterprise styling  

### Major screens

- Home / workspace selector
- Chat / copilot screen
- Document viewer with cited chunks
- Answer history view
- Feedback / annotation panel
- Admin or ingestion status screen

### Reusable component library

Create a local package such as:

- `packages/copilot-ui`
- `packages/copilot-hooks`

### Core components

- `PromptBox`
- `AnswerCard`
- `CitationDrawer`
- `SourceSnippetCard`
- `ToolExecutionPanel`
- `FeedbackWidget`
- `GroundedResponse`
- `ModelSelector`
- `TrustIndicator`

### Core hooks

- `useCopilotQuery`
- `useDocumentSearch`
- `useFeedback`
- `useConversationRuns`
- `useSourceCitations`

This part is especially important because it gives direct experience with the JD’s “reusable frontend components and hooks” requirement.

---

## 6.2 Backend

**Stack:** Python + FastAPI  

### Service responsibilities

#### API Gateway / App Service
Handles:
- authentication context
- request routing
- conversation storage
- response delivery
- feedback submission

#### Orchestration Service
Handles:
- prompt assembly
- model/provider selection
- LangChain workflows
- tool calls
- citation packaging

#### Ingestion Service
Handles:
- file upload processing
- parsing
- chunking
- metadata extraction
- embedding generation
- vector store writes

#### Retrieval Service
Handles:
- vector search
- metadata filtering
- reranking
- source chunk packaging

#### Evaluation Worker
Handles:
- retrieval evaluation
- answer quality checks
- prompt regression tests
- model comparison experiments

### Suggested REST endpoints

- `POST /api/v1/chat/query`
- `GET /api/v1/chat/runs/{id}`
- `POST /api/v1/documents/upload`
- `POST /api/v1/ingestion/run`
- `GET /api/v1/documents/{id}`
- `POST /api/v1/feedback`
- `GET /healthz`
- `GET /readyz`
- `GET /metrics`

---

## 6.3 LLM and Orchestration Layer

Use both named frameworks intentionally.

### LangChain
Use for:
- tool calling
- workflow orchestration
- provider abstraction
- prompt templates
- chain composition

### LlamaIndex
Use for:
- ingestion pipelines
- indexing
- retrieval workflow assembly
- structured source node handling

### Model providers
Build a provider interface that supports:
- OpenAI
- Claude
- Gemini

Even if only one provider is fully active in the MVP, the abstraction layer itself is good experience and gives a stronger systems-design story.

---

## 6.4 RAG Layer

### Retrieval pipeline

1. Upload document
2. Parse and normalize
3. Chunk document
4. Attach metadata
5. Generate embeddings
6. Store vectors and source metadata
7. Retrieve top-k relevant chunks
8. Optionally rerank results
9. Package citations into response
10. Render citations in UI

### Document types for MVP

- Markdown
- PDF
- plain text
- HTML
- CSV or simple tabular content later

### Chunk metadata

Each stored chunk should include:

- document ID
- title
- section or heading
- chunk index
- character range
- source URI or file reference
- access scope
- ingestion timestamp

### Retrieval output format

Return:
- answer text
- supporting chunk list
- confidence or support metadata
- cited source labels
- answer run ID

### Vector store plan

- **Local dev:** FAISS
- **Main app:** Qdrant
- **Stretch adapter:** Pinecone

That gives broad coverage without overcomplicating the first version.

---

## 6.5 Data and Storage

### PostgreSQL
Use for:
- users
- sessions
- conversations
- answer runs
- documents
- chunk metadata
- feedback
- audit logs
- evaluation results

### S3
Use for:
- uploaded source files
- original documents
- derived artifacts if needed

### Redis
Use for:
- task queues
- cache
- rate limiting support

---

## 6.6 Infrastructure and Deployment

### Recommended deployment path

#### Initial cloud target
Use **AWS ECS**.

This is the most practical way to get cloud/container experience aligned to the JD without taking on unnecessary Kubernetes overhead too early.

### AWS services

- ECS for services
- ECR for container images
- RDS PostgreSQL
- S3 for documents
- CloudWatch for logs and alarms
- Secrets Manager or SSM Parameter Store
- ALB for ingress

### Stretch goal
Add a basic **EKS deployment path** later if you want explicit container orchestration exposure beyond ECS.

---

## 7. Security and Governance Plan

The JD explicitly emphasizes security, privacy, observability, and internal governance. This project should reflect that from the beginning.

### Security features

- JWT or OAuth-based auth
- role-based access control
- document access scoping
- request validation
- rate limiting
- safe secret handling
- audit logging for queries and document access

### Governance features

- source citation requirement for grounded answers
- answer traceability via run IDs
- configurable system prompts per workspace
- document tagging by domain and sensitivity
- explicit separation between retrieved facts and generated summaries

### Trust UX features

- “Sources used” panel
- cited snippets
- answer support indicators
- user feedback buttons
- clear fallback when evidence is weak

---

## 8. Observability and Reliability Plan

This is one of the most important senior-level signals in the project.

### Health and readiness

- `/healthz`
- `/readyz`

### Metrics to instrument

- request count
- error rate
- API latency
- retrieval latency
- embedding job duration
- queue depth
- model invocation latency
- citation count per answer
- empty-retrieval frequency

### Dashboards

Use Prometheus + Grafana or CloudWatch dashboards to track:

- throughput
- p95 latency
- failure rate
- worker backlog
- retrieval quality indicators

### SLO examples

- 99% of chat requests complete successfully
- p95 API latency under target threshold
- ingestion jobs complete within agreed time window
- retrieval returns at least one supporting chunk for eligible grounded queries

### Incident-readiness artifacts

- basic runbook
- alert definitions
- failure mode matrix
- degraded mode behavior

---

## 9. Suggested Data Model

### Tables / entities

#### users
- id
- email
- role
- created_at

#### workspaces
- id
- name
- domain_type
- created_at

#### documents
- id
- workspace_id
- title
- source_type
- storage_uri
- access_scope
- uploaded_at

#### chunks
- id
- document_id
- chunk_index
- content
- metadata_json
- embedding_status

#### conversations
- id
- user_id
- workspace_id
- created_at

#### runs
- id
- conversation_id
- prompt_text
- model_name
- status
- latency_ms
- created_at

#### citations
- id
- run_id
- chunk_id
- rank

#### feedback
- id
- run_id
- user_id
- rating
- comments
- created_at

#### audit_logs
- id
- actor_id
- action_type
- resource_type
- resource_id
- created_at

#### eval_results
- id
- eval_suite_name
- run_id
- metric_name
- metric_value
- recorded_at

---

## 10. Recommended Build Phases

## Phase 1: Foundation MVP

### Goal
Ship a working employee copilot with grounded answers.

### Deliverables
- React + TypeScript chat UI
- FastAPI backend
- OpenAI integration
- LlamaIndex ingestion flow
- FAISS or Qdrant retrieval
- document upload
- citations in answer view
- PostgreSQL persistence
- Docker local setup
- basic auth
- `/healthz` and `/readyz`

### Outcome
You can demo a real end-to-end AI application.

---

## Phase 2: Platformization

### Goal
Turn the app into an internal AI platform rather than a one-off chatbot.

### Deliverables
- reusable component library
- reusable frontend hooks
- LangChain orchestration flows
- provider abstraction layer
- Qdrant-based retrieval service
- metadata filtering
- answer history and run trace views
- feedback capture
- role-aware document access

### Outcome
You can show platform thinking and front-end reuse, both strong matches for the JD.

---

## Phase 3: Reliability and Operations

### Goal
Demonstrate senior-level production discipline.

### Deliverables
- Prometheus metrics
- Grafana dashboards
- queue-backed ingestion workers
- retry-safe job handling
- SLO definitions
- alerting outline
- incident runbook
- audit logging

### Outcome
You can talk credibly about observability, SLOs, and operational excellence.

---

## Phase 4: Cloud Deployment

### Goal
Deploy a cloud-backed version aligned to the JD.

### Deliverables
- AWS ECS deployment
- ECR images
- RDS PostgreSQL
- S3 file storage
- CloudWatch logs
- Secrets Manager integration
- environment-specific configs

### Outcome
You can speak concretely about AWS, Docker, and scalable deployment.

---

## Phase 5: Evaluation and Quality

### Goal
Add the trust and measurement layer that strong applied-AI teams care about.

### Deliverables
- small evaluation dataset
- retrieval relevance checks
- grounded-answer regression tests
- model/provider comparison runs
- feedback-to-eval loop
- answer quality scorecard

### Outcome
You can discuss AI evaluation tooling and measured iteration, which is a bonus area in the JD.

---

## Phase 6: Stretch Goals

### Optional additions
- Pinecone adapter
- Gemini and Claude live providers
- EKS deployment variant
- frontend performance monitoring
- streaming responses
- admin analytics dashboard
- tool integrations for ticket drafting or request creation

---

## 11. What to Build First

The best first slice is:

1. Single workspace: **IT + HR assistant**
2. Single document corpus: policy pages and process docs
3. Single model provider: OpenAI
4. Single vector store: FAISS locally, Qdrant next
5. Single UI experience: chat + citations + source drawer

That will keep the project coherent while still touching the most important skills.

---

## 12. Suggested Repository Structure

```text
workforce-copilot-platform/
  apps/
    web/
    api/
    worker/
  packages/
    copilot-ui/
    copilot-hooks/
    shared-types/
  infrastructure/
    docker/
    aws/
  docs/
    architecture/
    runbooks/
    api/
  data/
    sample-docs/
  scripts/
```

---

## 13. Suggested API Surface

### Chat
- `POST /api/v1/chat/query`
- `GET /api/v1/chat/runs/{id}`
- `GET /api/v1/chat/conversations/{id}`

### Documents
- `POST /api/v1/documents/upload`
- `GET /api/v1/documents/{id}`
- `POST /api/v1/documents/{id}/reindex`

### Retrieval / Sources
- `GET /api/v1/runs/{id}/sources`
- `GET /api/v1/documents/{id}/chunks`

### Feedback / Eval
- `POST /api/v1/feedback`
- `GET /api/v1/evals/summary`

### Ops
- `GET /healthz`
- `GET /readyz`
- `GET /metrics`

---

## 14. Interview Value of This Project

This project will let Marc say:

- I built a full-stack GenAI application using **Python**, **React**, and **TypeScript**.
- I implemented a real **RAG pipeline** with chunking, embeddings, vector retrieval, and citations.
- I used **LangChain** for orchestration and **LlamaIndex** for ingestion and retrieval workflows.
- I built a **reusable frontend component and hooks library** so AI patterns could be embedded in multiple applications.
- I deployed the system with **Docker** and **AWS**.
- I added **observability**, **health checks**, **metrics**, and **SLO-oriented thinking**.
- I treated trust, security, and explainability as product requirements, not afterthoughts.

That is a much stronger story for this role than a narrow toy chatbot or a generic side project.

---

## 15. How This Extends Existing Experience

This project is especially good because it builds naturally on existing strengths already reflected in Marc’s current resume:

- Python and React/TypeScript applied AI work
- structured outputs and provenance-linked workflows
- limited retrieval-augmented analysis baseline
- API + worker patterns
- JWT/OAuth-style security foundations
- Docker and AWS exposure
- Prometheus / Grafana observability foundations

Instead of inventing a totally new persona, this project deepens the current applied-AI and full-stack story in the exact direction the Okta role wants.

---

## 16. Resume / Portfolio Positioning

When complete, this can appear as:

### Workforce Copilot Platform — Python + React + TypeScript + AWS
Built an internal AI self-service portal and reusable copilot UI toolkit for grounded employee support workflows. Implemented document ingestion, vector retrieval, LLM orchestration, cited answers, reusable frontend hooks/components, observability, and cloud-ready deployment foundations.

### Possible bullet themes
- End-to-end GenAI application architecture
- RAG and vector search implementation
- reusable AI UI patterns
- operational excellence and monitoring
- internal-tool security and trust design

---

## 17. Practical Recommendation

Do not try to show every technology on day one.

Use this order:

1. **Working product**
2. **Reusable platform layer**
3. **Reliability layer**
4. **Cloud deployment layer**
5. **Evaluation layer**

That sequence will produce the strongest portfolio artifact and the most believable interview narrative.

---

## 18. Final Recommendation

Build **Workforce Copilot Platform** as an internal AI self-service portal for IT and HR workflows, backed by a Python orchestration service, RAG retrieval layer, reusable React/TypeScript AI components, and AWS deployment foundations.

This is the single best project choice for gaining relevant experience across the technologies named in the Okta JD while staying tightly aligned to the actual product and engineering problems the role appears to target.

---

*Last updated: March 21, 2026*
