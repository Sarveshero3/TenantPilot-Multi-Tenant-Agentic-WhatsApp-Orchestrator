import { StatusBadge } from './StatusBadge'
import { TypingIndicator } from './TypingIndicator'
import type { ChatSession, MessageLog, Tenant } from '../types'
import './SessionList.css'

interface SessionListProps {
  loading: boolean
  previews: Record<string, MessageLog | undefined>
  selectedSessionId: string
  sessions: ChatSession[]
  tenant?: Tenant
  onSelectSession: (sessionId: string) => void
}

function relativeTime(value?: string): string {
  if (!value) return 'No activity'
  const then = new Date(value).getTime()
  const diffSeconds = Math.max(1, Math.floor((Date.now() - then) / 1000))
  if (diffSeconds < 60) return 'Just now'
  const diffMinutes = Math.floor(diffSeconds / 60)
  if (diffMinutes < 60) return `${diffMinutes} min ago`
  const diffHours = Math.floor(diffMinutes / 60)
  if (diffHours < 24) return `${diffHours} hr ago`
  const diffDays = Math.floor(diffHours / 24)
  return `${diffDays} day${diffDays === 1 ? '' : 's'} ago`
}

function previewText(message?: MessageLog): string {
  if (!message) return 'No messages yet'
  if (message.message_type === 'image') return 'Image attachment'
  if (message.message_type === 'document') return message.media_filename ?? 'Document attachment'
  return message.text_content || 'Text message'
}

export function SessionList({
  loading,
  previews,
  selectedSessionId,
  sessions,
  tenant,
  onSelectSession,
}: SessionListProps) {
  return (
    <section className="panel session-panel">
      <div className="panel-header">
        <p className="panel-eyebrow">Conversations</p>
        <h2 className="panel-title">{tenant ? tenant.name : 'Select a tenant'}</h2>
        <p className="panel-subtitle">Live sessions refresh every 3 seconds.</p>
      </div>

      <div className="session-list scroll-region">
        {loading && (
          <div className="skeleton-list" aria-label="Loading sessions">
            <div className="skeleton-card" />
            <div className="skeleton-card" />
            <div className="skeleton-card" />
          </div>
        )}

        {!loading && !tenant && (
          <div className="empty-state">
            <strong>Select a tenant</strong>
            <span>Choose a workspace to view active WhatsApp conversations.</span>
          </div>
        )}

        {!loading && tenant && sessions.length === 0 && (
          <div className="empty-state">
            <strong>No sessions yet</strong>
            <span>Inbound WhatsApp activity will appear here once the webhook receives messages.</span>
          </div>
        )}

        {!loading &&
          sessions.map((session) => {
            const preview = previews[session.id]
            return (
              <button
                className={`session-card${session.id === selectedSessionId ? ' session-card-active' : ''}${
                  session.status === 'NEEDS_HUMAN' ? ' session-card-needs-human' : ''
                }`}
                key={session.id}
                type="button"
                onClick={() => onSelectSession(session.id)}
              >
                <div className="session-topline">
                  <span className="session-phone">{session.customer_phone}</span>
                  <span className="session-time">{relativeTime(preview?.timestamp ?? session.updated_at)}</span>
                </div>
                <div className="session-middle">
                  <StatusBadge status={session.status} />
                  {session.is_typing && (
                    <span className="session-typing">
                      <TypingIndicator compact /> Typing
                    </span>
                  )}
                </div>
                <p className="session-preview">{previewText(preview)}</p>
              </button>
            )
          })}
      </div>
    </section>
  )
}
