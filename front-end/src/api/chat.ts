import { apiFetch } from './client'
import type { ChatRequest, ChatResponse } from '../types/chat'

export function sendChatMessage(sessionId: string, message: string): Promise<ChatResponse> {
  const body: ChatRequest = { session_id: sessionId, message }

  return apiFetch<ChatResponse>('/chat/', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}
