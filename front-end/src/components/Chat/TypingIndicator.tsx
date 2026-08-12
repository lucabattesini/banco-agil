import styles from './TypingIndicator.module.css'
import Avatar from './Avatar'

function TypingIndicator() {
  return (
    <div className={styles.row}>
      <Avatar />
      <div className={styles.bubble}>
        <span className={styles.dot} />
        <span className={styles.dot} />
        <span className={styles.dot} />
      </div>
    </div>
  )
}

export default TypingIndicator
