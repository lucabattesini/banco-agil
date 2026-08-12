import styles from './MessageBubble.module.css'
import Avatar from './Avatar'
import type { ChatMessage } from '../../types/chat'

interface MessageBubbleProps {
  message: ChatMessage
}

function renderFormattedContent(content: string) {
  return content.split(/(\*\*[^*]+\*\*)/g).map((part, index) =>
    part.startsWith('**') && part.endsWith('**') ? (
      <strong key={index}>{part.slice(2, -2)}</strong>
    ) : (
      part
    ),
  )
}

function MessageBubble({ message }: MessageBubbleProps) {
  const bubbleClass = [styles.bubble, styles[message.role], message.isError ? styles.error : '']
    .filter(Boolean)
    .join(' ')

  return (
    <div className={styles.row} data-role={message.role}>
      {message.role === 'assistant' && <Avatar />}
      <div className={bubbleClass}>{renderFormattedContent(message.content)}</div>
    </div>
  )
}

export default MessageBubble
