# Phase 1 Checklist

## Purpose
This document breaks Phase 1 (MVP) into smaller, practical implementation parts so the project can be built incrementally without losing the end-to-end goal.

Phase 1 remains the same MVP described in the existing planning docs:

- one workspace for IT and HR questions
- one model provider
- one upload flow
- one retrieval path
- grounded answers with citations
- lightweight base versioning for uploaded content and retrieval state
- local Docker-based development setup

## MVP Slice Decisions
To keep the first version narrow and achievable, use these defaults:

- workspace: single IT + HR assistant
- model provider: OpenAI
- vector store: FAISS for local MVP
- base versioning: immutable `document_versions`, not full corpus snapshots
- index versioning: one active local `index_version` for retrieval
- auth: mocked or minimal internal user context
- storage: PostgreSQL for metadata plus local file storage
- document scope: one or two supported formats at first

## Versioning and Indexing Approach
Phase 1 should include lightweight version-awareness so ingestion and retrieval are traceable without overcomplicating the MVP.

- `documents` represent stable logical source records
- each upload or reindex creates an immutable `document_version`
- `chunks` should belong to a `document_version`
- retrieval should use one active local `index_version`
- answer runs should record which `index_version` served the response once retrieval is implemented
- full corpus snapshots and rollback flows stay out of scope for MVP

## Recommended Build Order

## Part 1 - Foundation and Repo Scaffolding
Set up the base application structure and local development flow.

Checklist:
- [x] create `apps/web`
- [x] create `apps/api`
- [x] add shared environment configuration
- [x] add `.env.example`
- [x] add Docker Compose for web, api, and postgres
- [x] add a placeholder chat page shell
- [x] add `GET /healthz`
- [x] add `GET /readyz`

Definition of done:
- [x] web and api start locally
- [x] postgres runs through Docker Compose
- [x] the web app can reach the api

## Part 2 - Data Model and Persistence
Create the minimum database structure needed for document ingestion and chat runs.

Checklist:
- [x] add schema for `documents`
- [x] add schema for `chunks`
- [x] add schema for `runs`
- [x] optionally add schema for `conversations`
- [x] add migration setup
- [x] connect api to PostgreSQL

Definition of done:
- [x] the api can create and read core records
- [x] document and run metadata persist correctly

Versioning follow-up before Part 3:
- [x] add schema for `document_versions`
- [x] move chunks to reference `document_version` rather than only the logical document
- [x] reserve an `index_versions` concept for retrieval builds

## Part 3 - Document Upload and Parsing
Implement the first usable ingestion entry point.

Checklist:
- [x] add `POST /api/v1/documents/upload`
- [x] create or update the logical `document` record
- [x] create an immutable `document_version` for each upload or reindex
- [x] store uploaded files locally
- [x] parse supported documents into text
- [x] normalize extracted text
- [x] save document version metadata, content hash, and raw extracted content references

Definition of done:
- [x] a user can upload a supported document
- [x] the backend stores the file, extracted text, and version metadata successfully

## Part 4 - Chunking and Ingestion Pipeline
Convert parsed text into structured retrieval units.

Checklist:
- split normalized text into chunks
- attach chunk metadata plus parser/chunking version details
- persist chunks in the database against the `document_version`
- keep chunking simple and deterministic
- make ingestion traceable for debugging

Definition of done:
- one uploaded document becomes chunk records
- chunk metadata is version-aware and available for later retrieval and citation use

## Part 5 - Embeddings and Retrieval
Add the first working retrieval layer for grounded answers.

Checklist:
- generate embeddings for chunks
- store embeddings in FAISS for one active local `index_version`
- add retrieval logic for top matching chunks
- track which `index_version` served retrieval results
- add a retrieval-focused endpoint or internal service boundary
- verify the retrieval path with sample policy documents

Definition of done:
- a test query returns relevant chunks from the active index version
- retrieval is stable enough for a basic demo

## Part 6 - Answer Generation and Citations
Connect retrieval results to the model and return grounded responses.

Checklist:
- add `POST /api/v1/chat/query`
- assemble prompt context from retrieved chunks
- generate answer with one active model provider
- return citation payloads with source snippets
- add basic run persistence

Definition of done:
- a user can ask a question and receive a grounded answer
- the response includes supporting citations/snippets

## Part 7 - UI Polish, User Context, and Demo Readiness
Finish the MVP so it is presentable and easy to run locally.

Checklist:
- render citations in the answer UI
- add a source drawer or side panel
- add current-session conversation history
- add mocked or minimal auth/user context
- improve readiness checks
- add sample seed documents
- write setup and demo instructions in the README

Definition of done:
- a new user can run the project locally without manual patchwork
- the UI clearly shows answers and supporting sources
- the project is ready for a realistic end-to-end demo

## Suggested Milestone Grouping
If you want fewer checkpoints, group the parts like this:

- Milestone A: Parts 1 and 2
- Milestone B: Parts 3 and 4
- Milestone C: Part 5
- Milestone D: Part 6
- Milestone E: Part 7

## Exit Criteria for Phase 1
Phase 1 is complete when all of the following are true:

- a user can upload one or more policy or process documents
- the system can answer grounded questions about those documents
- the UI shows citations or source snippets used in the answer
- the app runs locally through Docker with minimal setup friction
- the architecture is clean enough to extend in later phases

## Out of Scope for This Slice
Do not expand Phase 1 with these unless the MVP is already working:

- advanced auth and RBAC
- multi-workspace support
- multiple model providers
- production cloud deployment
- complex evaluation pipelines
- async workers unless they become necessary
- extensive observability beyond basic health/readiness
