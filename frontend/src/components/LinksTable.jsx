import { API_BASE_URL, deleteLink } from '../api'

export default function LinksTable({ links, onChanged }) {
  async function handleDelete(shortCode) {
    await deleteLink(shortCode)
    onChanged()
  }

  if (links.length === 0) {
    return <p>No links yet — create one above.</p>
  }

  return (
    <table className="links-table">
      <thead>
        <tr>
          <th>Short link</th>
          <th>Destination</th>
          <th>Created</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        {links.map((link) => (
          <tr key={link.id}>
            <td>
              <a href={`${API_BASE_URL}/${link.short_code}`} target="_blank" rel="noreferrer">
                /{link.short_code}
              </a>
            </td>
            <td className="truncate">{link.long_url}</td>
            <td>{new Date(link.created_at).toLocaleString()}</td>
            <td>
              <button onClick={() => handleDelete(link.short_code)}>Delete</button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
