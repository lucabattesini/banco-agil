import styles from './StarterCards.module.css'

interface StarterCardsProps {
  onSelect: (text: string) => void
}

const SUGGESTIONS = [
  { icon: '💳', label: 'Consultar meu limite', message: 'Quero consultar meu limite de crédito' },
  { icon: '📈', label: 'Aumentar limite', message: 'Quero solicitar um aumento no meu limite' },
  { icon: '💱', label: 'Cotação de moeda', message: 'Qual a cotação do dólar hoje?' },
  { icon: '🙋', label: 'Falar com atendente', message: 'Olá, preciso de ajuda' },
]

function StarterCards({ onSelect }: StarterCardsProps) {
  return (
    <div className={styles.grid}>
      {SUGGESTIONS.map((suggestion) => (
        <button
          key={suggestion.label}
          type="button"
          className={styles.card}
          onClick={() => onSelect(suggestion.message)}
        >
          <span className={styles.icon}>{suggestion.icon}</span>
          <span className={styles.label}>{suggestion.label}</span>
        </button>
      ))}
    </div>
  )
}

export default StarterCards
