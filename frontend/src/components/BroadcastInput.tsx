import { FormEvent, useState } from 'react'
import { api } from '../api/client'
import './BroadcastInput.css'

interface BroadcastInputProps {
  customerPhone?: string
  disabled?: boolean
  tenantId?: string
  onError: (message: string) => void
  onSent: () => Promise<void> | void
}

function getErrorMessage(error: unknown): string {
  if (error instanceof Error) return error.message
  return 'Unable to send message'
}

export function BroadcastInput({ customerPhone, disabled, tenantId, onError, onSent }: BroadcastInputProps) {
  const [text, setText] = useState('')
  const [sending, setSending] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const trimmed = text.trim()
    if (!tenantId || !customerPhone || !trimmed) return

    setSending(true)
    try {
      await api.broadcast({ tenant_id: tenantId, customer_phone: customerPhone, text: trimmed })
      setText('')
      await onSent()
    } catch (error) {
      onError(`Broadcast failed: ${getErrorMessage(error)}`)
    } finally {
      setSending(false)
    }
  }

  return (
    <form className="broadcast-input" onSubmit={handleSubmit}>
      <textarea
        aria-label="Reply text"
        disabled={disabled || sending || !tenantId || !customerPhone}
        placeholder={customerPhone ? 'Send a manual WhatsApp reply…' : 'Select a session to reply'}
        rows={2}
        value={text}
        onChange={(event) => setText(event.target.value)}
      />
      <button disabled={disabled || sending || !tenantId || !customerPhone || text.trim().length === 0} type="submit">
        {sending ? 'Sending…' : 'Send'}
      </button>
    </form>
  )
}
