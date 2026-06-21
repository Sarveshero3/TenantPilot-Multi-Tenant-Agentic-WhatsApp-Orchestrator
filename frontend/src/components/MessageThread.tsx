import { useEffect, useRef } from 'react'
import { BroadcastInput } from './BroadcastInput'
import { StatusBadge } from './StatusBadge'
import { TypingIndicator } from './TypingIndicator'
import type { ChatSession, MessageLog, Tenant } from '../types'
import './MessageThread.css'

interface MessageThreadProps {
  loading: boolean
  messages: MessageLog[]
  newMessageFlash: boolean
  session?: ChatSession
  tenant?: Tenant
  onBroadcastSent: () => Promise<void> | void
  onError: (message: string) => void
}

function formatTimestamp(value: string): string {
  return new Intl.DateTimeFormat(undefined, {
    hour: 'numeric',
    minute: '2-digit',
    month: 'short',
    day: 'numeric',
  }).format(new Date(value))
}

function messageText(message: MessageLog): string {
  if (message.text_content) return message.text_content
  if (message.message_type === 'image') return 'Image attachment'
  if (message.message_type === 'document') return message.media_filename ?? 'Document attachment'
  return 'Message'
}

function renderMessageBody(message: MessageLog) {
  if (message.message_type === 'image' && message.media_url) {
    return (
      <figure className="message-media">
        <img alt={message.media_filename ?? 'WhatsApp image'} src={message.media_url} />
        {message.text_content && <figcaption>{message.text_content}</figcaption>}
      </figure>
    )
  }

  if (message.message_type === 'document' && message.media_url) {
    return (
      <a className="document-link" href={message.media_url} rel="noreferrer" target="_blank">
        <span className="document-icon">PDF</span>
        <span>
          <strong>{message.media_filename ?? 'Download document'}</strong>
          <small>Open public document URL</small>
        </span>
      </a>
    )
  }

  return <p>{messageText(message)}</p>
}

export function MessageThread({
  loading,
  messages,
  newMessageFlash,
  session,
  tenant,
  onBroadcastSent,
  onError,
}: MessageThreadProps) {
  const bottomRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages.length, session?.id])

  return (
    <section className="panel thread-panel">
      <div className="thread-header panel-header">
        <div>
          <p className="panel-eyebrow">Message thread</p>
          <h2 className="panel-title">{session ? session.customer_phone : 'Select a session'}</h2>
          <p className="panel-subtitle">{tenant ? tenant.name : 'Pick a tenant and conversation to inspect history.'}</p>
        </div>
        {session && (
          <div className="thread-header-actions">
            <StatusBadge status={session.status} />
            {session.is_typing && (
              <span className="thread-typing pill">
                <TypingIndicator compact /> Typing
              </span>
            )}
          </div>
        )}
      </div>

      {newMessageFlash && <div className="new-message-banner">New messages arrived</div>}

      <div className="thread-scroll scroll-region">
        {loading && (
          <div className="thread-skeleton" aria-label="Loading messages">
            <div className="skeleton-line skeleton-left" />
            <div className="skeleton-line skeleton-right" />
            <div className="skeleton-line skeleton-left short" />
          </div>
        )}

        {!loading && !session && (
          <div className="empty-state">
            <strong>Select a session</strong>
            <span>The full WhatsApp message history will appear here.</span>
          </div>
        )}

        {!loading && session && messages.length === 0 && (
          <div className="empty-state">
            <strong>No messages yet</strong>
            <span>This session exists, but no message logs have been recorded.</span>
          </div>
        )}

        {!loading &&
          messages.map((message) => {
            const outbound = message.direction === 'outbound'
            return (
              <article className={`message-row ${outbound ? 'message-row-outbound' : 'message-row-inbound'}`} key={message.id}>
                <div className={`message-bubble ${outbound ? 'bubble-outbound' : 'bubble-inbound'}`}>
                  <span className="message-sender">{message.sender}</span>
                  {renderMessageBody(message)}
                  <time dateTime={message.timestamp}>{formatTimestamp(message.timestamp)}</time>
                </div>
              </article>
            )
          })}
        <div ref={bottomRef} />
      </div>

      <BroadcastInput
        customerPhone={session?.customer_phone}
        disabled={!session || !tenant}
        tenantId={tenant?.tenant_id}
        onError={onError}
        onSent={onBroadcastSent}
      />
    </section>
  )
}
