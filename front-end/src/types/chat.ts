export interface ChatRequest {
  session_id: string
  message: string
}

export interface ChatResponse {
  reply: string
  end: boolean
}

export type ChatRole = 'user' | 'assistant'

export interface ChatMessage {
  id: string
  role: ChatRole
  content: string
  isError?: boolean
}
