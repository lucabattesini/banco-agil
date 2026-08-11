import { useEffect, useRef } from 'react'
import styles from './MessageList.module.css'
import MessageBubble from './MessageBubble'
import TypingIndicator from './TypingIndicator'
import type { ChatMessage } from '../../types/chat'

interface MessageListProps {
  messages: ChatMessage[]
  isTyping: boolean
}

function MessageList({ messages, isTyping }: MessageListProps) {
  const endRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages.length, isTyping])

  if (messages.length === 0 && !isTyping) {
    return (
      <div className={styles.list}>
        <div className={styles.empty}>Envie uma mensagem para começar o atendimento.</div>
      </div>
    )
  }

  return (
    <div className={styles.list}>
      {messages.map((message) => (
        <MessageBubble key={message.id} message={message} />
      ))}
      {isTyping && <TypingIndicator />}
      <div ref={endRef} />
    </div>
  )
}

export default MessageList
