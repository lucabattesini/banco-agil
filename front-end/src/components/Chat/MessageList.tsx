import { useEffect, useRef } from 'react'
import styles from './MessageList.module.css'
import MessageBubble from './MessageBubble'
import TypingIndicator from './TypingIndicator'
import StarterCards from './StarterCards'
import EndOfConversationCard from './EndOfConversationCard'
import type { ChatMessage } from '../../types/chat'

interface MessageListProps {
  messages: ChatMessage[]
  isTyping: boolean
  onSuggestionSelect: (text: string) => void
  conversationEnded: boolean
  onNewConversation: () => void
}

function MessageList({
  messages,
  isTyping,
  onSuggestionSelect,
  conversationEnded,
  onNewConversation,
}: MessageListProps) {
  const endRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages.length, isTyping, conversationEnded])

  if (messages.length === 0 && !isTyping) {
    return (
      <div className={styles.list}>
        <div className={styles.emptyState}>
          <div className={styles.empty}>👋 Olá! Envie uma mensagem para começar o atendimento.</div>
          <StarterCards onSelect={onSuggestionSelect} />
        </div>
      </div>
    )
  }

  return (
    <div className={styles.list}>
      {messages.map((message) => (
        <MessageBubble key={message.id} message={message} />
      ))}
      {isTyping && <TypingIndicator />}
      {conversationEnded && <EndOfConversationCard onNewConversation={onNewConversation} />}
      <div ref={endRef} />
    </div>
  )
}

export default MessageList
