import { useState } from 'react'
import { createLink } from '../api'

export default function CreateLinkForm({ onCreated }) {
  const [longUrl, setLongUrl] = useState('')
  const [shortCode, setShortCode] = useState('')
  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await createLink({
        long_url: longUrl,
        short_code: shortCode || undefined,
      })
      setLongUrl('')
      setShortCode('')
      onCreated()
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="create-link-form">
      <input
        type="url"
        placeholder="https://example.com/very/long/path"
        value={longUrl}
        onChange={(e) => setLongUrl(e.target.value)}
        required
      />
      <input
        type="text"
        placeholder="custom code (optional)"
        value={shortCode}
        onChange={(e) => setShortCode(e.target.value)}
        minLength={3}
        maxLength={16}
      />
      <button type="submit" disabled={submitting}>
        {submitting ? 'Creating...' : 'Shorten'}
      </button>
      {error && <p className="error">{error}</p>}
    </form>
  )
}
