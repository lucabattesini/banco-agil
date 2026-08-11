import styles from './ChatPage.module.css'
import Chat from '../components/Chat/Chat'

function ChatPage() {
  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <h1 className={styles.title}>Banco Ágil</h1>
        <p className={styles.subtitle}>Atendimento digital</p>
      </header>
      <div className={styles.chatWrapper}>
        <Chat />
      </div>
    </div>
  )
}

export default ChatPage
