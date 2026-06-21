export type SessionStatus =
  | 'WAITING_FOR_BOT'
  | 'AGENT_RESPONDING'
  | 'RESOLVED'
  | 'NEEDS_HUMAN'

export type MessageDirection = 'inbound' | 'outbound'
export type MessageType = 'text' | 'image' | 'document'
export type Sender = 'customer' | 'bot' | 'operator' | 'system'

export interface Tenant {
  tenant_id: string
  name: string
  whatsapp_phone_number_id: string
  system_prompt: string
  media_keys: string[]
  created_at: string
}

export interface ChatSession {
  id: string
  tenant_id: string
  customer_phone: string
  status: SessionStatus
  is_typing: boolean
  context_vars: Record<string, unknown>
  created_at: string
  updated_at: string
}

export interface MessageLog {
  id: string
  session_id: string
  tenant_id: string
  customer_phone: string
  direction: MessageDirection
  sender: Sender
  message_type: MessageType
  text_content: string | null
  media_url: string | null
  media_filename: string | null
  whatsapp_message_id: string | null
  timestamp: string
}

export interface BroadcastRequest {
  tenant_id: string
  customer_phone: string
  text: string
}

export interface BroadcastResponse {
  status: string
  message_id: string
}

export interface HealthResponse {
  status: string
  env: string
}
