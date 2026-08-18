export default function AnalyticsPanel({ topLinksData, clicksOverTimeData }) {
  const maxCount = Math.max(1, ...clicksOverTimeData.map((p) => p.count))

  return (
    <div className="analytics-panel">
      <div>
        <h3>Top links</h3>
        {topLinksData.length === 0 ? (
          <p>No clicks recorded yet.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Short link</th>
                <th>Clicks</th>
              </tr>
            </thead>
            <tbody>
              {topLinksData.map((row) => (
                <tr key={row.short_code}>
                  <td>/{row.short_code}</td>
                  <td>{row.click_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div>
        <h3>Clicks over time (last 7 days)</h3>
        {clicksOverTimeData.length === 0 ? (
          <p>No clicks recorded yet.</p>
        ) : (
          <div className="bar-chart">
            {clicksOverTimeData.map((point) => (
              <div className="bar-column" key={point.date}>
                <div
                  className="bar"
                  style={{ height: `${(point.count / maxCount) * 100}%` }}
                  title={`${point.date}: ${point.count}`}
                />
                <span className="bar-label">{point.date.slice(5)}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
