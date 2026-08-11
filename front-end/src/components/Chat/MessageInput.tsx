import { useState } from 'react'
import type { FormEvent } from 'react'
import styles from './MessageInput.module.css'

interface MessageInputProps {
  onSend: (text: string) => void
  disabled: boolean
  placeholder?: string
}

function MessageInput({ onSend, disabled, placeholder }: MessageInputProps) {
  const [value, setValue] = useState('')

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    const trimmed = value.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setValue('')
  }

  return (
    <form className={styles.form} onSubmit={handleSubmit}>
      <input
        className={styles.input}
        value={value}
        onChange={(event) => setValue(event.target.value)}
        disabled={disabled}
        placeholder={placeholder ?? 'Digite sua mensagem...'}
      />
      <button className={styles.button} type="submit" disabled={disabled || !value.trim()}>
        Enviar
      </button>
    </form>
  )
}

export default MessageInput
