# Workforce Copilot Platform
## Phased Build Plan for the Okta Senior Software Engineer, Applied AI (Fullstack) Role

## 1. Purpose of This Document

This document breaks the project into clear implementation phases, starting with a practical **MVP in Phase 1**. The plan is intentionally structured so it can be revised later as the project becomes more concrete.

The goal is to keep the roadmap:

- realistic
- interview-relevant
- tightly aligned to the Okta JD
- modular enough to expand or trim later

This is a **working phases plan**, not a fixed contract.

---

## 2. Project Summary

**Project:** Workforce Copilot Platform  
**Type:** Internal AI self-service portal + reusable AI UI/platform layer  
**Primary domain for v1:** IT and HR employee support workflows  

The system will let employees:

- ask policy and process questions
- retrieve grounded answers with citations
- view supporting source snippets
- upload or browse documents
- get summaries of long internal content
- submit feedback on answer quality

The broader long-term goal is to evolve this into a small internal AI platform with reusable components, stronger observability, cloud deployment, and evaluation tooling.

---

## 3. Planning Principles

### Keep the first phase narrow
The first version should be a coherent demoable product, not a scattered technology showcase.

### Add complexity in layers
Each later phase should deepen one dimension of the system rather than changing everything at once.

### Prefer believable engineering over feature inflation
A smaller but well-structured system is better than an oversized app with weak foundations.

### Preserve flexibility
This roadmap should be easy to reorder, merge, or trim later.

---

## 4. Overall Phase Sequence

| Phase | Name | Main Goal |
|---|---|---|
| 1 | MVP | Ship a working employee copilot with document-grounded answers |
| 2 | RAG + Data Foundations | Strengthen preprocessing, retrieval quality, and source handling |
| 3 | Platform Layer | Add reusable UI/hooks and cleaner backend service boundaries |
| 4 | Reliability + Operations | Add observability, async processing, and operational discipline |
| 5 | Cloud Deployment | Deploy to AWS with production-style service infrastructure |
| 6 | Evaluation + Quality | Add evaluation workflows and systematic answer measurement |
| 7 | Stretch / Optional | Add advanced integrations, providers, and orchestration expansions |

---

## 5. Phase 1 — MVP

## Goal
Build a working internal copilot for IT and HR questions that returns grounded answers with citations.

## Why this is the first phase
This phase creates the smallest complete version of the product while still touching the most important JD signals:

- React + TypeScript UI
- Python backend
- LLM integration
- basic RAG
- citations
- document ingestion
- Docker-based local execution

## User story for Phase 1
An employee can open the portal, ask a question about a policy or workflow, and receive a grounded answer that references uploaded internal documents.

## In scope

### Frontend
- React + TypeScript app
- single workspace UI for IT/HR assistant
- chat view
- answer card with citations
- source drawer or side panel
- basic conversation history for current session

### Backend
- FastAPI service
- endpoint for chat query submission
- endpoint for document upload
- endpoint for retrieving answer/source details
- basic persistence for documents, chunks, and runs

### LLM integration
- one active model provider, preferably OpenAI
- simple orchestration flow for retrieval + answer generation

### RAG
- upload document
- parse document
- normalize extracted text
- chunk text
- attach metadata
- generate embeddings
- store embeddings in vector store
- retrieve relevant chunks for answering
- return cited sources with answer

### Data/storage
- PostgreSQL for app data and run metadata
- local file storage or S3-compatible abstraction for uploaded docs
- FAISS locally or Qdrant if setup remains manageable

### Security
- basic auth layer or mocked internal user context
- minimal access scoping approach for documents

### Dev experience
- Docker Compose local setup
- sample seed documents
- `.env`-based local configuration
- health and readiness endpoints

## Explicit Phase 1 RAG preprocessing pipeline
This should be implemented in Phase 1, even in simple form.

1. Accept uploaded file
2. Parse file into text
3. Clean and normalize text
4. Split into chunks
5. Attach metadata to each chunk
6. Generate embeddings
7. Persist chunk records and vector entries
8. Make chunks retrievable for answer generation

## Deliverables
- working web UI
- working FastAPI API
- document upload flow
- retrieval-backed question answering
- citations rendered in UI
- basic schema for documents, chunks, runs, and feedback placeholders
- Dockerized local run
- short README with setup + demo steps

## Success criteria / exit criteria
Phase 1 is complete when all of the following are true:

- a user can upload one or more policy/process documents
- the system can answer at least a small set of grounded document questions
- the UI shows the supporting chunks or citations used
- the app runs locally through Docker without manual patchwork
- the architecture is clean enough to extend in later phases

## Out of scope for Phase 1
- multi-provider model routing
- advanced reranking
- reusable component package extraction
- async ingestion workers
- Prometheus/Grafana
- AWS deployment
- evaluation harness
- EKS or Kubernetes

---

## 6. Phase 2 — RAG + Data Foundations

## Goal
Make the retrieval pipeline more explicit, more reliable, and more explainable.

## Why this phase comes next
Phase 1 proves the product. Phase 2 makes the core knowledge pipeline stronger so later platform and reliability work rests on something real.

## In scope

### Preprocessing improvements
- better text normalization
- document-type-aware parsing rules
- heading-aware or section-aware chunking
- chunk-size experiments
- overlap strategy
- metadata enrichment
- ingestion status tracking

### Retrieval improvements
- metadata filtering
- workspace/domain filtering
- top-k tuning
- optional reranking layer
- retrieval debug output for inspection

### Source handling improvements
- stronger citation formatting
- chunk lineage and source labels
- answer run linking to exact retrieved chunks
- support/support-gap indicators in response payload

### Data model improvements
- more explicit ingestion job records
- chunk status fields
- retrieval trace metadata
- cleaner source references

## Deliverables
- improved preprocessing pipeline
- improved chunk metadata schema
- more inspectable retrieval results
- better citation/source rendering in the UI
- small retrieval test set for sanity checking

## Success criteria / exit criteria
- chunking strategy is documented and intentional
- retrieval quality is noticeably more stable than MVP baseline
- each answer run can be tied back to retrieved chunks clearly
- preprocessing is no longer an implied step; it is a visible subsystem

## Out of scope
- reusable frontend package publication
- full observability stack
- cloud deployment
- broad eval harness

---

## 7. Phase 3 — Platform Layer

## Goal
Turn the system from one application into a mini internal AI platform.

## Why this phase matters
The JD is not only about building an app. It also points toward reusable AI capabilities that other internal tools could adopt.

## In scope

### Frontend platformization
- extract shared UI into `copilot-ui`
- extract shared hooks into `copilot-hooks`
- create typed API client layer
- standardize answer, citation, and feedback patterns

### Backend platformization
- cleaner service boundaries between:
  - API/app service
  - ingestion service
  - retrieval service
  - orchestration service
- provider abstraction layer
- optional LangChain-based orchestration flows
- cleaner request/response contracts

### Product features
- answer history view
- run trace view
- feedback capture
- role-aware document access patterns
- workspace-aware configuration

## Deliverables
- reusable component library
- reusable hooks layer
- provider abstraction interface
- cleaner internal module/service boundaries
- richer product flows around answers and runs

## Success criteria / exit criteria
- at least a few AI UI patterns are reusable across screens
- model/provider swap is possible without major rewrites
- platform concepts are visible in the repository structure
- the system no longer feels like a one-off demo

## Out of scope
- AWS production deployment
- formal SLO dashboards
- large evaluation framework

---

## 8. Phase 4 — Reliability + Operations

## Goal
Add senior-level production discipline.

## Why this phase matters
This is where the project starts resembling a real internal platform rather than a prototype.

## In scope

### Async and worker model
- background ingestion worker
- retry-safe ingestion jobs
- queue-backed processing with Redis or similar
- idempotent document indexing behavior

### Observability
- metrics for request count, error rate, latency, retrieval latency, ingestion duration
- health and readiness signals
- structured logs
- dashboard plan or implementation

### Operational artifacts
- failure mode matrix
- degraded-mode behavior
- simple incident runbook
- service dependency notes

### Reliability behaviors
- timeout handling
- fallback handling for retrieval failure
- graceful error messaging in UI
- retry patterns where appropriate

## Deliverables
- worker-based ingestion path
- metrics instrumentation
- dashboard(s)
- structured logging
- reliability notes/runbook

## Success criteria / exit criteria
- ingestion no longer blocks the main app flow
- service behavior is observable through metrics/logs
- common failure modes are identified and at least partially handled
- the project supports a stronger operational narrative in interviews

## Out of scope
- full production hardening
- autoscaling
- complete enterprise security model

---

## 9. Phase 5 — Cloud Deployment

## Goal
Deploy the application to AWS using production-style service structure.

## Why this phase matters
The JD includes AWS, Docker, and cloud services. A deployed version makes that experience concrete.

## In scope

### Deployment target
- AWS ECS as the main deployment path
- ECR for images
- RDS PostgreSQL
- S3 for document storage
- ALB or similar ingress layer
- CloudWatch logs
- Secrets Manager or Parameter Store

### Delivery and configuration
- environment-specific configs
- container image build flow
- basic deployment documentation
- local vs cloud config separation

### Optional IaC direction
- Terraform later if desired
- infrastructure folder structure from the start

## Deliverables
- deployed cloud version
- environment configuration strategy
- deployment notes
- diagrams showing runtime architecture

## Success criteria / exit criteria
- the system is reachable in a deployed environment
- uploaded docs and app data persist across service restarts
- logs and config management are not hard-coded or manual
- the deployment story is something you can discuss clearly in interviews

## Out of scope
- EKS unless deliberately added later
- advanced autoscaling
- multi-region deployment

---

## 10. Phase 6 — Evaluation + Quality

## Goal
Add measurement and iteration loops for answer quality and retrieval quality.

## Why this phase matters
Applied AI teams increasingly care about evidence, testing, and iteration rather than raw demo quality.

## In scope

### Evaluation assets
- small curated eval dataset
- representative prompt set
- expected source/relevance cases
- regression cases for known failure modes

### Retrieval evaluation
- retrieved-chunk relevance checks
- empty-retrieval tracking
- citation coverage checks

### Answer quality evaluation
- groundedness checks
- answer usefulness checks
- provider comparison runs
- prompt/version comparison runs

### Product feedback loop
- connect user feedback to eval review
- tag low-quality answers for inspection
- basic scorecard or quality dashboard

## Deliverables
- lightweight eval harness
- evaluation dataset
- result summaries
- quality scorecard

## Success criteria / exit criteria
- system changes can be tested against a known baseline
- quality discussions are evidence-based rather than anecdotal
- the project supports a stronger AI-systems engineering narrative

## Out of scope
- large-scale automated benchmarking
- enterprise eval platform complexity

---

## 11. Phase 7 — Stretch / Optional

## Goal
Add selected advanced capabilities only after the core platform is already coherent.

## Possible additions
- Claude and Gemini live providers
- Pinecone adapter
- streaming responses
- tool calling for ticket drafting or request generation
- admin analytics dashboard
- EKS deployment variant
- frontend performance monitoring
- more advanced workspace/domain separation

## Rule for this phase
Do not start here. Only pull from this phase when earlier phases are already stable.

---

## 12. Recommended First Build Slice

Before thinking about the whole roadmap, start with this narrow slice:

### Initial slice
- one workspace: IT + HR
- one provider: OpenAI
- one retrieval path
- one upload flow
- one answer UI with citations
- one or two sample corpora

### First realistic demo
A user uploads policy/process documents, asks a question, and receives a grounded answer with source snippets.

That alone is enough to justify the project and begin building resume/interview material.

---

## 13. Suggested Milestone Order Inside Phase 1

### Milestone 1
- repo setup
- frontend and backend skeletons
- Docker Compose
- PostgreSQL connection
- basic chat page shell

### Milestone 2
- document upload
- document parsing
- chunk creation
- metadata persistence

### Milestone 3
- embeddings generation
- vector storage
- retrieval endpoint

### Milestone 4
- answer generation with retrieved chunks
- citation payload
- UI citation display

### Milestone 5
- basic auth/user context
- run persistence
- health/readiness endpoints
- README + demo prep

---

## 14. What This Plan Gives You for the Okta Role

This roadmap gives you a project that can credibly demonstrate:

- full-stack GenAI application development
- Python backend engineering
- React and TypeScript product UI work
- RAG preprocessing and retrieval design
- LangChain and/or LlamaIndex usage
- vector search concepts and tooling
- reusable UI components and hooks
- observability and operational thinking
- AWS and Docker deployment experience
- trust, provenance, and governance thinking in AI systems

---

## 15. Practical Recommendation

Treat **Phase 1** as the non-negotiable core.

Everything after that should be viewed as controlled expansion, not required scope. That will keep the project buildable, believable, and useful in interviews even before it is fully mature.

---

## 16. Revision Notes for Later

When revisiting this plan later, likely edit points will be:

- whether Phase 2 and Phase 3 should be merged
- whether Qdrant belongs in Phase 1 or Phase 2
- whether LangChain starts in Phase 1 or is deferred
- whether auth should be basic, mocked, or real in MVP
- whether AWS deployment should move earlier
- whether evaluation should begin with a tiny baseline in Phase 2

This is expected. The roadmap is meant to evolve.

---

*Last updated: March 21, 2026*
