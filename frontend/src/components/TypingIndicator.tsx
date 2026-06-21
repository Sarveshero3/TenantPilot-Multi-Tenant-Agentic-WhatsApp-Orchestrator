import './TypingIndicator.css'

interface TypingIndicatorProps {
  compact?: boolean
}

export function TypingIndicator({ compact = false }: TypingIndicatorProps) {
  return (
    <span className={`typing-indicator${compact ? ' typing-indicator-compact' : ''}`} aria-label="Typing">
      <span />
      <span />
      <span />
    </span>
  )
}
