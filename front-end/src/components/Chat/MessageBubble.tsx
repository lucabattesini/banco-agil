import styles from './MessageBubble.module.css'
import type { ChatMessage } from '../../types/chat'

interface MessageBubbleProps {
  message: ChatMessage
}

function MessageBubble({ message }: MessageBubbleProps) {
  const bubbleClass = [styles.bubble, styles[message.role], message.isError ? styles.error : '']
    .filter(Boolean)
    .join(' ')

  return (
    <div className={styles.row} data-role={message.role}>
      <div className={bubbleClass}>{message.content}</div>
    </div>
  )
}

export default MessageBubble
