import { useRef, useState } from 'react'
import styles from './Chat.module.css'
import MessageList from './MessageList'
import MessageInput from './MessageInput'
import { sendChatMessage } from '../../api/chat'
import type { ChatMessage } from '../../types/chat'

const TYPING_INDICATOR_DELAY_MS = 1000

function Chat() {
  const [sessionId] = useState(() => crypto.randomUUID())
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [showTypingIndicator, setShowTypingIndicator] = useState(false)
  const [conversationEnded, setConversationEnded] = useState(false)
  const typingTimeoutRef = useRef<number | undefined>(undefined)

  async function handleSend(text: string) {
    const userMessage: ChatMessage = { id: crypto.randomUUID(), role: 'user', content: text }
    setMessages((prev) => [...prev, userMessage])
    setIsLoading(true)
    typingTimeoutRef.current = window.setTimeout(() => {
      setShowTypingIndicator(true)
    }, TYPING_INDICATOR_DELAY_MS)

    try {
      const response = await sendChatMessage(sessionId, text)
      const assistantMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: response.reply,
      }
      setMessages((prev) => [...prev, assistantMessage])
      if (response.end) {
        setConversationEnded(true)
      }
    } catch {
      const errorMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: 'Não foi possível conectar ao servidor. Tente novamente.',
        isError: true,
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      window.clearTimeout(typingTimeoutRef.current)
      setShowTypingIndicator(false)
      setIsLoading(false)
    }
  }

  return (
    <div className={styles.chat}>
      <MessageList messages={messages} isTyping={showTypingIndicator} />
      <MessageInput
        onSend={handleSend}
        disabled={isLoading || conversationEnded}
        placeholder={conversationEnded ? 'Atendimento encerrado.' : undefined}
      />
    </div>
  )
}

export default Chat
