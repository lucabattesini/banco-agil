import styles from './ChatPage.module.css'
import Chat from '../components/Chat/Chat'

function ChatPage() {
  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div className={styles.logo}>🏦</div>
        <div className={styles.headerText}>
          <h1 className={styles.title}>Banco Ágil</h1>
          <p className={styles.subtitle}>Atendimento digital</p>
        </div>
      </header>
      <div className={styles.chatWrapper}>
        <Chat />
      </div>
    </div>
  )
}

export default ChatPage
