import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { api, API_BASE_URL } from './api/client'
import './App.css'
import { MessageThread } from './components/MessageThread'
import { SessionList } from './components/SessionList'
import { TenantSidebar } from './components/TenantSidebar'
import type { ChatSession, MessageLog, Tenant } from './types'

function latestMessage(messages: MessageLog[]): MessageLog | undefined {
  return messages[messages.length - 1]
}

function getErrorMessage(error: unknown): string {
  if (error instanceof Error) return error.message
  return 'Something went wrong'
}

export default function App() {
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null)
  const [tenants, setTenants] = useState<Tenant[]>([])
  const [selectedTenantId, setSelectedTenantId] = useState<string>('')
  const [sessions, setSessions] = useState<ChatSession[]>([])
  const [selectedSessionId, setSelectedSessionId] = useState<string>('')
  const [messages, setMessages] = useState<MessageLog[]>([])
  const [previews, setPreviews] = useState<Record<string, MessageLog | undefined>>({})
  const [loadingTenants, setLoadingTenants] = useState(true)
  const [loadingSessions, setLoadingSessions] = useState(false)
  const [loadingMessages, setLoadingMessages] = useState(false)
  const [toast, setToast] = useState<string>('')
  const [newMessageFlash, setNewMessageFlash] = useState(false)
  const previousMessageCount = useRef(0)

  const selectedTenant = useMemo(
    () => tenants.find((tenant) => tenant.tenant_id === selectedTenantId),
    [selectedTenantId, tenants],
  )

  const selectedSession = useMemo(
    () => sessions.find((session) => session.id === selectedSessionId),
    [selectedSessionId, sessions],
  )

  const showError = useCallback((message: string) => {
    setToast(message)
    window.setTimeout(() => setToast(''), 4200)
  }, [])

  useEffect(() => {
    let cancelled = false

    async function bootstrap() {
      setLoadingTenants(true)
      try {
        await api.health()
        if (!cancelled) setBackendOnline(true)
      } catch {
        if (!cancelled) setBackendOnline(false)
      }

      try {
        const tenantList = await api.listTenants()
        if (cancelled) return
        setTenants(tenantList)
        setSelectedTenantId((current) => current || tenantList[0]?.tenant_id || '')
      } catch (error) {
        if (!cancelled) {
          setBackendOnline(false)
          showError(`Backend unavailable at ${API_BASE_URL}: ${getErrorMessage(error)}`)
        }
      } finally {
        if (!cancelled) setLoadingTenants(false)
      }
    }

    bootstrap()
    return () => {
      cancelled = true
    }
  }, [showError])

  const loadSessions = useCallback(
    async (tenantId: string, options: { quiet?: boolean } = {}) => {
      if (!tenantId) return
      if (!options.quiet) setLoadingSessions(true)
      try {
        const sessionList = await api.listSessions(tenantId)
        setSessions(sessionList)
        setBackendOnline(true)
        setSelectedSessionId((current) => {
          if (current && sessionList.some((session) => session.id === current)) return current
          return sessionList[0]?.id || ''
        })

        const previewEntries = await Promise.all(
          sessionList.map(async (session) => {
            try {
              const sessionMessages = await api.getMessages(session.id)
              return [session.id, latestMessage(sessionMessages)] as const
            } catch {
              return [session.id, undefined] as const
            }
          }),
        )
        setPreviews(Object.fromEntries(previewEntries))
      } catch (error) {
        setBackendOnline(false)
        showError(`Could not load sessions: ${getErrorMessage(error)}`)
      } finally {
        if (!options.quiet) setLoadingSessions(false)
      }
    },
    [showError],
  )

  useEffect(() => {
    setSessions([])
    setMessages([])
    setPreviews({})
    setSelectedSessionId('')
    if (!selectedTenantId) return

    loadSessions(selectedTenantId)
    const interval = window.setInterval(() => loadSessions(selectedTenantId, { quiet: true }), 3000)
    return () => window.clearInterval(interval)
  }, [loadSessions, selectedTenantId])

  const loadMessages = useCallback(
    async (sessionId: string, options: { quiet?: boolean } = {}) => {
      if (!sessionId) return
      if (!options.quiet) setLoadingMessages(true)
      try {
        const nextMessages = await api.getMessages(sessionId)
        setMessages((current) => {
          if (options.quiet && current.length > 0 && nextMessages.length > current.length) {
            setNewMessageFlash(true)
            window.setTimeout(() => setNewMessageFlash(false), 2400)
          }
          previousMessageCount.current = nextMessages.length
          return nextMessages
        })
        setPreviews((current) => ({ ...current, [sessionId]: latestMessage(nextMessages) }))
        setBackendOnline(true)
      } catch (error) {
        setBackendOnline(false)
        showError(`Could not load messages: ${getErrorMessage(error)}`)
      } finally {
        if (!options.quiet) setLoadingMessages(false)
      }
    },
    [showError],
  )

  useEffect(() => {
    setMessages([])
    previousMessageCount.current = 0
    if (!selectedSessionId) return

    loadMessages(selectedSessionId)
    const interval = window.setInterval(() => loadMessages(selectedSessionId, { quiet: true }), 2000)
    return () => window.clearInterval(interval)
  }, [loadMessages, selectedSessionId])

  const handleBroadcastSent = useCallback(async () => {
    if (selectedTenantId) {
      await loadSessions(selectedTenantId, { quiet: true })
    }
    if (selectedSessionId) {
      await loadMessages(selectedSessionId, { quiet: true })
    }
  }, [loadMessages, loadSessions, selectedSessionId, selectedTenantId])

  return (
    <main className="app-shell">
      <div className="ambient ambient-one" />
      <div className="ambient ambient-two" />

      <section className="dashboard-frame" aria-label="TenantPilot dashboard">
        <TenantSidebar
          backendOnline={backendOnline}
          loading={loadingTenants}
          selectedTenantId={selectedTenantId}
          tenants={tenants}
          onSelectTenant={setSelectedTenantId}
        />

        <SessionList
          loading={loadingSessions}
          previews={previews}
          selectedSessionId={selectedSessionId}
          sessions={sessions}
          tenant={selectedTenant}
          onSelectSession={setSelectedSessionId}
        />

        <MessageThread
          loading={loadingMessages}
          messages={messages}
          newMessageFlash={newMessageFlash}
          session={selectedSession}
          tenant={selectedTenant}
          onBroadcastSent={handleBroadcastSent}
          onError={showError}
        />
      </section>

      {toast && (
        <div className="toast" role="status" aria-live="polite">
          <span>⚠</span>
          {toast}
        </div>
      )}
    </main>
  )
}
