import type { SessionStatus } from '../types'
import './StatusBadge.css'

interface StatusBadgeProps {
  status: SessionStatus
}

const labels: Record<SessionStatus, string> = {
  WAITING_FOR_BOT: 'Waiting',
  AGENT_RESPONDING: 'Responding',
  RESOLVED: 'Resolved',
  NEEDS_HUMAN: 'Human needed',
}

export function StatusBadge({ status }: StatusBadgeProps) {
  return <span className={`status-badge status-${status.toLowerCase()}`}>{labels[status]}</span>
}
