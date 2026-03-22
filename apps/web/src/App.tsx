import { useEffect, useState } from 'react'
import './App.css'

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

type ApiStatus = {
  api: string
  database: string
  service: string
}

const starterPrompts = [
  'How do I onboard a new employee laptop?',
  'What is the PTO carryover policy?',
  'Summarize the expense reimbursement process.',
]

function App() {
  const [apiStatus, setApiStatus] = useState<ApiStatus | null>(null)
  const [statusMessage, setStatusMessage] = useState('Checking API status...')

  useEffect(() => {
    const checkApiStatus = async () => {
      try {
        const response = await fetch(`${apiBaseUrl}/api/v1/system/status`)

        if (!response.ok) {
          throw new Error(`Status request failed with ${response.status}`)
        }

        const payload = (await response.json()) as ApiStatus
        setApiStatus(payload)
        setStatusMessage('API connected')
      } catch {
        setStatusMessage('API unavailable')
      }
    }

    void checkApiStatus()
  }, [])

  return (
    <main className="app-shell">
      <section className="hero-panel">
        <div className="hero-copy">
          <p className="eyebrow">Phase 1 foundation</p>
          <h1>Workforce Copilot</h1>
          <p className="hero-text">
            A focused internal assistant for HR and IT questions, grounded in
            company documents and built to grow into the full platform.
          </p>
        </div>

        <div className="status-card">
          <div className="status-header">
            <span className="status-dot" aria-hidden="true" />
            <span>{statusMessage}</span>
          </div>
          <dl className="status-grid">
            <div>
              <dt>Service</dt>
              <dd>{apiStatus?.service ?? 'Waiting for API'}</dd>
            </div>
            <div>
              <dt>API</dt>
              <dd>{apiStatus?.api ?? 'Offline'}</dd>
            </div>
            <div>
              <dt>Database</dt>
              <dd>{apiStatus?.database ?? 'Unknown'}</dd>
            </div>
            <div>
              <dt>Endpoint</dt>
              <dd>{apiBaseUrl}</dd>
            </div>
          </dl>
        </div>
      </section>

      <section className="workspace">
        <div className="panel chat-panel">
          <div className="panel-header">
            <div>
              <p className="panel-label">Workspace</p>
              <h2>IT + HR assistant</h2>
            </div>
            <span className="session-badge">Current session</span>
          </div>

          <div className="message-list">
            <article className="message assistant">
              <p className="message-role">Assistant</p>
              <p>
                Upload employee policies and process documents, then ask a
                grounded question. Citations and source details will appear
                here in later Phase 1 steps.
              </p>
            </article>
            <article className="message user">
              <p className="message-role">Example</p>
              <p>What steps should I follow to provision a new laptop?</p>
            </article>
          </div>

          <form className="composer">
            <label className="composer-label" htmlFor="question">
              Ask a workplace question
            </label>
            <textarea
              id="question"
              name="question"
              placeholder="Ask about onboarding, access requests, HR policies, or IT workflows..."
              rows={4}
              disabled
            />
            <div className="composer-actions">
              <button type="button" disabled>
                Ask copilot
              </button>
              <p>Chat submission arrives in Part 6.</p>
            </div>
          </form>
        </div>

        <aside className="panel side-panel">
          <section>
            <p className="panel-label">Starter prompts</p>
            <ul className="prompt-list">
              {starterPrompts.map((prompt) => (
                <li key={prompt}>{prompt}</li>
              ))}
            </ul>
          </section>

          <section>
            <p className="panel-label">Upcoming in Phase 1</p>
            <ul className="checklist">
              <li>Document upload and parsing</li>
              <li>Chunking and metadata persistence</li>
              <li>Embeddings and retrieval</li>
              <li>Answer generation with citations</li>
            </ul>
          </section>
        </aside>
      </section>
    </main>
  )
}

export default App
