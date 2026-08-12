import styles from './EndOfConversationCard.module.css'

interface EndOfConversationCardProps {
  onNewConversation: () => void
}

function EndOfConversationCard({ onNewConversation }: EndOfConversationCardProps) {
  return (
    <div className={styles.card}>
      <p className={styles.text}>
        👋 Parece que seu atendimento chegou ao fim. Deseja iniciar uma nova conversa?
      </p>
      <button type="button" className={styles.button} onClick={onNewConversation}>
        Iniciar nova conversa
      </button>
    </div>
  )
}

export default EndOfConversationCard
